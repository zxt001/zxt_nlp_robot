# -*- coding:utf-8 -*-
import socket
import sys
import threading
import time
import threadpool
import logging
import os
from options.monitorconfig import socket_config,server_portID
 
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s %(filename)s %(levelname)s: %(message)s',
                   filename='../log/server.log',
                   filemode='a')
 
class Server():
    def __init__(self):
        self.ip = socket_config['ip']
        self.port=socket_config['port']
        self.addr = (self.ip, self.port)
        self.byte = socket_config['byte']
     
    def createserver(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.addr)
        logging.info('create server success')
    
    def setsocktimeout(self,time):
        self.sock.settimeout(time)

    def recv_data(self):
        try:
            (recvdata, clientaddr) = self.sock.recvfrom(self.byte)
            recvtext = recvdata.decode('utf-8')
        except ConnectionError:
            logging.error('connect error')
            return ('connect error'),0
        except socket.timeout as e:
            logging.error('error:time out')
            return ("error:time out"),0
            
        return recvtext,clientaddr
        

    def send_data(self,recvdata,clientaddr):
            try:
                data = recvdata.encode('utf-8')
                self.sock.sendto(data, clientaddr)
            except ConnectionError:
                logging.error('connect error')
                return ('connect error')
            except:
                logging.error('unexpect error')
                return ('unexpect error')
            return 'send data succeed!'

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
            print(reststrs[1])
            try:
                os.popen('kill -9 '+reststrs[1])
            except:
                logging.error('kill'+reststrs[1]+'failed')
                continue

def isnginxalive():
    result=os.popen("ps -ef|grep nginx").read()
    if 'master process' in result:
        return True
    else:
        return False


                
if __name__=='__main__':
    server1=Server()
    server1.createserver()
    waitforconn=True
    while waitforconn:
        recvdata, clientaddr = server1.recv_data()
        if recvdata =='request connection':
            server1.send_data(recvdata, clientaddr)
            waitforconn=False
            logging.info('connection succeed')
    time.sleep(30)
    server1.setsocktimeout(socket_config['timeout'])
    while True:
        recvdata=''
        recvdata,clientaddr=server1.recv_data()
        if clientaddr!=0:
            server1.send_data(recvdata,clientaddr)
        while isnginxalive()==False:
                os.popen('/usr/local/nginx/sbin/nginx')
                time.sleep(1)
        for ID in server_portID:
            out =os.popen("ps -ef|grep portID="+ID).read()
            if ('python REST.py --portID='+ID)not in out:
                os.popen("python REST.py --portID="+ID)
                time.sleep(1)
        
        
        
        







    
    