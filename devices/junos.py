"""Module docstring.

Junos Router Base Class

"""
__author__ = "Zacharias El Banna"
__version__ = "17.11.01GA"
__status__ = "Production"

from sdcp import PackageContainer as PC
from generic import GenericDevice
from netsnmp import VarList, Varbind, Session

################################ JUNOS Object #####################################
#

class Junos(GenericDevice):

 @classmethod
 def get_widgets(cls):
  return ['get_up_interfaces','get_lldp' ]

 def __init__(self,aIP,aID = None):
  GenericDevice.__init__(self,aIP,aID)
  from jnpr.junos import Device as JunosDevice
  from jnpr.junos.utils.config import Config
  self._router = JunosDevice(self._ip, user=PC.netconf['username'], password=PC.netconf['password'], normalize=True)
  self._config = Config(self._router)
  self._model = ""
  self._version = ""
  self._interfacesname = {}
 
 def __str__(self):
  return "{} Type:{} Model:{} Version:{}".format(str(self._router),  self.get_type(), self._model, self._version)

 def get_type(self):
  return 'junos'

 def __enter__(self):
  if self.connect():
   return self
  else:
   raise RuntimeError("Error connecting to host")
 
 def __exit__(self, *ctx_info):
  self.close()

 def connect(self):
  try:
   self._router.open()
   self._model = self._router.facts['model']
   self._version = self._router.facts['version']
  except Exception as err:
   self.log_msg("System Error - Unable to connect to router: " + str(err))
   return False
  return True

 def close(self):
  try:
   self._router.close()
  except Exception as err:
   self.log_msg("System Error - Unable to properly close router connection: " + str(err))

 def get_rpc(self):
  return self._router.rpc

 def get_dev(self):
  return self._router

 def get_interface_name(self, aifl):
  return self._interfacesname.get(aifl.split('.')[0],None)
 
 #
 # Netconf shit
 # 
 def ping_rpc(self,ip):
  result = self._router.rpc.ping(host=ip, count='1')
  return len(result.xpath("ping-success"))

 def get_facts(self,akey):
  return self._router.facts[akey]

 def load_interfaces_name(self):
  interfaces = self._router.rpc.get_interface_information(descriptions=True)
  for interface in interfaces:
   ifd         = interface.find("name").text
   description = interface.find("description").text
   self._interfacesname[ifd] = description

 def get_up_interfaces(self):
  interfaces = self._router.rpc.get_interface_information()
  ret = []
  for ifd in interfaces:
   entry = {'Interface':ifd[0].text, 'State':ifd[2].text, 'SNMP':ifd[4].text, 'Description':ifd[5].text }
   # Split ge-0/0/0 into ge and 0/0/0, remove extra numbers for aeX interfaces
   tp = entry['Interface'].partition('-')[0].rstrip('0123456789')
   if tp in [ 'ge', 'fe', 'xe', 'et','st0','ae' ] and entry['State'] == "up":
    ret.append(entry)
  return ret

 def get_lldp(self):
  neighbors = self._router.rpc.get_lldp_neighbors_information()
  ret = []
  for neigh in neighbors:
   # Remote system always last, remote port second to last, local is always first and pos 3 (2) determines if there is a mac or not
   fields = len(neigh)-1
   ret.append({ 'Neighbor':neigh[fields].text, 'MAC':neigh[3].text if neigh[2].text == "Mac address" else '-','Local_port':neigh[0].text,'Destination_port':neigh[fields-1].text })
  return ret

 #
 # End of NETCONF crap
 # 
 # SNMP is much smoother than Netconf for some things :-)
 #
 def quick_load(self):
  try:
   devobjs = VarList(Varbind('.1.3.6.1.2.1.1.1.0'))
   session = Session(Version = 2, DestHost = self._ip, Community = PC.snmp['read_community'], UseNumeric = 1, Timeout = 100000, Retries = 2)
   session.get(devobjs)
   datalist = devobjs[0].val.split()
   self._model = datalist[3]
   self._version = datalist[datalist.index('JUNOS') + 1].strip(',')
   if "ex" in self._model:
    self._type = "ex"
   elif "srx" in self._model:
    self._type = "srx"
   elif "qfx" in self._model:
    self._type = "qfx"
   elif "mx" in self._model:
    self._type = "mx"
  except:
   pass

 def print_conf(self,argdict):
  from sdcp import PackageContainer as PC
  print "set system host-name {}<BR>".format(argdict['name'])
  if PC.netconf['username'] == 'root':
   print "set system root-authentication encrypted-password \"{}\"<BR>".format(PC.netconf['encrypted'])
  else:
   print "set system login user {0} class super-user<BR>".format(PC.netconf['username'])
   print "set system login user {0} authentication encrypted-password \"{1}\"<BR>".format(PC.netconf['username'],PC.netconf['encrypted'])
  base  = "set groups default_system "
  print base + "system domain-name {}<BR>".format(argdict['domain'])
  print base + "system domain-search {}<BR>".format(argdict['domain'])
  print base + "system name-server {}<BR>".format(PC.netconf['dnssrv'])
  print base + "system services ssh root-login allow<BR>"
  print base + "system services netconf ssh<BR>"
  print base + "system syslog user * any emergency<BR>"
  print base + "system syslog file messages any notice<BR>"
  print base + "system syslog file messages authorization info<BR>"
  print base + "system syslog file interactive-commands interactive-commands any<BR>"
  print base + "system archival configuration transfer-on-commit<BR>"
  print base + "system archival configuration archive-sites ftp://{}/<BR>".format(PC.netconf['anonftp'])
  print base + "system commit persist-groups-inheritance<BR>"
  print base + "system ntp server {}<BR>".format(PC.netconf['ntpsrv'])
  print base + "routing-options static route 0.0.0.0/0 next-hop {}<BR>".format(argdict['gateway'])
  print base + "routing-options static route 0.0.0.0/0 no-readvertise<BR>"
  print base + "snmp community {} clients {}/{}<BR>".format(PC.snmp['read_community'],argdict['subnet'],argdict['mask'])
  print base + " protocols lldp port-id-subtype interface-name<BR>"
  print base + " protocols lldp interface all<BR>"
  print base + " class-of-service host-outbound-traffic forwarding-class network-control<BR>"
  print "set apply-groups default_system<BR>"
