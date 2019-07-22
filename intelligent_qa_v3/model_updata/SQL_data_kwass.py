# -*- coding: utf-8 -*-

import pymysql
from options.MySQLconfig import mysql_config
from langconv import *


#sql_que = 'SELECT question,solution_id FROM question WHERE solution_id IN (SELECT solution_id FROM solution WHERE now_status=0) and del=0'

sql_que = "SELECT que.question,que.solution_id  FROM question AS que,solution AS sol,classes AS cla WHERE que.del=0 AND sol.del=0 AND sol.now_status=0 AND que.solution_id=sol.solution_id AND sol.group_id=cla.id AND cla.id!=2595"

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
    return cur,connect
def select_data(sql):
    result = []
    dic = {}
    cur,connect = connect_mysql()
    cur.execute(sql)
    alldata = cur.fetchall()
    #print(alldata)
    for rec in alldata:
        result.append(rec[:])
    for que in result:
        con_que=Converter('zh-hans').convert(que[0])
        dic[con_que]=que[-1]
    connect.close()
    return dic


def dic_merge():
    dic_relationship = {}
    que_list = []
    merge = {}
    que_dic = select_data(sql_que)
    return que_dic

def trigger_log():
    cur,connect = connect_mysql()
    sql_trigger = 'SELECT operation FROM aq_bigdata_info'
    cur.execute(sql_trigger)
    alldata = cur.fetchall()
    connect.close()
    return alldata
def trigger_delete():
    cur,connect = connect_mysql()
    sql_delect = 'DELETE FROM aq_bigdata_info'
    try:
        cur.execute(sql_delect)
        connect.commit()
    except:
        connect.rollback()
    connect.close()




