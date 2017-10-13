"""Module docstring.

Ajax ESXi calls module

"""
__author__= "Zacharias El Banna"                     
__version__ = "17.10.4"
__status__= "Production"

########################################## ESXi Operations ##########################################
#
# Split into main and list ZEB
#

def main(aWeb):
 import sdcp.core.GenLib as GL                   
 db = GL.DB()
 db.connect()
 id = aWeb.get_value('id')
 print "<DIV CLASS=z-navbar ID=div_navbar>"
 if id:
  db.do("SELECT hostname, INET_NTOA(ip) as ipasc, domains.name AS domain FROM devices INNER JOIN domains ON domains.id = devices.a_dom_id WHERE devices.id = '{}'".format(id))
  data = db.get_row() 
  print "<A CLASS='z-warning z-op' DIV=div_esxi_op MSG='Really shut down?' URL='index.cgi?call=esxi_op&nstate=poweroff&id={}'>Shutdown</A>".format(id)
  print "<A CLASS=z-op DIV=div_content_right  URL=index.cgi?call=esxi_graph&hostname={0}&domain={1}>Stats</A>".format(data['hostname'],data['domain'])
  print "<A CLASS=z-op DIV=div_content_right  URL=index.cgi?call=esxi_logs&hostname={0}&domain={1}>Logs</A>".format(data['hostname'],data['domain'])
  print "<A CLASS=z-op HREF=https://{0}/ui     target=_blank>UI</A>".format(data['ipasc'])
  print "<A CLASS='z-op z-reload' DIV=div_main_cont URL='index.cgi?{}'></A>".format(aWeb.get_args())
  print "</DIV>"
  print "<DIV CLASS=z-content ID=div_content>"
  print "<DIV CLASS=z-content-left ID=div_content_left>"
  op(aWeb,data['ipasc'],data['hostname'])
 else:
  db.do("SELECT id, INET_NTOA(ip) AS ipasc, hostname, type FROM devices WHERE type = 'esxi' OR type = 'vcenter' ORDER BY type,hostname")
  rows = db.get_rows() 
  print "&nbsp;</DIV>"    
  print "<DIV CLASS=z-content ID=div_content>"
  print "<DIV CLASS=z-content-left ID=div_content_left>"
  print "<DIV CLASS=z-frame><DIV CLASS=z-table style='width:99%'>"
  print "<DIV CLASS=thead><DIV CLASS=th>Type</DIV><DIV CLASS=th>Hostname</DIV></DIV>"        
  print "<DIV CLASS=tbody>"
  for row in rows:
   print "<DIV CLASS=tr><DIV CLASS=td>{}</DIV><DIV CLASS=td>".format(row['type'])
   if row['type'] == 'esxi':                  
    print "<A CLASS=z-op DIV=div_main_cont URL='index.cgi?call=esxi_main&id={}'>{}</A>".format(row['id'],row['hostname'])
   else:        
    print "<A TARGET=_blank HREF='https://{}:9443/vsphere-client/'>{}</A>".format(row['ipasc'],row['hostname'])
   print "</DIV></DIV>"
  print "</DIV></DIV></DIV>"
 db.close()
 print "</DIV>" 
 print "<DIV CLASS=z-content-right ID=div_content_right></DIV>"
 print "</DIV>"        


#
# Graphing
#
def graph(aWeb):
 from sdcp.tools.munin import widget_cols
 hostname = aWeb.get_value('hostname')
 domain   = aWeb.get_value('domain')
 print "<DIV CLASS=z-frame style='overflow-x:auto;'>"
 widget_cols([ "{1}/{0}.{1}/esxi_vm_info".format(hostname,domain), "{1}/{0}.{1}/esxi_cpu_info".format(hostname,domain), "{1}/{0}.{1}/esxi_mem_info".format(hostname,domain) ])
 print "</DIV>"

#
# Logs
#
def logs(aWeb):
 hostname = aWeb.get_value('hostname')
 try:
  from subprocess import check_output
  import sdcp.PackageContainer as PC
  logs = check_output("tail -n 30 " + PC.esxi['logformat'].format(hostname) + " | tac", shell=True)
  print "<DIV CLASS='z-logs'><H1>{} operation logs</H1>{}</DIV>".format("{}".format(hostname),logs.replace('\n','<BR>'))
 except:
  pass

