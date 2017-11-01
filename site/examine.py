"""Module docstring.

Ajax generic SDCP calls module

"""
__author__= "Zacharias El Banna"
__version__ = "17.11.01GA"
__status__= "Production"

from sdcp import PackageContainer as PC

############################################ Examine ##############################################
#
# Examine Logs
#
def main(aWeb):
 if not aWeb.cookie.get('sdcp_id'):
  print "<SCRIPT>location.replace('index.cgi')</SCRIPT>"
  return
 upshost = PC.sdcp['upshost']
 print "<DIV CLASS='z-navbar' ID=div_navbar>"
 print "<A CLASS='z-warning z-op' DIV=div_content MSG='Clear Network Logs?' URL='sdcp.cgi?call=examine_clear'>Clear Logs</A>"
 print "<A CLASS=z-op DIV=div_content URL=sdcp.cgi?call=examine_logs>Logs</A>"
 if upshost:
  print "<A CLASS=z-op DIV=div_content URL=sdcp.cgi?call=examine_ups>UPS</A>"
 print "<A CLASS=z-op DIV=div_content URL=sdcp.cgi?call=dns_top>DNS</A>"
 print "<A CLASS=z-op DIV=div_content URL=sdcp.cgi?call=dhcp_leases>DHCP</A>"
 print "<A CLASS=z-op DIV=div_content URL=sdcp.cgi?call=examine_svc>Services Logs</A>"
 print "<A CLASS='z-reload z-op' DIV=div_main_cont URL=sdcp.cgi?call=examine_main></A>"
 print "</DIV>"
 print "<DIV CLASS=z-content ID=div_content></DIV>"

#
#
#
def clear(aWeb):
 from sdcp.core.rest import call as rest_call
 res_dns  = rest_call(PC.dns['url'],'sdcp.rest.examine_clear_logs',{ 'logs':[PC.generic['logformat']]})
 res_host = rest_call("http://127.0.0.1/rest.cgi",'sdcp.rest.examine_clear_logs',{ 'logs':[PC.generic['logformat'],PC.sdcp['netlogs']]})
 print "<DIV CLASS=z-frame>{}<BR>{}</DIV>".format(res_host,res_dns)

#
# Internal Logs
#
def logs(aWeb):
 from sdcp.core.rest import call as rest_call
 logs = rest_call('http://127.0.0.1/rest.cgi','sdcp.rest.examine_get_logs',{'count':10,'logs':[PC.generic['logformat'],PC.sdcp['netlogs']]})
 for file,res in logs.iteritems():
  print "<DIV CLASS='z-logs'><H1>{}</H1><PRE>".format(file)
  for line in res:
   print line
  print "</PRE></DIV>"

#
# UPS graphs
#
def ups(aWeb):
 from sdcp.tools.munin import widget_cols
 upshost,void,domain = PC.sdcp['upshost'].partition('.')
 print "<DIV CLASS=z-frame STYLE='width:auto;'>"
 widget_cols([ "{1}/{0}.{1}/hw_apc_power".format(upshost,domain), "{1}/{0}.{1}/hw_apc_time".format(upshost,domain), "{1}/{0}.{1}/hw_apc_temp".format(upshost,domain) ])
 print "</DIV>"

#
# Service logs
#
def svc(aWeb):
 from sdcp.core.rest import call as rest_call
 logs = rest_call("http://{}/rest.cgi".format(PC.sdcp['svcsrv']), "sdcp.rest.examine_get_logs",{'count':20,'logs':[PC.generic['logformat']]})
 for file,res in logs.iteritems():
  print "<DIV CLASS='z-logs'><H1>{}</H1><PRE>".format(file)
  for line in res:
   print line
  print "</PRE></DIV>"
