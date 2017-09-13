import json

dic={}
dic['recent_page'] = 10;
dic['has'] = {'author':[], "title":[], "content":[]}
dic['not'] = {'author':[], "title":[], "content":[]}
dic['comment'] = {"content":[]}
dic['pushcount'] = -9999
print json.dumps(dic)
