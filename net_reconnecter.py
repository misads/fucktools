import misc_utils as utils
import time
from icecream import ic
import os

delay = 60
hostname = 'mypc'  # 修改为你的设备名称
ip_start = '172.20'  # ip会包含这个，以防获取到虚假的ip

def getip():
    ipstr = utils.cmd(f'ifconfig | grep {ip_start}')
    if not len(ipstr):
        return None
    ipstr = ipstr[0].split(' ')
    ipstr = list(filter(lambda x: ip_start in x , ipstr))[0]
    #print(ipstr)
    return ipstr

def unconnect(wait=5):
    command = 'sudo poff -a'
    print(command)
    os.system(command)
    time.sleep(wait)

def connect(wait=0):
    command = 'sudo pon dsl-provider'
    print(command)
    os.system(command)
    time.sleep(wait)

def isconnected():
    responses = utils.cmd('ping xyu.ink -c 1')
    for response in responses:
        if 'ttl' in response:
            return True
    return False

update = True
while True:
    for i in range(delay):
        time.sleep(1)
        utils.progress_bar(i, delay, 'Waiting...')

    ip = getip()
    if not isconnected():
        status = 'disconnected.'
        ic(status)
        unconnect()
        unconnect()
        connect()
        update = True

    else:
        if update:
            url = f'http://xyu.ink:8002/put?key={hostname}&value={ip}'
            command = f'wget "{url}" --output-document=/dev/null'
            os.system(command)
        ic(ip)
        update = False