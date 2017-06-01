"""Module docstring.

IPMI interworking module

- https://lime-technology.com/forum/index.php?topic=39238.0
- requires ipmitool to be installed on system and "in path"
- ipmitool -H <host> -U <username> -P <password> raw 0x3a 0x01 0x00 0x00 0x28 0x28 0x2d 0x2d 0x00 0x00

"""
__author__ = "Zacharias El Banna"                     
__version__ = "17.6.1GA"
__status__ = "Production"

import sdcp.SettingsContainer as SC
from XtraLib import get_results, str2hex
from subprocess import check_output, check_call


################################### IPMI #######################################

class IPMI(object):
 def __init__(self, ahost):
  self.hostname = ahost
  
 def print_info(self, agrep):
  readout = check_output("ipmitool -H " + self.hostname + " -U " + SC.ipmi_username + " -P " + SC.ipmi_password + " sdr | grep -E '" + agrep + "'",shell=True)
  for fanline in readout.split('\n'):
   if fanline is not "":
    fan = fanline.split()
    print fan[0] + "\t" + fan[3] + " " + fan[4]

 def set_fans(self, arear, afront):
  from io import open
  from os import devnull
  FNULL = open(devnull, 'w')
  rear  = str2hex(arear)
  front = str2hex(afront)
  ipmistring = "ipmitool -H " + self.hostname + " -U " + SC.ipmi_username + " -P " + SC.ipmi_password + " raw 0x3a 0x01 0x00 0x00 " + rear + " " + rear + " " + front + " " + front + " 0x00 0x00"
  res = check_call(ipmistring,stdout=FNULL,stderr=FNULL,shell=True)
  print get_results(res)