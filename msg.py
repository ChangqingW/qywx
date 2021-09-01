import json
import sys
import subprocess
import requests
from time import sleep
import os

def token_update():
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'secrets.json')
    print('Updating token...', end='')
    with open(json_path) as f:
        d = json.load(f)
    required_params = ('corpid', 'corpsecret')
    r = requests.get(url, params = { k:d[k] for k in required_params })
    while not r:
        print('error\nretrying again...', end='')
        sleep(3)
        r = requests.get(url, params = { k:d[k] for k in required_params })
    print('success!\n')
    token = json.loads(r.text)['access_token']
    d.update({'access_token': token})
    with open(json_path, 'w') as f:
        json.dump(d,f)
    return None

def json_read():
    json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'secrets.json')
    with open(json_path) as f:
        d = json.load(f)
    return d

def wx_upload(file, filetype=None):

    #File type
    extensions = {'image': ['.png', 'jpg'],
                  'video': ['.mp4', '.mkv', '.avi']}
    if filetype == None:
        for k,v in extensions.items():
            for i in v:
                if i in file:
                    filetype = k
    if filetype == None:
        filetype = 'file'
    filetype = '&type=' + filetype

    token = json_read()['access_token']

    api = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token='
    url = api + token + filetype

    command = subprocess.run(['curl', '-F', 'media=@'+file, url], stdout=subprocess.PIPE)
    print()
    result=json.loads(command.stdout.decode('utf-8'))
    if result['errmsg'] == 'ok':
        return result
    while result['errmsg'] != 'ok':
        print('while uploading file, api returned '+result['errmsg']+'\nRetrying...\n')
        sleep(3)
        token_update()
        token = json_read()['access_token']
        url = api + token + filetype
        command = subprocess.run(['curl', '-F', 'media=@'+file, url], stdout=subprocess.PIPE)
        print()
        result=json.loads(command.stdout.decode('utf-8'))
    return result

def wx_send_file(upload_result):
    print(upload_result, end='\n\n')
    url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'

    d = json_read()
    token = {'access_token': d['access_token']}

    data = {
        "toparty" : "1" ,
        "msgtype" : upload_result["type"],
        "agentid" : d["agentid"],
        # video
        #"title" : "Title",
        upload_result['type'] : {
        "media_id" : upload_result['media_id']}}
    r = requests.post(url, json=data, params=token)
    result=json.loads(r.text)
    print(r.text, end='\n\n')
    while (not r):
        sleep(3)
        token_update()
        token['access_token'] = json_read()['access_token']
        r = requests.post(url, json=data, params=token)
        result=json.loads(r.text) 
    return None

def wx_send_msg(msg):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'

    d = json_read()
    token = {'access_token': d['access_token']}

    data = {
        "toparty" : '1',
        "msgtype" : "text",
        "agentid" : d["agentid"],
        "text" : {
        "content" : msg}}
    r = requests.post(url, json=data, params=token)
    result=json.loads(r.text)
    print(r.text, end='\n\n')
    while (not r) or result['errmsg'] != 'ok':
        sleep(3)
        token_update()
        token['access_token'] = json_read()['access_token']
        r = requests.post(url, json=data, params=token)
        result=json.loads(r.text)
    return None

if __name__ == "__main__":
    assert len(sys.argv) > 1, 'no message provided'
    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            wx_send_file(wx_upload(sys.argv[1]))
        elif os.path.isfile(sys.argv[1].replace('\\','')):
            wx_send_file(wx_upload(sys.argv[1].replace('\\','')))
        else:
            wx_send_msg(sys.argv[1])
    else:
        wx_send_msg( ' '.join(sys.argv[1:]) )
