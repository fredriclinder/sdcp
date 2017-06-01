"""Module docstring.

Ajax Openstack calls module

"""
__author__= "Zacharias El Banna"
__version__ = "17.6.1GA"
__status__= "Production"


############################### Openstack #############################
#
# Assume we've created a token from the pane, so auth is done and we should pick up cookie template .. now username is the final thing .. before proper cookies in web reader
#
from sdcp.devices.openstack import OpenstackRPC
import sdcp.SettingsContainer as SC

def _print_info(aName,aData):
 print "<H2>{}</H2>".format(aName)
 print "<TABLE style='width:99%'>"
 print "<THEAD><TH>Field</TH><TH>Data</TH></THEAD>"
 for key,value in aData.iteritems():
  if not isinstance(value,dict):
   print "<TR><TD>{}</TD><TD style='white-space:normal; overflow:auto;'>{}</TD></TR>".format(key,value)
  else:
   print "<TR><TD>{}</TD><TD style='white-space:normal; overflow:auto;'><TABLE style='width:100%'>".format(key)
   for k,v in value.iteritems():
    print "<TR><TD>{}</TD><TD>{}</TD>".format(k,v)
   print "</TABLE></TD></TR>"
 print "</TABLE>"

##################################### Heatstack ##################################
#
def heat_list(aWeb):
 project = aWeb.get_value('project')
 (pid,pname) = project.split('_')
 controller  = OpenstackRPC("127.0.0.1")
 if not controller.load(SC.openstack_cookietemplate.format(pname)):
  print "Not logged in"
  return
 port,lnk,svc = controller.get_service('heat','public')
 ret = controller.call(port,lnk + "/stacks") 
 print "<DIV CLASS='z-table' style='width:394px'><TABLE style='width:99%'>"
 print "<THEAD style='height:20px'><TH COLSPAN=3><CENTER>Heat Stacks</CENTER></TH></THEAD>"
 print "<TR style='height:20px'><TD COLSPAN=3>"
 print "<A TITLE='Reload List' CLASS='z-btn z-small-btn z-op' OP=load DIV=div_navleft LNK='ajax.cgi?call=openstack_heat_list&project={}'><IMG SRC='images/btn-reboot.png'></A>".format(project)
 print "<A TITLE='Add service' CLASS='z-btn z-small-btn z-op' OP=load DIV=div_navcont LNK='ajax.cgi?call=openstack_heat_choose_template&project={}'><IMG SRC='images/btn-add.png'></A>".format(project)
 print "</TR>"
 print "<THEAD><TH>Name</TH><TH>Status</TH><TH>Operations</TH></THEAD>"
 for stack in ret['data'].get('stacks',None):
  tmpl = "<A TITLE='{}' CLASS='z-btn z-op z-small-btn' DIV=div_navcont LNK=ajax.cgi?call=openstack_heat_action&project=" + project + "&name=" + stack['stack_name'] + "&id=" + stack['id'] + "&op={} OP=load SPIN=true>{}</A>"
  print "<TR>"
  print "<TD>{}</TD>".format(stack['stack_name'])
  print "<TD>{}</TD>".format(stack['stack_status'])
  print "<TD>"
  print tmpl.format('Stack info','info','<IMG SRC=images/btn-info.png>')
  if stack['stack_status'] == "CREATE_COMPLETE" or stack['stack_status'] == "CREATE_FAILED":
   print tmpl.format('Remove stack','remove','<IMG SRC=images/btn-remove.png>')
  print "</TD>"
  print "</TR>"
 print "</TABLE>"
 print "</DIV>"

######################### HEAT ADD ######################
#
# Add instantiation
#
def heat_choose_template(aWeb):
 project = aWeb.get_value('project')
 print "<DIV CLASS='z-table' style='display:inline-block; padding:6px'>"
 print "<FORM ID=frm_heat_choose_template>"
 print "<INPUT TYPE=hidden NAME=project VALUE={}>".format(project)
 try:
  print "Add solution from template:<SELECT NAME=template style='height:22px;'>"
  from os import listdir
  for file in listdir("os_templates/"):
   name = file.partition('.')[0]
   print "<OPTION VALUE={}>{}</OPTION>".format(file,name)
  print "</SELECT>"
 except Exception as err:
  print "openstack_choose_template: error finding template files in 'os_templates/' [{}]".format(str(err))
 print "</FORM>"
 print "<A TITLE='Enter parameters' CLASS='z-btn z-small-btn z-op' OP=post FRM=frm_heat_choose_template DIV=div_os_info LNK='ajax.cgi?call=openstack_heat_enter_parameters'><IMG SRC='images/btn-document.png'></A>"
 print "<A TITLE='View template'    CLASS='z-btn z-small-btn z-op' OP=post FRM=frm_heat_choose_template DIV=div_os_info LNK='ajax.cgi?call=openstack_heat_action&op=templateview'><IMG SRC='images/btn-info.png'></A>"
 print "</DIV>"
 print "<DIV ID=div_os_info></DIV>"

