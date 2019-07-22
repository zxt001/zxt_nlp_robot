# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
import pymysql
# from options.MySQLconfig import mysql_config
# from langconv import *




sql_que = 'SELECT question,solution_id,queLevel,id FROM question WHERE del=0 and solution_id in (select solution_id from solution where now_status=0 and del=0)'
sql_ans = 'SELECT answer,solution_id FROM answer WHERE del=0 and solution_id in (select solution_id from solution where now_status=0 and del=0)'
sql_cla = 'SELECT que.solution_id FROM question AS que,solution AS sol,classes AS cla WHERE que.del=0 AND sol.del=0 AND sol.now_status=0 AND que.solution_id=sol.solution_id AND sol.group_id=cla.id AND cla.id=2595'

def connect_mysql():
    connect = pymysql.connect(
        host='10.195.226.246',
        user='bigdata_xiaoaiapi',
        passwd='xiaoaiapi_bigdata',
        port=3306,
        db='ics_r1',
        charset='utf8mb4'
    )
    cur = connect.cursor()
    return cur,connect
def select_data(sql, flag=0):
    dic = {}
    cur,connect = connect_mysql()
    cur.execute(sql)
    alldata = cur.fetchall()
    if 0 == flag:
        for record in alldata:
            dic[record[-1]] = {'quelevel': record[2], 'solution_d': record[1], 'question': record[0]}# Converter('zh-hans').convert(record[0])}
    else:
        for record in alldata:
            dic[record[-1]] = {'answer': record[0] }#Converter('zh-hans').convert(record[0])}
    connect.close()
    
    return dic

def dic_merge():
    dic_relationship = {}
    que_list = []
    merge = {}
    que_dic = select_data(sql_que)
    tmp_dic = {}
    for idx, ques_id in enumerate(que_dic.keys()):
        que_list.append(que_dic[ques_id]['question'])
        dic_relationship[idx] = que_dic[ques_id]['solution_d']
        if 1 == que_dic[ques_id]['quelevel']:
            tmp_dic[que_dic[ques_id]['solution_d']] = que_dic[ques_id]['question']
    ans_dic = select_data(sql_ans, 1)
    for k1 in tmp_dic.keys():
        merge[k1] = ans_dic[k1]['answer'] + '____' + tmp_dic[k1]
    
    return merge, que_list, dic_relationship

def trigger_log():
    cur, connect = connect_mysql()
    sql_trigger = 'SELECT operation FROM aq_bigdata_info'
    cur.execute(sql_trigger)
    alldata = cur.fetchall()
    connect.close()
    return alldata
def trigger_delete():
    cur, connect = connect_mysql()
    sql_delect = 'DELETE FROM aq_bigdata_info'
    try:
        cur.execute(sql_delect)
        connect.commit()
    except:
        connect.rollback()
    connect.close()

def select_que_cla():
    cur, connect = connect_mysql()
    que_cla_list = []
    cur.execute(sql_cla)
    ques_claes = cur.fetchall()
    #print(ques_claes)
    for que_cla in ques_claes:
        que_cla_list.append(que_cla[0])

    connect.close()
    return que_cla_list


if __name__ == '__main__':
    pass
    # li = select_que_cla()
    # print(li)
    # pass
    # dic = {1:2,3:4}
    # if 1 in dic.keys():
    #     print("OK")




