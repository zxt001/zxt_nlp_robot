# -*- coding:utf-8 -*-
import socket
import sys
import threading
import time
import logging
sys.path.append('../')
from options.monitorconfig import socket_config

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s: %(message)s',
                    filename='../log/client.log',
                    filemode='a')

class Client():
    def __init__(self):
        self.ip = socket_config['ip']
        self.port=socket_config['port']
        self.addr = (self.ip, self.port)
        self.byte = socket_config['byte']

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(socket_config['timeout'])
        logging.info('connection succeed')

    def send_data(self,data):
        try:
            text = data.encode('utf-8')
            self.sock.sendto(text, self.addr)
        except ConnectionError:
            logging.error('connect error')
            return ('connect error')
        except:
            logging.error('unexpect error')
            return ('unexpect error')

        try:
            data, addr =self.sock.recvfrom(self.byte)
            text = data.decode("utf-8")
            return text
        except socket.timeout as e:
            logging.error('connect error')
            return ('error:%s'%e)

                
                
                
                
                
