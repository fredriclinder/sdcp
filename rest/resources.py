"""Module docstring.

Resources REST module

"""
__author__ = "Zacharias El Banna"
__version__ = "17.11.01GA"
__status__ = "Production"

def list(aDict):
 from sdcp.core.dbase import DB
 ret = {'res':'OK'}
 ret['user_id'] = aDict.get('user_id',"0")
 ret['view'] = aDict.get('view',"0")
 ret['type'] = aDict.get('type')
 select = "%s(user_id = %s %s)"%("type = '%s' AND "%ret['type'] if ret['type'] else "", ret['user_id'],"" if ret['view'] == '0' else 'OR private = 0')
 with DB() as db:
  ret['xist'] = db.do("SELECT id, icon, title, href, type, inline, user_id FROM resources WHERE %s ORDER BY type,title"%select)
  ret['data'] = db.get_rows()
 return ret