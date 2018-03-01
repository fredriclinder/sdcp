"""Module docstring.

HTML5 Ajax Device calls module

"""
__author__= "Zacharias El Banna"
__version__ = "18.02.09GA"
__status__ = "Production"
__icon__ = 'images/icon-network.png'

########################################## Device Operations ##########################################

def main(aWeb):
 target = aWeb['target']
 arg    = aWeb['arg']

 print "<NAV><UL>"
 print "<LI><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=device_list{0}'>Devices</A></LI>".format('' if (not target or not arg) else "&target="+target+"&arg="+arg)
 print "<LI><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=bookings_list'>Bookings</A></LI>"
 if target == 'vm':
  print "<LI><A CLASS='z-op reload' DIV=main URL='sdcp.cgi?{}'></A></LI>".format(aWeb.get_args())
 else:
  data = aWeb.rest_call("racks_info",{'id':arg} if target == 'rack_id' else None)
  for type in ['pdu','console']:
   if len(data[type]) > 0:
    print "<LI CLASS='dropdown'><A>%s</A><DIV CLASS='dropdown-content'>"%(type.title())
    for row in data[type]:
     print "<A CLASS=z-op DIV=div_content_left SPIN=true URL='sdcp.cgi?call=%s_inventory&ip=%s'>%s</A>"%(row['type'],row['ipasc'],row['hostname'])
    print "</DIV></LI>"
  if data.get('name'):
   print "<LI><A CLASS='z-op' DIV=div_content_right  URL='sdcp.cgi?call=rack_inventory&rack=%s'>'%s' info</A></LI>"%(arg,data['name'])
  print "<LI><A CLASS='z-op reload' DIV=main URL='sdcp.cgi?{}'></A></LI>".format(aWeb.get_args())
  print "<LI CLASS=right><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=ipam_list'>IPAM</A></LI>"
  print "<LI CLASS=right><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=dns_list'>DNS</A></LI>"
  print "<LI CLASS='right dropdown'><A>Rackinfo</A><DIV CLASS='dropdown-content'>"
  print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=rack_list_infra&type=pdu'>PDUs</A>"
  print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=rack_list_infra&type=console'>Consoles</A>"
  print "<A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?call=rack_list'>Racks</A>"
  print "</DIV></LI>"
 print "</UL></NAV>"
 print "<SECTION CLASS=content       ID=div_content>"
 print "<SECTION CLASS=content-left  ID=div_content_left></SECTION>"
 print "<SECTION CLASS=content-right ID=div_content_right></SECTION>"
 print "</SECTION>"
 print "<SCRIPT>include_html('div_content_right','README.devices.html');</SCRIPT>"

#
#
def list(aWeb):
 args = {'sort':aWeb.get('sort','ip')}
 if aWeb['target']:
  args['rack'] = "vm" if aWeb['target'] == "vm" else aWeb['arg']
 res = aWeb.rest_call("device_list",args)
 print "<ARTICLE><P>Devices</P><DIV CLASS='controls'>"
 print aWeb.button('reload',DIV='div_content_left',URL='sdcp.cgi?{}'.format(aWeb.get_args()))
 print aWeb.button('add',DIV='div_content_right',URL='sdcp.cgi?call=device_new&{}'.format(aWeb.get_args()))
 print aWeb.button('search',DIV='div_content_right',URL='sdcp.cgi?call=device_discover')
 print aWeb.button('save'  ,DIV='div_content_right', URL='sdcp.cgi?call=device_graph_save')
 print "</DIV>"
 print "<DIV CLASS=table>"
 print "<DIV CLASS=thead><DIV CLASS=th><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?{0}&sort=ip'>IP</A></DIV><DIV CLASS=th><A CLASS=z-op DIV=div_content_left URL='sdcp.cgi?{0}&sort=hostname'>FQDN</A></DIV><DIV CLASS=th>Model</DIV></DIV>".format(aWeb.get_args(['sort']))
 print "<DIV CLASS=tbody>"
 for row in res['data']:
  print "<DIV CLASS=tr><DIV CLASS=td><A CLASS=z-op DIV=div_content_right URL='sdcp.cgi?call=device_info&id=%i'>%s</A></DIV><DIV CLASS=td STYLE='max-width:180px; overflow-x:hidden'>%s.%s</DIV><DIV CLASS=td>%s</DIV></DIV>"%(row['id'],row['ipasc'], row['hostname'],row['domain'], row['model'])
 print "</DIV></DIV></ARTICLE>"