#
# ESXi operations
#
def op(aWeb,aIP = None, aName = None):
 from sdcp.devices.ESXi import ESXi
 ip     = aWeb.get_value('ip',aIP)
 name   = aWeb.get_value('name',aName)
 excpt  = aWeb.get_value('except','-1')
 nstate = aWeb.get_value('nstate')
 vmid   = aWeb.get_value('vmid','-1')
 sort   = aWeb.get_value('sort','name')
 aEsxi  = ESXi(ip)
 aEsxi.set_name(name)

 if nstate:
  from subprocess import check_call, check_output
  import sdcp.PackageContainer as PC
  try:
   if nstate == 'vmsvc-snapshot.create':
    from time import strftime
    with aEsxi:
     aEsxi.ssh_send("vim-cmd vmsvc/snapshot.create {} 'Portal Snapshot' '{}'".format(vmid,strftime("%Y%m%d")))
   elif nstate == 'vmsvc-snapshot.revert':
    with aEsxi:
     data = aEsxi.ssh_send("vim-cmd vmsvc/snapshot.get {} ".format(vmid))
     s_last = 0
     for line in data.splitlines():
      if "Snapshot Id" in line:
       s_id = int(line.split()[3])
       s_last = s_last if s_last > s_id else s_id
     if s_last > 0:
      aEsxi.ssh_send("vim-cmd vmsvc/snapshot.revert {} {} suppressPowerOff".format(vmid,s_last))
   elif "vmsvc-" in nstate:
    vmop = nstate.partition('-')[2]
    with aEsxi:
     aEsxi.ssh_send("vim-cmd vmsvc/{} {}".format(vmop,vmid))
   elif nstate == 'poweroff':
    with aEsxi:
     aEsxi.ssh_send("poweroff")
   elif nstate == 'vmsoff':
    excpt = "" if vmid == '-1' else vmid
    check_call("/usr/local/sbin/ups-operations shutdown {} {} {} &".format(ip,name,excpt), shell=True)
  except Exception as err:
   PC.log_msg("ESXi: nstate error [{}]".format(str(err)))

 statelist = aEsxi.get_vms(sort)
 # Formatting template (command, btn-xyz, vm-id, hover text)
 template="<A CLASS='z-btn z-small-btn z-op' TITLE='{3}' SPIN=true DIV=div_content_left URL='index.cgi?call=esxi_op&ip=" + ip + "&name=" + name + "&nstate={0}&vmid={2}&sort=" + sort + "'><IMG SRC=images/btn-{1}.png></A>"
 print "<DIV CLASS=z-frame>"
 if nstate:
  print "<DIV CLASS=title>{}<SPAN style='font-size:12px'>{}:{}</SPAN></DIV>".format(name,vmid, nstate.split('-')[1])
 else:
  print "<DIV CLASS=title>{}</DIV>".format(name)
 print "<A TITLE='Reload List' CLASS='z-btn z-small-btn z-op' DIV=div_content_left URL='index.cgi?call=esxi_op&ip={0}&name={1}'><IMG SRC='images/btn-reboot.png'></A>".format(ip,name)
 print "<DIV CLASS=z-table style='width:99%'>"
 print "<DIV CLASS=thead><DIV CLASS=th><A CLASS=z-op DIV=div_content_left URL='index.cgi?call=esxi_op&ip=" + ip + "&name=" + name + "&sort=" + ("id" if sort == "name" else "name") + "'>VM</A></DIV><DIV CLASS=th>Operations</DIV></DIV>"
 print "<DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>"
 if nstate and nstate == 'vmsoff':
  print "<B>SHUTDOWN ALL VMs!</B>"
 else:
  print "SHUTDOWN ALL VMs!"
 print "</DIV><DIV CLASS=td><CENTER>" + template.format('vmsoff','shutdown',excpt, "Shutdown all VMs") + "&nbsp;</CENTER></DIV></DIV>"
 for vm in statelist:
  print "<DIV CLASS=tr><DIV CLASS=td style='padding:0px;'>"
  print "<B>{}</B>".format(vm[1]) if vm[0] == vmid else vm[1]
  print "</DIV><DIV CLASS=td style='padding:0px;'>"
  if vm[2] == "1":
   print template.format('vmsvc-power.shutdown','shutdown', vm[0], "Soft shutdown")
   print template.format('vmsvc-power.reboot','reboot', vm[0], "Soft reboot")
   print template.format('vmsvc-power.suspend','suspend', vm[0], "Suspend")
   print template.format('vmsvc-power.off','off', vm[0], "Hard power off")
  elif vm[2] == "3":
   print template.format('vmsvc-power.on','start', vm[0], "Start")
   print template.format('vmsvc-power.off','off', vm[0], "Hard power off")
  else:
   print template.format('vmsvc-power.on','start', vm[0], "Start")
   print template.format('vmsvc-snapshot.create','snapshot', vm[0], "Snapshot")
   print template.format('vmsvc-snapshot.revert','revert', vm[0], "Snapshot revert to last")
  print "</DIV></DIV>"
 print "</DIV></DIV></DIV>"