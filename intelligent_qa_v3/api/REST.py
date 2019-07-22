from flask import Flask,Response
from flask_restful import reqparse, abort, Api, Resource
from qa import InvertedIndex
from kwass import InvertedIndex_kw
import threading
import time
from tornado import wsgi
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import logging
import json
import fcntl
from datetime import datetime
from options.options import Options
import redis
from multiprocessing import Lock

def load_modellog():
    global iia,iib,ia,ib,modelflag
    while True:
        try:
            con = open("../log/flag.txt",'r')
            fcntl.flock(con,fcntl.LOCK_EX)
            str = con.readlines()
            fcntl.flock(con, fcntl.LOCK_UN)
        except Exception as e:
            logging.error(e)
            continue
        time.sleep(5)
        if modelflag != str[0][-1]:
            if 'modelA' in str:
                iia = InvertedIndex('modelA')
                ia =InvertedIndex_kw('modelA')
                muxlock.acquire()
                modelflag='A'
                muxlock.release()
                logging.warning('create modelA succeed!')
            elif 'modelB' in str:
                iib = InvertedIndex('modelB')
                ib =InvertedIndex_kw('modelB')
                muxlock.acquire()
                modelflag='B'
                muxlock.release()
                logging.warning('create modelB succeed!')
            else:
                pass
        con.close()


muxlock = threading.Lock()
iia = InvertedIndex()
iib = InvertedIndex()
ia =InvertedIndex_kw()
ib =InvertedIndex_kw()
modelflag='C'

app = Flask(__name__)
api = Api(app)

pool = redis.ConnectionPool(host='localhost', port=6379, db=1, decode_responses=True)
red = redis.Redis(connection_pool=pool)

class GetKeywordAssociation(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('question', type=str,required=True)
        self.parser.add_argument('emp_no', type=str)
        
    def gen_json(self, sim_list=[], flag=0):
        res = {}
        res['result'] = {}
        res['result']['IsOK'] = '1' if flag else '0'
        res['result']['Msg'] = r'request sucess' if flag else r'request failed'
        res['result']['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res['result']['similarity_question'] = sim_list
        return res
    
    def get(self):
        args = self.parser.parse_args()
        try:
            question=args.get('question')
            #print(question)
            question_id=question.replace('/','')
        except Exception as e:
            logging.error('get failed:{}'.format(e))
            return self.gen_json()
        text = ''
        if modelflag == 'A':
            text = ia.get_answer(question_id)
        elif modelflag == 'B':
            text = ib.get_answer(question_id)

        #redthread = threading.Thread(target=self.answer2red, args=(question_id,text, emp_no))
        #redthread.start()

        return Response(text, mimetype='text/plain')


#   show a single question item
class GetSimilarityQuestion(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('question', type=str,required=True)
        self.parser.add_argument('emp_no', type=str)
    
    def gen_json(self,hit_type=4, ques='', answer='', sim_list=[], flag=0):
        res = {}
        res['result'] = {}
        res['result']['IsOK'] = '1' if flag else '0'
        res['result']['Msg'] = r'request sucess' if flag else r'request failed'
        res['result']['hit_type']  = str(hit_type)
        res['result']['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res['result']['hit_question'] = ques
        res['result']['similarity_question'] = sim_list
        res['result']['answer'] = answer
        return res
    
    def get(self):
        args = self.parser.parse_args()
        try:
            question=args.get('question')
            question_id=question.replace('/','')
            emp_no=args.get('emp_no')
        except Exception as e:
            logging.error('get failed:{}'.format(e))
            return self.gen_json()
        text = ''
        if modelflag == 'A':
            text = iia.get_answer(question_id)
        elif modelflag == 'B':
            text = iib.get_answer(question_id)

        redthread = threading.Thread(target=self.answer2red, args=(question_id,text, emp_no))
        redthread.start()

        return Response(text, mimetype='text/plain')

    def answer2red(self,question_id,text, emp_no):
        answerdic = json.loads(text)
        resultdic = answerdic['result']
        lock = Lock()
        lock.acquire()
        redlist=[]
        try:
            if emp_no != None:
                redlist.append(emp_no)
            else:
                redlist.append('0000000')
            redlist.append(resultdic['time'])
            redlist.append(resultdic['hit_type'])

            if '1' == resultdic['hit_type']:
                question2red=question_id+'&&'
                redlist.append(question2red+resultdic['hit_question'])
                redlist.append('1')
            elif '2' == resultdic['hit_type']:
                question2red = question_id+'&&'
                score2red = ''
                for item in resultdic['similarity_question']:
                    question2red = question2red + item['hit_question']
                    question2red = question2red + '&'
                    score2red = score2red + item['score']
                    score2red = score2red + '&'
                redlist.append(question2red[:-1])
                redlist.append(score2red[:-1])
            else:
                redlist.append(question_id)
                redlist.append('0')
                
            redstr='||'.join(str(i) for i in redlist)
            red.rpush('questionlist',redstr)
        except Exception as e:
            logging.error(e)
        lock.release()
api.add_resource(GetSimilarityQuestion, '/xiaoai')
api.add_resource(GetKeywordAssociation,'/xiaoaikw')
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s [%(filename)s] %(levelname)s:%(message)s',
                    filename='../log/REST.log',
                    filemode='a')
logging.getLogger("requests").setLevel(logging.INFO)


if __name__ == '__main__':
    opt = Options().parse()
    portID=opt.portID
    t=threading.Thread(target=load_modellog,args=())
    t.start()
    http_server = HTTPServer(wsgi.WSGIContainer(app))
    try:
        http_server.listen(portID)
        logging.warning('{} start succeed'.format(portID))
        IOLoop.instance().start()
    except Exception as e:
        logging.error('{} start failed:{}'.format(portID,e))


