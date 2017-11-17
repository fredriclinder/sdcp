"""Module docstring.

HTML5 Ajax Device calls module

"""
__author__= "Zacharias El Banna"
__version__ = "17.11.01GA"
__status__= "Production"

from sdcp.core.dbase import DB

########################################## Device Operations ##########################################

def main(aWeb):
 target = aWeb['target']
 arg    = aWeb['arg']

 print "<NAV>"
 print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=device_list{0}'>Devices</A>".format('' if (not target or not arg) else "&target="+target+"&arg="+arg)
 print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=graph_list{0}'>Graphing</A>".format('' if (not target or not arg) else "&target="+target+"&arg="+arg)
 print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=bookings_list'>Bookings</A>"
 if target == 'vm':
  print "<A CLASS='z-reload z-op' DIV=main URL='sdcp.cgi?{}'></A>".format(aWeb.get_args())
 else:
  with DB() as db:
   if target == 'rack_id':
    res = db.do("SELECT racks.name, fk_pdu_1, fk_pdu_2, INET_NTOA(consoles.ip) as con_ip FROM racks LEFT JOIN consoles ON consoles.id = racks.fk_console WHERE racks.id= '{}'".format(arg))
    if res > 0:
     data = db.get_row()
     if data.get('con_ip'):
      print "<A CLASS=z-op DIV=div_content_left SPIN=true URL='sdcp.cgi?call=console_inventory&consolelist={0}'>Console</A>".format(data['con_ip'])
     if (data.get('fk_pdu_1') or data.get('fk_pdu_2')):
      res = db.do("SELECT INET_NTOA(ip) as ip, id FROM pdus WHERE (pdus.id = {0}) OR (pdus.id = {1})".format(data.get('fk_pdu_1','0'),data.get('fk_pdu_2','0')))
      rows = db.get_rows()
      pdus = ""
      for row in rows:
       pdus = pdus + "&pdulist=" + row.get('ip')
      print "<A CLASS=z-op DIV=div_content_left SPIN=true URL='sdcp.cgi?call=pdu_inventory{0}'>Pdu</A>".format(pdus)  
     print "<A CLASS=z-op DIV=div_content_right URL='sdcp.cgi?call=rack_inventory&rack={0}'>'{1}' info</A>".format(arg,data['name'])
   else:
    for type in ['pdu','console']:
     res = db.do("SELECT id, INET_NTOA(ip) as ip FROM {}s".format(type))
     if res > 0:
      tprows = db.get_rows()
      arglist = "call={}_list".format(type)
      for row in tprows:
       arglist = arglist + "&{}list=".format(type) + row['ip']
      print "<A CLASS=z-op DIV=div_content_left SPIN=true URL='sdcp.cgi?call={0}_inventory&{1}'>{2}</A>".format(type,arglist,type.title())
  print "<A CLASS='z-reload z-op' DIV=main URL='sdcp.cgi?{}'></A>".format(aWeb.get_args())
  print "<A CLASS='z-right z-op' DIV=div_content_left URL='sdcp.cgi?call=ipam_list'>IPAM</A>"
  print "<A CLASS='z-right z-op' DIV=div_content_left URL='sdcp.cgi?call=dns_domains'>DNS</A>"
  print "<A CLASS='z-right z-op' DIV=div_content_left URL='sdcp.cgi?call=pdu_list'>PDUs</A>"
  print "<A CLASS='z-right z-op' DIV=div_content_left URL='sdcp.cgi?call=console_list'>Consoles</A>"
  print "<A CLASS='z-right z-op' DIV=div_content_left URL='sdcp.cgi?call=rack_list'>Racks</A>"
  print "<SPAN CLASS='z-right z-navinfo'>Configuration:</SPAN>"
 print "</NAV>"
 print "<SECTION CLASS=content       ID=div_content>"
 print "<SECTION CLASS=content-left  ID=div_content_left></SECTION>"
 print "<SECTION CLASS=content-right ID=div_content_right>"
 from sdcp.core.extras import get_include
 print get_include('README.devices.html')
 print "</SECTION></SECTION>"