#
#
################################ Gigantic Device info and Ops function #################################
#
#
# Simplify REST calls for this one TODO
#
def info(aWeb):
 if not aWeb.cookies.get('sdcp'):
  print "<SCRIPT>location.replace('index.cgi')</SCRIPT>"
  return

 cookie = aWeb.cookie_unjar('sdcp')

 ###################### Update ###################
 opres = {}

 if aWeb['op'] == 'update':
  d = aWeb.get_args2dict(['call','op','ip'])
  if d['devices_hostname'] != 'unknown':
   from ..core import genlib as GL
   if not d.get('devices_vm'):
    d['devices_vm'] = 0
   if not d.get('devices_comment'):
    d['devices_comment'] = 'NULL'

   dns   = aWeb.rest_call("dns_list_domains_cache",{'filter':'forward','dict':'id'})['domains']

   fqdn   = ".".join([d['devices_hostname'],  dns[d['devices_a_dom_id']]['name']])
   dom_id = aWeb.rest_call("dns_list_domains",{'filter':'reverse','dict':'name'})['domains'].get(GL.ip2arpa(aWeb['ip']),{}).get('id')

   opres['a'] = aWeb.rest_call("dns_record_update", { 'type':'A', 'id':d['devices_a_id'], 'domain_id':d['devices_a_dom_id'], 'name':fqdn, 'content':aWeb['ip'] })
   if dom_id:
    opres['ptr'] = aWeb.rest_call("dns_record_update", { 'type':'PTR', 'id':d['devices_ptr_id'], 'domain_id':dom_id, 'name':GL.ip2ptr(aWeb['ip']), 'content':fqdn })
   else:
    opres['ptr'] = {'id':0,'info':'nonexisting_ptr_domain'}

   for type in ['a','ptr']:
    if not str(opres[type]['id']) == str(d['devices_%s_id'%type]):
     d['devices_%s_id'%type] = opres[type]['id']
    else:
     d.pop('devices_%s_id'%type,None)

   opres['update'] = aWeb.rest_call("device_update",d)

 restargs = {'id':aWeb['id'],'ip':aWeb['ip']}
 restargs.update({'info':['username','booking','rackinfo','basics'],'op':aWeb['op']})

 dev   = aWeb.rest_call("device_info",restargs)
 infra = aWeb.rest_call("sdcp_infra")

 if dev['xist'] == 0:
  print "<ARTICLE>Warning - device with either id:[{}]/ip[{}]: does not exist</ARTICLE>".format(aWeb['id'],aWeb['ip'])
  return
 if aWeb['op'] == 'update' and dev['racked'] and (dev['rack']['pem0_pdu_id'] or dev['rack']['pem1_pdu_id']):
  opres['pdu'] = aWeb.rest_call("device_update_pdu",dev['rack'])
 print opres

 ########################## Data Tables ######################

 width = 680 if dev['racked'] == 1 and not dev['type'] == 'pdu' else 470

 print "<ARTICLE CLASS='info' STYLE='position:relative; width:%spx;'><P TITLE='%s'>Device Info</P>"%(width,dev['id'])
 print "<!-- OP:{} -->".format(opres)
 print "<FORM ID=info_form>"
 print "<INPUT TYPE=HIDDEN NAME=id VALUE={}>".format(dev['id'])
 print "<INPUT TYPE=HIDDEN NAME=racked VALUE={}>".format(dev['racked'])
 print "<!-- Reachability Info -->"
 print "<DIV STYLE='margin:3px; float:left; height:172px;'>"
 print "<DIV CLASS=table STYLE='width:210px;'><DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>Name:</DIV><DIV CLASS=td><INPUT NAME=devices_hostname TYPE=TEXT VALUE='{}'></DIV></DIV>".format(dev['info']['hostname'])
 print "<DIV CLASS=tr><DIV CLASS=td>IP:</DIV><DIV CLASS=td><INPUT NAME=ip TYPE=TEXT VALUE={} READONLY></DIV></DIV>".format(dev['ip'])
 print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT NAME=devices_a_dom_id>"
 for dom in infra['domains']:
  extra = " selected" if dev['info']['a_dom_id'] == dom['id'] else ""
  print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(dom['id'],extra,dom['name'])
 print "</SELECT></DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td><A CLASS=z-op DIV=div_content_right URL=sdcp.cgi?call=ipam_layout&id=%s>%s</A></DIV></DIV>"%(dev['info']['subnet_id'],dev['info']['subnet'])
 print "<DIV CLASS=tr><DIV CLASS=td>Type:</DIV><DIV CLASS=td TITLE='Device type'><SELECT NAME=devices_type_id>"
 for type in infra['types']:
  extra = " selected" if dev['info']['type_id'] == type['id'] or (not dev['info']['type_id'] and type['name'] == 'generic') else ""
  print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(type['id'],extra,type['name'])
 print "</SELECT></DIV></DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>Model:</DIV><DIV CLASS=td STYLE='max-width:150px;'><INPUT TYPE=TEXT READONLY VALUE='%s'></DIV></DIV>"%(dev['info']['model'])
 print "<DIV CLASS=tr><DIV CLASS=td>VM:</DIV><DIV CLASS=td><INPUT NAME=devices_vm TYPE=checkbox VALUE=1 {0}></DIV></DIV>".format("checked=checked" if dev['info']['vm'] == 1 else "") 
 print "</DIV></DIV></DIV>"

 print "<!-- Additional info -->"
 print "<DIV STYLE='margin:3px; float:left; height:172px;'>"
 print "<DIV CLASS=table STYLE='width:227px;'><DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>Rack:</DIV>"
 if dev['info']['vm']:
  print "<DIV CLASS=td>Not used <INPUT TYPE=hidden NAME=rackinfo_rack_id VALUE=NULL></DIV>"
 else:
  print "<DIV CLASS=td><SELECT NAME=rackinfo_rack_id>"
  for rack in infra['racks']:
   extra = " selected" if ((dev['racked'] == 0 and rack['id'] == 'NULL') or (dev['racked'] == 1 and dev['rack']['rack_id'] == rack['id'])) else ""
   print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(rack['id'],extra,rack['name'])
  print "</SELECT></DIV>"
 print "</DIV>"
 print "<DIV CLASS=tr><DIV CLASS=td>DNS A ID:</DIV><DIV CLASS=td><INPUT TYPE=TEXT NAME=devices_a_id VALUE='%s' READONLY></DIV></DIV>"%(dev['info']['a_id'])
 print "<DIV CLASS=tr><DIV CLASS=td>DNS PTR ID:</DIV><DIV CLASS=td><INPUT TYPE=TEXT NAME=devices_ptr_id VALUE='%s' READONLY></DIV></DIV>"%(dev['info']['ptr_id'])
 print "<DIV CLASS=tr><DIV CLASS=td>SNMP:</DIV><DIV CLASS=td><INPUT TYPE=TEXT READONLY VALUE='%s'></DIV></DIV>"%(dev['info']['snmp'])
 print "<DIV CLASS=tr><DIV CLASS=td>MAC:</DIV><DIV CLASS=td><INPUT TYPE=TEXT NAME=devices_mac VALUE={}></DIV></DIV>".format(dev['mac'])
 print "<DIV CLASS=tr><DIV CLASS=td><A CLASS=z-op TITLE='update graph state' DIV=div_content_right URL=sdcp.cgi?call=device_graph_info&id=%s>Graphing</A></DIV>"%(dev['id'])
 if dev['info']['graph_update'] == 1:
  print "<DIV CLASS=td><A CLASS=z-op TITLE='View graphs for {1}' DIV=div_content_right URL='/munin-cgi/munin-cgi-html/{0}/{1}/index.html#content'>yes</A></DIV></DIV>".format(dev['info']['domain'],dev['fqdn'])
 else:
  print "<DIV CLASS=td>no</DIV></DIV>"
 print "<DIV CLASS=tr ID=div_booking_info><DIV CLASS=td>Booked by:</DIV>"
 if dev['booked']:
  print "<DIV CLASS='td %s'>"%("red" if dev['booking']['valid'] == 1 else "orange")
  if dev['booking']['user_id'] == int(cookie['id']):
   print "<A CLASS=z-op DIV=div_booking_info URL='sdcp.cgi?call=bookings_update&op=debook&id=%s'>%s</A>"%(dev['id'],dev['booking']['alias'])
  else:
   print dev['booking']['alias']
  print "</DIV>"
 else:
  print "<DIV CLASS='td green'><A CLASS=z-op DIV=div_booking_info URL='sdcp.cgi?call=bookings_update&op=book&id=%s'>None</A></DIV>"%dev['id']
 print "</DIV>"
 print "</DIV></DIV></DIV>"

 print "<!-- Rack Info if such exists -->"
 if dev['racked'] == 1 and not dev['type'] == 'pdu':
  print "<!-- %s -->"%dev['type']
  print "<DIV STYLE='margin:3px; float:left; height:172px;'>"
  print "<DIV CLASS=table STYLE='width:210px;'><DIV CLASS=tbody>"
  if not dev['type'] == 'controlplane':
   print "<DIV CLASS=tr><DIV CLASS=td>Rack Size:</DIV><DIV CLASS=td><INPUT NAME=rackinfo_rack_size TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['rack_size'])
   print "<DIV CLASS=tr><DIV CLASS=td>Rack Unit:</DIV><DIV CLASS=td TITLE='Top rack unit of device placement'><INPUT NAME=rackinfo_rack_unit TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['rack_unit'])
  if not dev['type'] == 'console' and infra['consolexist'] > 0:
   print "<DIV CLASS=tr><DIV CLASS=td>TS:</DIV><DIV CLASS=td><SELECT NAME=rackinfo_console_id>"
   for console in infra['consoles']:
    extra = " selected='selected'" if (dev['rack']['console_id'] == console['id']) or (not dev['rack']['console_id'] and console['id'] == 'NULL') else ""
    print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(console['id'],extra,console['hostname'])
   print "</SELECT></DIV></DIV>"
   print "<DIV CLASS=tr><DIV CLASS=td>TS Port:</DIV><DIV CLASS=td TITLE='Console port in rack TS'><INPUT NAME=rackinfo_console_port TYPE=TEXT PLACEHOLDER='{}'></DIV></DIV>".format(dev['rack']['console_port'])
  if not dev['type'] == 'controlplane' and infra['pduxist'] > 0:
   for pem in ['pem0','pem1']:
    print "<DIV CLASS=tr><DIV CLASS=td>{0} PDU:</DIV><DIV CLASS=td><SELECT NAME=rackinfo_{1}_pdu_slot_id>".format(pem.upper(),pem)
    for pdu in infra['pdus']:
     pduinfo = infra['pduinfo'].get(str(pdu['id']))
     if pduinfo:
      for slotid in range(0,pduinfo['slots']):
       pdu_slot_id   = pduinfo[str(slotid)+"_slot_id"]
       pdu_slot_name = pduinfo[str(slotid)+"_slot_name"]
       extra = "selected" if ((dev['rack'][pem+"_pdu_id"] == pdu['id']) and (dev['rack'][pem+"_pdu_slot"] == pdu_slot_id)) or (not dev['rack'][pem+"_pdu_id"] and  pdu['id'] == 'NULL') else ""
       print "<OPTION VALUE=%s.%s %s>%s</OPTION>"%(pdu['id'],pdu_slot_id, extra, pdu['hostname']+":"+pdu_slot_name)
    print "</SELECT></DIV></DIV>"
    print "<DIV CLASS=tr><DIV CLASS=td>{0} Unit:</DIV><DIV CLASS=td><INPUT NAME=rackinfo_{1}_pdu_unit TYPE=TEXT PLACEHOLDER='{2}'></DIV></DIV>".format(pem.upper(),pem,dev['rack'][pem + "_pdu_unit"])
  print "</DIV></DIV></DIV>"
 print "<DIV STYLE='display:block; clear:both; margin-bottom:3px; margin-top:1px; width:99%'><SPAN>Comments:</SPAN><INPUT CLASS='white' STYLE='width:{}px; overflow-x:auto;' TYPE=TEXT NAME=devices_comment VALUE='{}'></DIV>".format(width-90,"" if not dev['info']['comment'] else dev['info']['comment'])
 print "</FORM><DIV CLASS=controls>"
 print aWeb.button('reload',DIV='div_content_right',URL='sdcp.cgi?call=device_info&id=%i'%dev['id'])
 print aWeb.button('delete',DIV='div_content_right',URL='sdcp.cgi?call=device_delete&id=%i'%dev['id'], MSG='Are you sure you want to delete device?', TITLE='Delete device')
 print aWeb.button('search',DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=lookup&id={}&ip={}'.format(dev['id'],dev['ip']), TITLE='Lookup and Detect Device information')
 print aWeb.button('save',  DIV='div_content_right',URL='sdcp.cgi?call=device_info&op=update', FRM='info_form', TITLE='Save Device Information and Update DDI and PDU')
 print aWeb.button('document',  DIV='div_dev_data', URL='sdcp.cgi?call=device_conf_gen&id=%i'%(dev['id']),TITLE='Generate System Conf')
 print aWeb.a_button('term',TITLE='SSH',HREF='ssh://%s@%s'%(dev['username'],dev['ip']))
 if dev['racked'] == 1 and (dev['rack']['console_ip'] and dev['rack'].get('console_port',0) > 0):
  print aWeb.a_button('term',TITLE='Console', HREF='telnet://%s:%i'%(dev['rack']['console_ip'],6000+dev['rack']['console_port']))

 # ["%s(%s)"%(key,value) for key,value in opres.iteritems() if value.get('res','NOT_FOUND') != 'OK']
 res = ""
 for key,value in opres.iteritems():
  if value.get('res','NOT_FOUND') != 'OK':
   res += "{}({})".format(key,value)
 print "<SPAN CLASS='results' ID=update_results>%s</SPAN>"%str(dev.get('result',''))
 print "</DIV></ARTICLE>"

 print "<!-- Function navbar and content -->"
 print "<NAV><UL>"
 for fun in dev['info']['functions'].split(','):
  if fun == 'manage':
   print "<LI><A CLASS=z-op DIV=main URL='sdcp.cgi?call=%s_manage&id=%i'>Manage</A></LI>"%(dev['info']['type_name'],dev['id'])
  else:
   print "<LI><A CLASS=z-op DIV=div_dev_data SPIN=true URL='sdcp.cgi?call=device_function&ip={0}&type={1}&op={2}'>{3}</A></LI>".format(dev['ip'], dev['info']['type_name'], fun, fun.title())
 print "</UL></NAV>"
 print "<SECTION CLASS='content' ID=div_dev_data STYLE='top:307px; overflow-x:hidden; overflow-y:auto;'></SECTION>"


####################################################### Functions #######################################################
#
# View operation data / widgets
#

def conf_gen(aWeb):
 print "<ARTICLE>"
 res = aWeb.rest_call("device_configuration_template",{'id':aWeb['id']})
 if res['result'] == 'OK':
  print "<BR>".join(res['data'])
 else:
  print "<B>Error in devdata: %s</B>"%res['info']
 print "</ARTICLE>"

#
#
#
def function(aWeb):
 print "<ARTICLE>"
 res = aWeb.rest_call("device_function",{'ip':aWeb['ip'],'op':aWeb['op'],'type':aWeb['type']})
 if res['result'] == 'OK':
  from ..core import extras as EXT
  EXT.dict2table(res['data'])
 else:
  print "<B>Error in devdata: %s</B>"%res['info']
 print "</ARTICLE>"

#
#
#
def mac_sync(aWeb):
 macs = aWeb.rest_call("sdcp_mac_sync")
 print "<ARTICLE CLASS=info>"
 print "<DIV CLASS=table>"
 print "<DIV CLASS=thead><DIV CLASS=th>Id</DIV><DIV CLASS=th>IP</DIV><DIV CLASS=th>Hostname</DIV><DIV CLASS=th>MAC</DIV></DIV>"
 print "<DIV CLASS=tbody>"
 for row in macs:
  print "<DIV CLASS=tr><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV><DIV CLASS=td>{}</DIV></DIV>".format(row['id'],row['ipasc'],row['hostname'],row['xist'])
 print "</DIV></DIV></ARTICLE>"

#
# new device:
#
def new(aWeb):
 cookie = aWeb.cookie_unjar('sdcp')
 if not aWeb.cookies.get('sdcp'):
  print "<SCRIPT>location.replace('index.cgi')</SCRIPT>"
  return
 ip     = aWeb.get('ip')
 name   = aWeb.get('hostname','unknown')
 mac    = aWeb.get('mac',"00:00:00:00:00:00")
 op     = aWeb['op']
 subnet_id = aWeb['subnet_id']
 if not ip:
  from ..core import genlib as GL
  ip = "127.0.0.1" if not aWeb['ipint'] else GL.int2ip(int(aWeb['ipint']))

 if op == 'new':
  args = { 'ip':ip, 'mac':mac, 'hostname':name, 'a_dom_id':aWeb['a_dom_id'], 'subnet_id':subnet_id }
  if aWeb['vm']:
   args['vm'] = 1
  else:
   args['target'] = aWeb['target']
   args['arg']    = aWeb['arg']
   args['vm'] = 0
  res = aWeb.rest_call("device_new",args)
  print "Operation:%s"%str(res)
  aWeb.log("{} - 'new device' operation:[{}] -> [{}]".format(cookie['id'],args,res))
 elif op == 'find':
  print aWeb.rest_call("ipam_find",{'id':subnet_id})['ip']
 else:
  subnets = aWeb.rest_call("ipam_list")['subnets']
  domains = aWeb.rest_call("dns_list_domains",{'filter':'forward'})['domains']
  print "<ARTICLE CLASS=info><P>Add Device</P>"
  print "<FORM ID=device_new_form>"
  print "<DIV CLASS=table><DIV CLASS=tbody>"
  print "<DIV CLASS=tr><DIV CLASS=td>Hostname:</DIV><DIV CLASS=td><INPUT NAME=hostname TYPE=TEXT VALUE={}></DIV></DIV>".format(name)
  print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT  NAME=a_dom_id>"
  for d in domains:
   print "<OPTION VALUE={0} {1}>{2}</OPTION>".format(d['id'],"selected" if d['name'] == aWeb['domain'] else "",d['name'])
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td><SELECT NAME=subnet_id>"
  for s in subnets:
   print "<OPTION VALUE={} {}>{} ({})</OPTION>".format(s['id'],"selected" if str(s['id']) == subnet_id else "", s['subasc'],s['description'])
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>IP:</DIV><DIV CLASS=td><INPUT  NAME=ip ID=device_ip TYPE=TEXT VALUE='{}'></DIV></DIV>".format(ip)
  print "<DIV CLASS=tr><DIV CLASS=td>MAC:</DIV><DIV CLASS=td><INPUT NAME=mac TYPE=TEXT PLACEHOLDER='{0}'></DIV></DIV>".format(mac)
  if aWeb['target'] == 'rack_id':
   print "<INPUT TYPE=HIDDEN NAME=target VALUE={}>".format(aWeb['target'])
   print "<INPUT TYPE=HIDDEN NAME=arg VALUE={}>".format(aWeb['arg'])
  else:
   print "<DIV CLASS=tr><DIV CLASS=td>VM:</DIV><DIV  CLASS=td><INPUT NAME=vm  TYPE=CHECKBOX VALUE=1  {0} ></DIV></DIV>".format("checked" if aWeb['target'] == 'vm' else '')
  print "</DIV></DIV>"
  print "</FORM><DIV CLASS=controls>"
  print aWeb.button('start', DIV='device_span', URL='sdcp.cgi?call=device_new&op=new',  FRM='device_new_form', TITLE='Create')
  print aWeb.button('search',DIV='device_ip',   URL='sdcp.cgi?call=device_new&op=find', FRM='device_new_form', TITLE='Find IP',INPUT='True')
  print "</DIV><SPAN CLASS='results' ID=device_span STYLE='max-width:400px;'></SPAN>"
  print "</ARTICLE>"

#
#
def delete(aWeb):
 res = aWeb.rest_call("device_delete",{ 'id':aWeb['id'] })
 print "<ARTICLE>Unit {} deleted, op:{}</ARTICLE>".format(aWeb['id'],res)

#
# find devices operations
#
def discover(aWeb):
 if aWeb['op']:
  res = aWeb.rest_generic(aWeb._rest_url,"device_discover",{ 'subnet_id':aWeb['ipam_subnet'], 'a_dom_id':aWeb['a_dom_id']}, aTimeout = 200)
  print "<ARTICLE>%s</ARTICLE>"%(res)
 else:
  subnets = aWeb.rest_call("ipam_list")['subnets']
  domains = aWeb.rest_call("dns_list_domains_cache",{'filter':'forward'})['domains']
  dom_name = aWeb['domain']
  print "<ARTICLE CLASS=info><P>Device Discovery</P>"
  print "<FORM ID=device_discover_form>"
  print "<INPUT TYPE=HIDDEN NAME=op VALUE=json>"
  print "<DIV CLASS=table><DIV CLASS=tbody>"
  print "<DIV CLASS=tr><DIV CLASS=td>Domain:</DIV><DIV CLASS=td><SELECT NAME=a_dom_id>"
  for d in domains:
   extra = "" if not dom_name == d.get('name') else "selected=selected"
   print "<OPTION VALUE=%s %s>%s</OPTION>"%(d.get('id'),extra,d.get('name'))
  print "</SELECT></DIV></DIV>"
  print "<DIV CLASS=tr><DIV CLASS=td>Subnet:</DIV><DIV CLASS=td><SELECT NAME=ipam_subnet>"
  for s in subnets:
   print "<OPTION VALUE=%s>%s (%s)</OPTION>"%(s['id'],s['subasc'],s['description'])
  print "</SELECT></DIV></DIV>"
  print "</DIV></DIV>"
  print "</FORM><DIV CLASS=controls>"
  print aWeb.button('start', DIV='div_content_right', SPIN='true', URL='sdcp.cgi?call=device_discover', FRM='device_discover_form')
  print "</DIV></ARTICLE>"

#
# clear db
#
def clear_db(aWeb):
 res = aWeb.rest_call("device_clear")
 print "<<ARTICLE>%s</ARTICLE>"%(res)

#
# Generate output for munin, until we have other types
#
def graph_save(aWeb):
 res = aWeb.rest_call("device_graph_save")
 print "<ARTICLE>Done updating devices' graphing (%s)</ARTICLE>"%(res)

#
#
def graph_info(aWeb):
 dev = aWeb.rest_call("device_graph_info",{'id':aWeb['id'],'graph_proxy':aWeb['graph_proxy'],'graph_update':aWeb['graph_update'],'op':aWeb['op']})

 print "<ARTICLE CLASS='info'><P>Graph for %s</DIV>"%(dev['fqdn'])
 print "<FORM ID=device_graph_form>"
 print "<INPUT TYPE=HIDDEN NAME=id VALUE='%s'>"%(aWeb['id'])
 print "<DIV CLASS=table STYLE='width:auto'><DIV CLASS=tbody>"
 print "<DIV CLASS=tr><DIV CLASS=td>Proxy:</DIV><DIV CLASS=td><INPUT  TYPE=TEXT NAME=graph_proxy STYLE='width:200px;' VALUE='%s'></DIV></DIV>"%(dev['graph_proxy'])
 print "<DIV CLASS=tr><DIV CLASS=td>Enable:</DIV><DIV CLASS=td><INPUT TYPE=CHECKBOX NAME=graph_update VALUE=1 %s></DIV></DIV>"%("checked=checked" if dev['graph_update'] == 1 else "")
 print "</DIV></DIV>"
 print "<SPAN>%s</SPAN>"%(dev.get('op'))
 print "</FORM><DIV CLASS=controls>"
 print aWeb.button('save',  DIV='div_content_right', URL='sdcp.cgi?call=device_graph_info&id=%s&op=update', FRM='device_graph_form')
 print aWeb.button('search',DIV='div_content_right', URL='sdcp.cgi?call=device_graph_info&id=%s&op=detect', FRM='device_graph_form')
 print "</DIV></ARTICLE>"