def heat_enter_parameters(aWeb):
 from json import load,dumps
 project  = aWeb.get_value('project')
 template = aWeb.get_value('template')
 with open("os_templates/"+template) as f:
  data = load(f)
 print "<DIV CLASS='z-table' style='display:inline-block; padding:6px'>"
 print "<FORM ID=frm_heat_template_parameters>"
 print "<INPUT TYPE=hidden NAME=project VALUE={}>".format(project)
 print "<INPUT TYPE=hidden NAME=template VALUE={}>".format(template)
 print "<TABLE>"
 print "<THEAD><TH>Parameter</TH><TH style='min-width:300px'>Value</TH></THEAD>"
 print "<TR><TD><B>Unique Name</B></TD><TD><INPUT CLASS='z-input' TYPE=text NAME=name PLACEHOLDER='change-this-name'></TD></TR>"
 for key,value in data['parameters'].iteritems():
  print "<TR><TD>{0}</TD><TD><INPUT CLASS='z-input' TYPE=TEXT NAME=param_{0} PLACEHOLDER={1}></TD></TR>".format(key,value)
 print "</TABLE>"
 print "</FORM>"
 print "<A TITLE='Create' CLASS='z-btn z-small-btn z-op' style='float:right;' OP=post SPIN=true FRM=frm_heat_template_parameters DIV=div_navcont LNK='ajax.cgi?call=openstack_heat_action&op=create2'><IMG SRC='images/btn-start.png'></A>"
 print "</DIV>"

#
# Heat Actions
#
def heat_action(aWeb):
 project = aWeb.get_value('project')
 (pid,pname) = project.split('_')
 name = aWeb.get_value('name')
 id   = aWeb.get_value('id')
 op   = aWeb.get_value('op','info')
 controller = OpenstackRPC("127.0.0.1")
 if not controller.load(SC.openstack_cookietemplate.format(pname)):
  print "Not logged in"
  return
 aWeb.log_msg("openstack_heat_action - id:{} name:{} op:{} for project:{}".format(id,name,op,project))
 port,lnk,svc = controller.get_service('heat','public')

 if   op == 'info':
  tmpl = "<A TITLE='{}' CLASS='z-btn z-op' DIV=div_os_info LNK=ajax.cgi?call=openstack_heat_action&project=" + project + "&name=" + name + "&id=" + id+ "&op={} OP=load SPIN=true>{}</A>"
  print "<DIV>"
  print tmpl.format('Stack Details','details','Details')
  print tmpl.format('Stack Parameters','events','Events')
  print tmpl.format('Stack Template','template','Template')
  print tmpl.format('Stack Parameters','parameters','Parameters')
  print "</DIV>"
  print "<DIV CLASS='z-table' style='overflow:auto' ID=div_os_info>"
  ret = controller.call(port,lnk + "/stacks/{}/{}".format(name,id))
  _print_info(name,ret['data']['stack'])
  print "</DIV>"

 elif op == 'events':
  from json import dumps
  ret = controller.call(port,lnk + "/stacks/{}/{}/events".format(name,id))
  print "<TABLE>"
  for event in ret['data']['events']:
   print "<TR><TD>{}</TD><TD>{}</TD><TD>{}</TD><TD>{}</TD></TR>".format(event['resource_name'],event['logical_resource_id'],event['resource_status'],event['resource_status_reason'])
  print "</TABLE>"

 elif op == 'details':
  ret = controller.call(port,lnk + "/stacks/{}/{}".format(name,id))
  _print_info(name,ret['data']['stack'])

 elif op == 'remove':
  ret = controller.call(port,lnk + "/stacks/{}/{}".format(name,id), method='DELETE')
  print "<DIV CLASS='z-table'>"
  print "<H3>Removing {}</H3>".format(name)
  if ret['code'] == 204:
   print "Stack removed"
  else:
   print "Error code: {}".format(ret['code'])
  print "</DIV>"

 elif op == 'template':
  from json import dumps
  ret = controller.call(port,lnk + "/stacks/{}/{}/template".format(name,id))
  print "<PRE>" + dumps(ret['data'], indent=4) + "</PRE>"

 elif op == 'parameters':
  from json import dumps
  ret = controller.call(port,lnk + "/stacks/{}/{}".format(name,id))
  data = ret['data']['stack']['parameters']
  data.pop('OS::project_id')
  data.pop('OS::stack_name')
  data.pop('OS::stack_id')
  print "<PRE>" + dumps(data, indent=4) + "</PRE>"

 elif op == 'create':
  template = aWeb.get_value('template')
  if name and template:
   from json import load,dumps
   with open("os_templates/"+template) as f:
    data = load(f)
   data['stack_name'] = name
   params  = aWeb.get_args2dict_except(['op','call','template','project','name'])
   for key,value in params.iteritems():
    data['parameters'][key[6:]] = value
   ret = controller.call(port,lnk + "/stacks",arg=data)
   if ret['code'] == 201:
    print "<DIV CLASS='z-table'>"
    print "<H2>Successful instantiation of '{}' solution</H2>".format(template.partition('.')[0])
    print "Name: {}<BR>Id:{}".format(name,ret['data']['stack']['id'])
    print "</DIV>"
   else:
    print "<PRE>Error instantiating stack:" + str(ret) + "</PRE>"
  else:
   print "Error - need to provide a name for the instantiation"

 if op == 'templateview':
  template = aWeb.get_value('template')
  from json import load,dumps
  with open("os_templates/"+template) as f:
   data = load(f)
  data['stack_name'] = name if name else "Need_to_specify_name"
  print "<DIV CLASS='z-table'><PRE>"
  print dumps(data, indent=4, sort_keys=True)
  print "</PRE></DIV>"

