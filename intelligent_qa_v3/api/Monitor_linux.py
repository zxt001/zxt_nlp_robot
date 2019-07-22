import os
import sys
import time
from client import Client
from options.monitorconfig import server_portID

def isnginxalive():
    result=os.popen("ps -ef|grep nginx").read()
    if 'master process' in result:
        return True
    else:
        return False
        
def isRESTrunning():
    restpro =os.popen("ps -ef|grep REST").read()
    if 'python REST'in restpro:
        return True
    else:   
        return False
        
def killallREST():
    restpro =os.popen("ps -ef|grep REST").read()
    restlist=restpro.split('\n')
    for reststr in restlist:
        if ('python REST')in reststr:
            reststrs=reststr.split()
            try:
                os.popen('kill -9 '+reststrs[1])
            except Exception as e:
                logging.error('kill'+reststrs[1]+'failed:{}'.format(e))
                continue

if __name__=='__main__':
    monitor_client=Client()
    monitor_client.connect() 

    while isRESTrunning():
        killallREST()

    while True:
        while isnginxalive()==False:
            os.popen('/usr/local/nginx/sbin/nginx')
            time.sleep(1)

        for ID in server_portID:
            out =os.popen("ps -ef|grep portID="+ID).read()
            if ('python REST.py --portID='+ID)not in out:
                os.popen("python REST.py --portID="+ID)
                time.sleep(1)
        try:
            text = monitor_client.send_data('request connection')
        except Exception as e:
            logging.error(e)
        time.sleep(1)

