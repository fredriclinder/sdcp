"""Module docstring.

Module for graph interaction

Exports:
- Grapher

"""  
__author__ = "Zacharias El Banna"
__version__ = "17.6.1GA"
__status__ = "Production"

import sdcp.core.GenLib as GL

####################################### Grapher Class ##########################################
#
#

class Grapher(object):

 def __init__(self, aconf='/etc/munin/munin.conf', agraphplug = '/var/www/device.graph.plugins'):
  self._configfile = aconf
  self._configitems = {}
  self._graphplug = agraphplug
 
 def __str__(self):
  return "ConfigFile:{} PluginFile:{} ConfigKeys:[{}]".format(self._configfile, self._graphplug, str(self._configitems.keys()))

 def _print_graph_link(self, asource, aX = "399", aY = "224"):
  from time import time
  stop  = int(time())-300
  start = stop - 24*3600 
  print "<A target=main_cont HREF='munin-cgi/munin-cgi-html/static/dynazoom.html?"
  print "cgiurl_graph=/munin-cgi/munin-cgi-graph&plugin_name={0}&size_x=800&size_y=400&start_epoch={1}&stop_epoch={2}'>".format(asource,str(start),str(stop))
  print "<IMG width={0} height={1} ALT='munin graph:{2}' SRC='/munin-cgi/munin-cgi-graph/{2}-day.png' /></A>".format(aX, aY, asource)

 def widget_cols(self, asources):
  lwidth = 3 if len(asources) < 3 else len(asources)
  print "<DIV CLASS='z-graph' style='padding:5px; width:{}px; height:240px; float:left;'>".format(str(lwidth * 410))
  for src in asources:
   self._print_graph_link(src)
  print "</DIV>"

 def widget_rows(self, asources):
  lheight = 3 if len(asources) < 3 else len(asources)
  print "<DIV CLASS='z-graph' style='padding-top:10px; padding-left:5px; width:420px; height:{}px; float:left;'>".format(str(lheight * 230))
  for src in asources:
   self._print_graph_link(src)
  print "</DIV>"

 #
 # Config items contains entry: [ handler, updatestate ]
 #
 def load_conf(self):
  # read until find [ ... ] then read two more lines, finally add to dict
  with open(self._configfile) as conffile:
   # Clear old dict first..
   self._configitems.clear()
   entry,handler,update = None, None, None
   extra = []
  
   # Modify for arbitrary length! to store more "nice" stuff with Grapher
   #
   for linen in conffile:
    line = linen.strip()
    if entry:
     if line.startswith("address"):
      handler = line[8:]
     elif line.startswith("update"):
      update = line[7:10].strip()
      self._configitems[entry] = {'handler':handler, 'update':update}
      entry,handler,update = None, None, None
      extra = []
    elif line.startswith("[") and line.endswith("]"):
     entry = line[1:-1]

 def get_entry(self, aentry):
  if not self._configitems:
   self.load_conf()
  return self._configitems.get(aentry,None)

 def get_keys(self):
  if not self._configitems:
   self.load_conf()
  return sorted(self._configitems.keys())
 
 def update_entry(self, akey, astate):
  oldstate = "no" if astate == "yes" else "yes"
  try:
   with open(self._configfile, 'r') as conffile:
    filedata = conffile.read()
   pos = filedata.find("[" + akey + "]")
   old,new = None, None
   if pos > 0:
    old = filedata[pos:pos + 100].split("[")[1]
    new = old.replace("update " + oldstate, "update " + astate, 1)
    filedata = filedata.replace(old,new)
    with open(self._configfile, 'w') as conffile:
     conffile.write(filedata)
    data = self._configitems.get(akey,None)
    if data:
     data['update'] = astate
     self._configitems[akey] = data
  except Exception as err:
   GL.log_msg("Grapher updateEntry: Error [{}]".format(str(err)))

 def add_entry(self, akey, aupdate, ahandler = '127.0.0.1'):
  GL.log_msg("Grapher: Adding entry: {} - {} - {}".format(akey, aupdate, ahandler))
  with open(self._configfile, 'a') as conffile:
   conffile.write("\n")
   conffile.write("[" + akey + "]\n")
   conffile.write("address " + ahandler + "\n")
   conffile.write("update " + aupdate + "\n")
  self._configitems[akey] = { 'handler':ahandler, 'update':aupdate }
 
 #
 # Writes plugin info for devices found with DeviceHandler
 #
 def discover(self, ahandler = '127.0.0.1'):
  from os import chmod
  from time import time
  from threading import Lock, Thread, BoundedSemaphore
  start_time = int(time())
  try:
   flock = Lock()
   sema  = BoundedSemaphore(10)
   with open(self._graphplug, 'w') as f:
    f.write("#!/bin/bash\n")
   chmod(self._graphplug, 0o777)
   db = GL.DB()
   db.connect()
   db.do("SELECT type, hostname, domains.name AS domain, INET_NTOA(ip) as ip FROM devices INNER JOIN domains ON devices.a_dom_id = domains.id")
   rows = db.get_all_rows()
   db.close()
   for item in rows:
    sema.acquire()
    t = Thread(target = self._detect, args=[item['ip'], item, ahandler, flock, sema])
    t.start()
   for i in range(10):
    sema.acquire()       
  except Exception as err:
   GL.log_msg("Grapher: failure in processing Device entries: [{}]".format(str(err)))
  GL.log_msg("Grapher: Total time spent: {} seconds".format(int(time()) - start_time))

 ########################### Detect Plugins ###########################
 #
 # Device must answer to ping(!) for system to continue
 #
 #
 # DevHandler should have a method for getting a 'type' object
 #
 def _detect(self, aip, aentry, ahandler, alock, asema):
  if not GL.ping_os(aip):
   asema.release()
   return False

  activeinterfaces = []
  type = aentry['type']
  fqdn = aentry['hostname'] + "." + aentry['domain']
  try:
   if type in [ 'ex', 'srx', 'qfx', 'mx', 'wlc' ]:
    from sdcp.devices.Router import Junos
    if not type == 'wlc':
     jdev = Junos(aip)
     if jdev.connect():
      activeinterfaces = jdev.get_up_interfaces()
      jdev.close()
     else:
      GL.log_msg("Graph detect: impossible to connect to {}! [{} - {}]".format(fqdn,type,model))
    alock.acquire()
    with open(self._graphplug, 'a') as graphfile:
     if not self.get_entry(fqdn):
      self.add_entry(fqdn, "no", ahandler)
     graphfile.write('ln -s /usr/local/sbin/plugins/snmp__{0} /etc/munin/plugins/snmp_{1}_{0}\n'.format(type,fqdn))
     graphfile.write('ln -s /usr/share/munin/plugins/snmp__uptime /etc/munin/plugins/snmp_' + fqdn + '_uptime\n')
     graphfile.write('ln -s /usr/share/munin/plugins/snmp__users  /etc/munin/plugins/snmp_' + fqdn + '_users\n')
     for ifd in activeinterfaces:
      graphfile.write('ln -s /usr/share/munin/plugins/snmp__if_    /etc/munin/plugins/snmp_' + fqdn + '_if_'+ ifd[2] +'\n')
    alock.release()
   elif type == "esxi":
    alock.acquire()
    with open(self._graphplug, 'a') as graphfile:
     if not self.get_entry(fqdn):
      self.add_entry(fqdn, "no", ahandler)
     graphfile.write('ln -s /usr/share/munin/plugins/snmp__uptime /etc/munin/plugins/snmp_' + fqdn + '_uptime\n')              
     graphfile.write('ln -s /usr/local/sbin/plugins/snmp__esxi    /etc/munin/plugins/snmp_' + fqdn + '_esxi\n')
    alock.release()
  except Exception as err:
   GL.log_msg("Graph detect - error: [{}]".format(str(err)))
  
  asema.release()
  return True

#############################################################################