#
#
def list(aWeb):
 print "<ARTICLE><P>Devices</P>"
 print aWeb.button('reload',DIV='div_content_left',URL='sdcp.cgi?{}'.format(aWeb.get_args()))
 print aWeb.button('add',DIV='div_content_right',URL='sdcp.cgi?call=device_new&{}'.format(aWeb.get_args()))
 print aWeb.button('search',DIV='div_content_right',URL='sdcp.cgi?call=device_discover',MSG='Run device discovery?')
 print "<DIV CLASS=z-table>"
 print "<DIV CLASS=thead><DIV CLASS=th><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?{0}&sort=ip'>IP</A></DIV><DIV CLASS=th><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?{0}&sort=hostname'>FQDN</A></DIV><DIV CLASS=th>Model</DIV></DIV>".format(aWeb.get_args_except(['sort']))
 args = {'sort':aWeb.get('sort','ip')}
 if aWeb['target']:
  args['rack'] = "vm" if aWeb['target'] == "vm" else aWeb['arg']
 from sdcp.rest.device import list as rest_list
 res = rest_list(args)
 print "<DIV CLASS=tbody>"
 for row in res['devices']:
  print "<DIV CLASS=tr><DIV CLASS=td><A CLASS=z-op TITLE='Show device info for {0}' DIV=div_content_right URL='sdcp.cgi?call=device_info&id={3}'>{0}</A></DIV><DIV CLASS=td>{1}</DIV><DIV CLASS=td>{2}</DIV></DIV>".format(row['ipasc'], row['hostname']+"."+row['domain'], row['model'],row['id'])
 print "</DIV></DIV></ARTICLE>"

