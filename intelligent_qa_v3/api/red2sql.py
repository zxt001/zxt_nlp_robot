import sys
sys.path.append('..')
from options.MySQLconfig import mysql_config
import redis
import pymysql
import time
import logging

def connect_mysql():
    connect = pymysql.connect(
        host=mysql_config['host'],
        user=mysql_config['user'],
        passwd=mysql_config['passwd'],
        port= mysql_config['port'],
        db= mysql_config['db'],
        charset= mysql_config['charset']
    )
    cur = connect.cursor()
    return cur, connect

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s [%(filename)s] %(levelname)s:%(message)s',
                        filename='../log/redis.log',
                        filemode='a')
    pool = redis.ConnectionPool(host='localhost', port=6379, db=1, decode_responses=True)
    red = redis.Redis(connection_pool=pool)
    while True:
        length = red.llen("questionlist")
        if length > 10:
            cur, connect = connect_mysql()
            while red.exists('questionlist'):
                try:
                    str=red.lpop('questionlist')
                    sqldata=str.split('||')
                    score = red.lpop('score')
                    sql_insert = "INSERT INTO user_data_table(request_time,hit_type,hit_question,emp_no,score) VALUES('%s','%s','%s','%s','%s')" % (
                        sqldata[1], sqldata[2], sqldata[3], sqldata[0], sqldata[4])
                    cur.execute(sql_insert)
                except Exception as e:
                    logging.error(e)
            cur.close()
            connect.commit()
            connect.close()
        else:
            time.sleep(5)