############################### Contrail ##############################
#
def contrail_list(aWeb):
 (pid,pname) = aWeb.get_value('project').split('_')
 controller = OpenstackRPC("127.0.0.1")
 if not controller.load(SC.openstack_cookietemplate.format(pname)):
  print "Not logged in"
  return
 ret = controller.call("8082","virtual-networks")
 # print ret
 print "<DIV CLASS='z-table' style='width:394px'><TABLE style='width:99%'>"
 print "<THEAD style='height:20px'><TH COLSPAN=3><CENTER>Contrail VNs</CENTER></TH></THEAD>"
 print "<THEAD><TH>Owner</TH><TH>Network</TH></THEAD>"
 for net in ret['data']['virtual-networks']:
  # net['uuid']
  if net['fq_name'][1] == pname:
   print "<TR><TD>{}</TD><TD>{}</TD></TR>".format(pname,net['fq_name'][2])
 print "</TABLE>"
 print "</DIV>"

################################# Nova ###############################
#
def nova_list(aWeb):
 project = aWeb.get_value('project')
 (pid,pname) = project.split('_')
 controller  = OpenstackRPC("127.0.0.1")
 if not controller.load(SC.openstack_cookietemplate.format(pname)):
  print "Not logged in"
  return
 port,lnk,svc = controller.get_service('nova','public')
 ret = controller.call(port,lnk + "/servers")
 print "<DIV CLASS='z-table' style='width:394px'><TABLE style='width:99%'>"
 print "<THEAD style='height:20px'><TH COLSPAN=3><CENTER>Nova Servers</CENTER></TH></THEAD>"
 print "<TR style='height:20px'><TD COLSPAN=3>"
 print "<A TITLE='Reload List' CLASS='z-btn z-small-btn z-op' OP=load DIV=div_navleft LNK='ajax.cgi?call=openstack_nova_list&project={}'><IMG SRC='images/btn-reboot.png'></A>".format(project)
 print "</TR>"
 print "<THEAD><TH>Name</TH><TH style='width:94px;'>Operations</TH></THEAD>"
 for server in ret['data'].get('servers',None):
  print "<TR>"
  print "<TD>{}</TD>".format(server['name'])
  print "<TD>"
  print "<A TITLE='VM info'   CLASS='z-btn z-op z-small-btn' DIV=div_navcont LNK=ajax.cgi?call=openstack_nova_action&project={0}&name={1}&id={2}&op=info   OP=load SPIN=true><IMG SRC='images/btn-info.png'></A>".format(project,server['name'],server['id'])
  print "<A TITLE='Remove VM' CLASS='z-btn z-op z-small-btn' DIV=div_navcont LNK=ajax.cgi?call=openstack_nova_action&project={0}&name={1}&id={2}&op=remove OP=load SPIN=true><IMG SRC='images/btn-remove.png'></A>".format(project,server['name'],server['id'])
  print "</TD>"
  print "</TR>"
 print "</TABLE>"
 print "</DIV>"

#
# Actions
# 
def nova_action(aWeb):
 project = aWeb.get_value('project')
 name = aWeb.get_value('name')
 id   = aWeb.get_value('id')
 op   = aWeb.get_value('op','info')
 (pid,pname) = project.split('_')
 controller = OpenstackRPC("127.0.0.1")
 if not controller.load(SC.openstack_cookietemplate.format(pname)):
  print "Not logged in"
  return
 aWeb.log_msg("openstack_nova_action - id:{} name:{} op:{} for project:{}".format(id,name,op,project))
 port,lnk,svc = controller.get_service('nova','public')

 if   op == 'info':
  ret = controller.call(port,lnk + "/servers/{}".format(id))
  print "<DIV CLASS='z-table' style='overflow:auto' ID=div_os_info>"
  _print_info(name,ret['data']['server'])
  print "</DIV>"
 elif op == 'remove':
  ret = controller.call(port,lnk + "/servers/{}".format(id), method='DELETE')
  print "<DIV CLASS='z-table'>"
  print "<H2>Removing {}</H2>".format(name)
  if ret['code'] == 204:
   print "Server removed"
  else:
   print "Error code: {}".format(ret['code'])
  print "</DIV>"