################################ Gigantic Device info and Ops function #################################
#
def info(aWeb):
 if not aWeb.cookie.get('sdcp_id'):
  print "<SCRIPT>location.replace('index.cgi')</SCRIPT>"
  return

 op    = aWeb.get('op',"")
 opres = {}
 ###################### Update ###################
 if op == 'lookup':
  from sdcp.rest.device import detect as rest_detect
  opres['lookup'] = rest_detect({'ip':aWeb['ip'],'update':True,'id':aWeb['id']})

 elif op == 'update':
  from sdcp.rest.device import update as rest_update
  from sdcp import PackageContainer as PC
  from sdcp.core.rest import call as rest_call
  d = aWeb.get_args2dict_except(['call','op','ip'])
  if d['devices_hostname'] != 'unknown':
   if not d.get('devices_vm'):
    d['devices_vm'] = 0
   if not d.get('devices_comment'):
    d['devices_comment'] = 'NULL'
   from sdcp.core import genlib as GL
   with DB() as db:
    db.do("SELECT hostname, INET_NTOA(ip) as ip, a_id, ptr_id FROM devices WHERE devices.id = {}".format(aWeb['id']))
    ddi  = db.get_row()
    xist = db.do("SELECT id FROM domains WHERE name = '{}'".format(GL.ip2arpa(ddi['ip'])))
    ddi['ptr_dom_id'] = db.get_val('id') if xist > 0 else None
    ddi['a_dom_id']   = d['devices_a_dom_id']
    xist = db.do("SELECT name FROM domains WHERE id = '{}'".format(ddi['a_dom_id']))
    fqdn = ".".join([d['devices_hostname'],db.get_val('name') if xist > 0 else 'local'])
   for type,name,content in [('a',fqdn,ddi['ip']),('ptr',GL.ip2ptr(ddi['ip']),fqdn)]:
    if ddi['%s_dom_id'%(type)]:
     opres[type] = rest_call(PC.dns['url'], "sdcp.rest.{}_record_update".format(PC.dns['type']), { 'type':type.upper(), 'id':ddi['%s_id'%(type)], 'domain_id':ddi['%s_dom_id'%(type)], 'name':name, 'content':content })
     if not str(opres[type]['id']) == str(ddi['%s_id'%(type)]):
      d['devices_%s_id'%(type)] = opres[type]['id']
   opres['update'] = rest_update(d)

 elif "book" in op:
  from sdcp.rest.booking import booking
  booking({'device_id':aWeb['id'], 'user_id':aWeb.cookie['sdcp_id'], 'op':op})

 from sdcp.rest.device import info as rest_info
 from sdcp.rest.tools  import infra as rest_infra
 dev   = rest_info({'id':aWeb['id']} if aWeb['id'] else {'ip':aWeb['ip']})
 if dev['exist'] == 0:
  print "<ARTICLE>Warning - device with either id:[{}]/ip[{}]: does not exist</ARTICLE>".format(aWeb['id'],aWeb['ip'])
  return
 if op == 'update' and dev['racked'] and (dev['rack']['pem0_pdu_id'] or dev['rack']['pem1_pdu_id']):
  from sdcp.rest.pdu import update_device_pdus
  opres['pdu'] = update_device_pdus(dev['rack'])
 infra = rest_infra(None)

 ########################## Data Tables ######################

 width= 675 if dev['racked'] == 1 and not dev['type'] == 'pdu' else 470

 print "<ARTICLE style='position:relative; resize:horizontal; margin-left:0px; width:{}px; height:255px; float:left;'>".format(width)
 print "<!-- DEV:{} -->".format(dev['info'])
 print "<!-- OP:{} -->".format(opres)
 print "<FORM ID=info_form>"
 print "<INPUT TYPE=HIDDEN NAME=id VALUE={}>".format(dev['id'])
 print "<INPUT TYPE=HIDDEN NAME=racked VALUE={}>".format(dev['racked'])
 print "<!-- Reachability Info -->"
 print "<DIV style='margin:3px; float:left; height:185px;'><DIV CLASS=title>Reachability Info</DIV>"
 print "<DIV CLASS=z-table style='width:210px;'><DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>Name:</DIV><DIV CLASS=td><INPUT NAME=devices_hostname TYPE=TEXT VALUE='{}'></DIV></DIV>".format(dev['info']['hostname'])
 print "<DIV CLASS=tr><DIV CLASS=td>IP:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['ip'])
 print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT NAME=devices_a_dom_id>"
 for dom in infra['dnscache']:
  if not "arpa" in dom['name']:
   extra = " selected" if dev['info']['a_dom_id'] == dom['id'] else ""
   print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(dom['id'],extra,dom['name'])
 print "</SELECT></DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['info']['subnet'])
 print "<DIV CLASS=tr><DIV CLASS=td>SNMP:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['info']['snmp'])
 print "<DIV CLASS=tr><DIV CLASS=td>Type:</DIV><DIV CLASS=td TITLE='Device type'><SELECT NAME=devices_type_id>"
 for type in infra['types']:
  extra = " selected" if dev['info']['type_id'] == type['id'] or (not dev['info']['type_id'] and type['name'] == 'generic') else ""
  print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(type['id'],extra,type['name'])
 print "</SELECT></DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Model:</DIV><DIV CLASS=td style='max-width:150px;'>{}</DIV></DIV>".format(dev['info']['model'])
 print "<DIV CLASS=tr><DIV CLASS=td>VM:</DIV><DIV CLASS=td><INPUT NAME=devices_vm style='width:auto;' TYPE=checkbox VALUE=1 {0}></DIV></DIV>".format("checked=checked" if dev['info']['vm'] == 1 else "") 
 print "</DIV></DIV></DIV>"

 print "<!-- Additional info -->"
 print "<DIV style='margin:3px; float:left; height:185px;'><DIV CLASS=title>Additional Info</DIV>"
 print "<DIV CLASS=z-table style='width:227px;'><DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>Rack:</DIV><DIV CLASS=td>"
 if dev['info']['vm']:
  print "Not used <INPUT TYPE=hidden NAME=rackinfo_rack_id VALUE=NULL>"
 else:
  print "<SELECT NAME=rackinfo_rack_id>"
  for rack in infra['racks']:
   extra = " selected" if ((dev['racked'] == 0 and rack['id'] == 'NULL') or (dev['racked'] == 1 and dev['rack']['rack_id'] == rack['id'])) else ""
   print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(rack['id'],extra,rack['name'])
  print "</SELECT>"
 print "</DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Lookup:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['info']['fqdn'])
 print "<DIV CLASS=tr><DIV CLASS=td>DNS A ID:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['info']['a_id'])
 print "<DIV CLASS=tr><DIV CLASS=td>DNS PTR ID:</DIV><DIV CLASS=td>{}</DIV></DIV>".format(dev['info']['ptr_id'])
 print "<DIV CLASS=tr><DIV CLASS=td>MAC:</DIV><DIV CLASS=td><INPUT TYPE=TEXT NAME=devices_mac VALUE={}></DIV></DIV>".format(dev['mac'])
 if dev['info']['graph_update'] == 1:
  print "<DIV CLASS=tr><DIV CLASS=td><A CLASS=z-op TITLE='View graphs for {1}' DIV=div_content_right URL='/munin-cgi/munin-cgi-html/{0}/{1}/index.html#content'>Graphs</A>:</DIV><DIV CLASS=td>yes</DIV></DIV>".format(dev['info']['a_name'],dev['info']['hostname']+"."+ dev['info']['a_name'])
 else:
  print "<DIV CLASS=tr><DIV CLASS=td>Graphs:</DIV><DIV CLASS=td>no</DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Booked by:</DIV>"
 if int(dev['booked']) == 0:
  print "<DIV CLASS=td STYLE='background-color:#00cc66'>None</DIV></DIV>"
 else:
  print "<DIV CLASS=td STYLE='background-color:{0}'><A CLASS=z-op DIV=div_content_right URL=sdcp.cgi?call=users_info&id={1}&op=view>{2}</A> {3}</DIV>".format("#df3620" if dev['booking']['valid'] == 1 else "orange",dev['booking']['user_id'],dev['booking']['alias'],'' if dev['booking']['valid'] else "(obsolete)")
  print "</DIV>"
 print "</DIV></DIV></DIV>"

 print "<!-- Rack Info if such exists -->"
 if dev['racked'] == 1 and not dev['type'] == 'pdu':
  print "<DIV style='margin:3px; float:left; height:185px;'><DIV CLASS=title>Rack Info</DIV>"
  print "<DIV CLASS=z-table style='width:210px;'><DIV CLASS=tbody>"
  print "<DIV CLASS=tr><DIV CLASS=td>Rack Size:</DIV><DIV CLASS=td><INPUT NAME=rackinfo_rack_size TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['rack_size'])
  print "<DIV CLASS=tr><DIV CLASS=td>Rack Unit:</DIV><DIV CLASS=td TITLE='Top rack unit of device placement'><INPUT NAME=rackinfo_rack_unit TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['rack_unit'])
  if not dev['type'] == 'console' and infra['consolexist'] > 0:
   print "<DIV CLASS=tr><DIV CLASS=td>TS:</DIV><DIV CLASS=td><SELECT NAME=rackinfo_console_id>"
   for console in infra['consoles']:
    extra = " selected='selected'" if (dev['rack']['console_id'] == console['id']) or (not dev['rack']['console_id'] and console['id'] == 'NULL') else ""
    print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(console['id'],extra,console['name'])
   print "</SELECT></DIV></DIV>"
   print "<DIV CLASS=tr><DIV CLASS=td>TS Port:</DIV><DIV CLASS=td TITLE='Console port in rack TS'><INPUT NAME=rackinfo_console_port TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['console_port'])
  else:
   print "<DIV CLASS=tr><DIV CLASS=td>&nbsp;</DIV><DIV CLASS=td>&nbsp;</DIV></DIV>"
   print "<DIV CLASS=tr><DIV CLASS=td>&nbsp;</DIV><DIV CLASS=td>&nbsp;</DIV></DIV>"

  if not dev['type'] == 'pdu' and infra['pduxist'] > 0:
   for pem in ['pem0','pem1']:
    print "<DIV CLASS=tr><DIV CLASS=td>{0} PDU:</DIV><DIV CLASS=td><SELECT NAME=rackinfo_{1}_pdu_slot_id>".format(pem.upper(),pem)
    for pdu in infra['pdus']:
     for slotid in range(0,pdu['slots'] + 1):
      extra = " selected" if ((dev['rack'][pem+"_pdu_id"] == pdu['id']) and (dev['rack'][pem+"_pdu_slot"] == pdu[str(slotid)+"_slot_id"])) or (not dev['rack'][pem+"_pdu_id"] and  pdu['id'] == 'NULL')else ""
      print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(str(pdu['id'])+"."+str(pdu[str(slotid)+"_slot_id"]), extra, pdu['name']+":"+pdu[str(slotid)+"_slot_name"])
    print "</SELECT></DIV></DIV>"
    print "<DIV CLASS=tr><DIV CLASS=td>{0} Unit:</DIV><DIV CLASS=td><INPUT NAME=rackinfo_{1}_pdu_unit TYPE=TEXT PLACEHOLDER='{2}'></DIV></DIV>".format(pem.upper(),pem,dev['rack'][pem + "_pdu_unit"])
  else:
   for index in range(0,4):
    print "<DIV CLASS=tr><DIV CLASS=td>&nbsp;</DIV><DIV CLASS=td>&nbsp;</DIV></DIV>"
  print "</DIV></DIV></DIV>"
 print "<DIV STYLE='display:block; font-size:11px; clear:both; margin-bottom:3px; width:99%'><SPAN>Comments:</SPAN><INPUT STYLE='width:{}px; border:none; background-color:white; overflow-x:auto; font-size:11px;' TYPE=TEXT NAME=devices_comment VALUE='{}'></DIV>".format(width-90,"" if not dev['info']['comment'] else dev['info']['comment'])
 print "</FORM>"

 print "<!-- Controls -->"
 print "<DIV STYLE='clear:left;'>"
 print aWeb.button('reload',DIV='div_content_right',URL='sdcp.cgi?call=device_info&id=%i'%dev['id'])
 print aWeb.button('delete',DIV='div_content_right',URL='sdcp.cgi?call=device_remove&id=%i'%dev['id'], MSG='Are you sure you want to delete device?', TITLE='Delete device')
 print aWeb.button('search',DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=lookup&id={}&ip={}'.format(dev['id'],dev['ip']), TITLE='Lookup and Detect Device information')
 print aWeb.button('save',  DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=update', FRM='info_form', TITLE='Save Device Information and Update DDI and PDU')
 if dev['booked']:
  if int(aWeb.cookie.get('sdcp_id')) == dev['booking']['user_id']:
   print aWeb.button('remove',DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=debook&id=%i'%dev['id'],TITLE='Unbook')
 else:
   print aWeb.button('add',   DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=book&id=%i'%dev['id'],TITLE='Book')   
 print aWeb.button('document',  DIV='div_dev_data', URL='sdcp.cgi?call=device_conf_gen&type_name=%s&id=%i'%(dev['info']['type_name'],dev['id']),TITLE='Generate System Conf')
 from sdcp import PackageContainer as PC
 print aWeb.button('term',TITLE='SSH',HREF='ssh://%s@%s'%(PC.netconf['username'],dev['ip']))
 if dev['racked'] == 1 and (dev['rack']['console_ip'] and dev['rack'].get('console_port',0) > 0):
  print aWeb.button('term',TITLE='Console', HREF='telnet://%s:%i'%(dev['rack']['console_ip'],6000+dev['rack']['console_port']))

 res = ""
 for key,value in opres.iteritems():
  if value.get('res','NOT_FOUND') != 'OK':
   res += "{}({})".format(key,value)
 print "<SPAN ID=upd_results style='text-overflow:ellipsis; overflow:hidden; float:right; font-size:9px;'>{}</SPAN>".format(res)
 print "</DIV>"
 print "</ARTICLE>"

 print "<!-- Function navbar and content -->"
 print "<NAv STYLE='top:260px;'>"
 try:
  from importlib import import_module
  module = import_module("sdcp.devices.{}".format(dev['info']['type_name']))
  Device = getattr(module,'Device',None)
  functions = Device.get_widgets() if Device else []
  if functions:
   if functions[0] == 'operated':
    if dev['info']['type_name'] == 'esxi':
     print "<A CLASS=z-op DIV=main URL='sdcp.cgi?call=esxi_main&id={}'>Manage</A></B></DIV>".format(id)
   else:
    for fun in functions:
     funname = " ".join(fun.split('_')[1:])
     print "<A CLASS=z-op DIV=div_dev_data SPIN=true URL='sdcp.cgi?call=device_op_function&ip={0}&type={1}&op={2}'>{3}</A>".format(dev['ip'], dev['info']['type_name'], fun, funname.title())
 except:
  print "&nbsp;"
 print "</NAV>"
 print "<SECTION CLASS='content' ID=div_dev_data style='top:294px; overflow-x:hidden; overflow-y:auto; z-index:100'></SECTION>"


####################################################### Functions #######################################################
#
# View operation data / widgets
#

def conf_gen(aWeb):
 from importlib import import_module
 id = aWeb.get('id','0')
 type = aWeb['type_name']
 print "<ARTICLE>"
 with DB() as db:
  db.do("SELECT INET_NTOA(ip) AS ipasc, hostname,domains.name as domain, INET_NTOA(subnets.gateway) as gateway, INET_NTOA(subnets.subnet) AS subnet, subnets.mask FROM devices LEFT JOIN domains ON domains.id = devices.a_dom_id JOIN subnets ON subnets.id = devices.subnet_id WHERE devices.id = '{}'".format(id))
  row = db.get_row()
 try:
  module = import_module("sdcp.devices.{}".format(type))
  dev = getattr(module,'Device',lambda x: None)(row['ipasc'])
  dev.print_conf({'name':row['hostname'], 'domain':row['domain'], 'gateway':row['gateway'], 'subnet':row['subnet'], 'mask':row['mask']})
 except Exception as err:
  print "No instance config specification for type:[{}]".format(type)
 print "</ARTICLE>"

#
#
#
def op_function(aWeb):
 from sdcp.core import extras as EXT
 from importlib import import_module
 print "<ARTICLE>"
 try:
  module = import_module("sdcp.devices.{}".format(aWeb['type']))
  dev = getattr(module,'Device',lambda x: None)(aWeb['ip'])
  with dev:
   EXT.dict2table(getattr(dev,aWeb['op'],None)())
 except Exception as err:
  print "<B>Error in devdata: {}</B>".format(str(err))
 print "</ARTICLE>"

#
#
#
def mac_sync(aWeb):
 from sdcp.core import genlib as GL
 print "<ARTICLE CLASS=info>"
 print "<DIV CLASS=z-table>"
 print "<DIV CLASS=thead><DIV CLASS=th>Id</DIV><DIV CLASS=th>IP</DIV><DIV CLASS=th>Hostname</DIV><DIV CLASS=th>MAC</DIV></DIV>"
 print "<DIV CLASS=tbody>"
 try:
  arps = {}
  with open('/proc/net/arp') as f:
   _ = f.readline()
   for data in f:
    ( ip, _, _, mac, _, _ ) = data.split()
    if not mac == '00:00:00:00:00:00':
     arps[ip] = mac
  with DB() as db:
   db.do("SELECT id, hostname, INET_NTOA(ip) as ipasc,mac FROM devices WHERE hostname <> 'unknown' ORDER BY ip")
   rows = db.get_rows()
   for row in rows:
    xist = arps.get(row['ipasc'],None)
    print "<DIV CLASS=tr><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV></DIV>".format(row['id'],row['ipasc'],row['hostname'],xist)
    if xist:
     db.do("UPDATE devices SET mac = {} WHERE id = {}".format(GL.mac2int(xist),row['id']))
 except:
  pass
 print "</DIV></DIV></ARTICLE>"

#
# new device:
#
def new(aWeb):
 ip     = aWeb.get('ip',None)
 name   = aWeb.get('hostname','unknown')
 mac    = aWeb.get('mac',"00:00:00:00:00:00")
 op     = aWeb['op']
 subnet_id = aWeb['subnet_id']
 if not ip:
  from sdcp.core import genlib as GL
  ip = "127.0.0.1" if not aWeb['ipint'] else GL.int2ip(int(aWeb['ipint']))
 from sdcp.rest import sdcpipam

 if op == 'new':
  from sdcp.rest.device import new as rest_new

  a_dom_id,_,domain = aWeb['a_dom_id'].partition('_')
  fqdn = "{}.{}".format(name,domain)
  args = { 'ip':ip, 'mac':mac, 'hostname':name, 'fqdn':fqdn, 'a_dom_id':a_dom_id, 'subnet_id':subnet_id }

  if aWeb['vm']:
   args['vm'] = 1
  else:
   args['target'] = aWeb['target']
   args['arg']    = aWeb['arg']
   args['vm'] = 0
  res  = rest_new(args)
  print "DB:{}".format(res)
  aWeb.log("{} - 'new device' operation:[{}] -> [{}]".format(aWeb.cookie.get('sdcp_user'),args,res))
 elif op == 'find':
  res  = sdcpipam.find({'id':subnet_id})
  print "IP:{}".format(res['ip'])
 else:
  domain = aWeb['domain']
  subnets = sdcpipam.list(None)['subnets']
  with DB() as db:
   db.do("SELECT id, name FROM domains")
   domains = db.get_rows()
  print "<ARTICLE CLASS=info><P>Add Device</P>"
  print "<!-- {} -->".format(aWeb.get_args2dict_except())
  print "<FORM ID=device_new_form>"
  print "<DIV CLASS=z-table><DIV CLASS=tbody>"
  print "<DIV CLASS=tr><DIV CLASS=td>IP:</DIV><DIV CLASS=td><INPUT       NAME=ip       TYPE=TEXT VALUE={}></DIV></DIV>".format(ip)
  print "<DIV CLASS=tr><DIV CLASS=td>Hostname:</DIV><DIV CLASS=td><INPUT NAME=hostname TYPE=TEXT VALUE={}></DIV></DIV>".format(name)
  print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT  NAME=a_dom_id>"
  for d in domains:
   if not "in-addr.arpa" in d.get('name'):
    print "<OPTION VALUE={0}_{2} {1}>{2}</OPTION>".format(d['id'],"selected" if d['name'] == domain else "",d['name'])
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td><SELECT NAME=subnet_id>"
  for s in subnets:
   print "<OPTION VALUE={} {}>{} ({})</OPTION>".format(s['id'],"selected" if str(s['id']) == subnet_id else "", s['subnet'],s['description'])
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>MAC:</DIV><DIV CLASS=td><INPUT NAME=mac TYPE=TEXT PLACEHOLDER='{0}'></DIV></DIV>".format(mac)
  if aWeb['target'] == 'rack_id':
   print "<INPUT TYPE=HIDDEN NAME=target VALUE={}>".format(aWeb['target'])
   print "<INPUT TYPE=HIDDEN NAME=arg VALUE={}>".format(aWeb['arg'])
  else:
   print "<DIV CLASS=tr><DIV CLASS=td>VM:</DIV><DIV  CLASS=td><INPUT NAME=vm  TYPE=CHECKBOX VALUE=1  {0} ></DIV></DIV>".format("checked" if aWeb['target'] == 'vm' else '')
  print "</DIV></DIV>"
  print "</FORM>"
  print aWeb.button('start', DIV='device_new_span', URL='sdcp.cgi?call=device_new&op=new',  FRM='device_new_form', TITLE='Create')
  print aWeb.button('search',DIV='device_new_span', URL='sdcp.cgi?call=device_new&op=find', FRM='device_new_form', TITLE='Find IP')
  print "<SPAN ID=device_new_span style='max-width:400px; font-size:9px; float:right'></SPAN>"
  print "</ARTICLE>"

#
#
#
def remove(aWeb):
 from sdcp.rest.device import remove as rest_remove
 id  = aWeb['id']
 ret = rest_remove({ 'id':id })
 print "<ARTICLE>"
 print "Unit {} deleted, DB:{}".format(id,ret['deleted'])
 if ret['res'] == 'OK':
  from sdcp.core.rest import call as rest_call
  from sdcp import PackageContainer as PC
  arec = rest_call(PC.dns['url'],"sdcp.rest.{}_record_remove".format(PC.dns['type']),{'id':ret['a_id']})   if ret['a_id']   else 0
  prec = rest_call(PC.dns['url'],"sdcp.rest.{}_record_remove".format(PC.dns['type']),{'id':ret['ptr_id']}) if ret['ptr_id'] else 0
  print ",A:{},PTR:{}".format(arec,prec)
 print "</ARTICLE>"

#
# find devices operations
#
def discover(aWeb):
 op = aWeb['op']
 if op:
  from sdcp.rest.device import discover
  clear = aWeb.get('clear',False)
  a_dom = aWeb['a_dom_id']
  ipam  = aWeb.get('ipam_subnet',"0_0_32").split('_')
  # id, subnet int, subnet mask
  res = discover({ 'subnet_id':ipam[0], 'ipam_mask':ipam[2], 'start':int(ipam[1]), 'end':int(ipam[1]) + 2**(32-int(ipam[2])) - 1, 'a_dom_id':a_dom, 'clear':clear})
  print "<ARTICLE>%s</ARTICLE>"%(res)
 else:
  with DB() as db:
   db.do("SELECT id, subnet, INET_NTOA(subnet) as subasc, mask, description FROM subnets ORDER BY subnet");
   subnets = db.get_rows()
   db.do("SELECT id, name FROM domains")
   domains  = db.get_rows()
  dom_name = aWeb['domain']
  print "<ARTICLE CLASS=info><P>Device Discovery</P>"
  print "<FORM ID=device_discover_form>"
  print "<INPUT TYPE=HIDDEN NAME=op VALUE=json>"
  print "<DIV CLASS=z-table><DIV CLASS=tbody>"
  print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT NAME=a_dom_id>"
  for d in domains:
   if not "in-addr.arpa" in d.get('name'):
    extra = "" if not dom_name == d.get('name') else "selected=selected"
    print "<OPTION VALUE={0} {2}>{1}</OPTION>".format(d.get('id'),d.get('name'),extra)
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td><SELECT NAME=ipam_subnet>"
  for s in subnets:
   print "<OPTION VALUE={0}_{1}_{3}>{2}/{3} ({4})</OPTION>".format(s.get('id'),s.get('subnet'),s.get('subasc'),s.get('mask'),s.get('description'))
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>Clear DB<B>??</B>:</DIV><DIV CLASS=td><INPUT TYPE=checkbox NAME=clear VALUE=True></DIV></DIV>"
  print "</DIV></DIV>"
  print aWeb.button('start', DIV='div_content_right', SPIN='true', URL='sdcp.cgi?call=device_discover', FRM='device_discover_form')
  print "</ARTICLE>"

#
# clear db
#
def clear_db(aWeb):
 with DB() as db:
  db.do("TRUNCATE TABLE devices")
 print "<<ARTICLE>Cleared DB</ARTICLE>"
