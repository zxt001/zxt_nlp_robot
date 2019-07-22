#coding=utf-8
import re
import os
import xlrd
import json
from datetime import datetime
from xlrd import xldate_as_tuple

class DealFile(object):
    def __init__(self):
        self.cols = {'userid':0, 'NAME':1, 'company':2, 'sex':3, 'addr':4, 'dep':5, 'job':6, 'mobile':7, 'rank':8, 'joindate':9, '使用日期':10, '使用時間':11, 'question':12, 'solutionId':13, 'bzquestion':14, 'NAME_2':15, 'reply':16, '是否滿意':17, '标准不滿意原因':18, '自定义不满意原因':19}

        pass

    def _get_content(self, path):
        info = {}
        workbook = xlrd.open_workbook(path)
        for name in workbook.sheet_names():
            booksheet = workbook.sheet_by_name(name)
            for row in range(2, booksheet.nrows):
                userid, sex, job, rank, question, bzquestion, reply = \
                    booksheet.cell(row, 0).value, booksheet.cell(row, 3).value, booksheet.cell(row, 6).value, booksheet.cell(row, 8).value, booksheet.cell(row, 12).value, booksheet.cell(row, 14).value, booksheet.cell(row, 16).value
                day_type, time_type = booksheet.cell(row, 10).ctype, booksheet.cell(row, 11).ctype
                if day_type == 3:
                    date = datetime(*(xldate_as_tuple(booksheet.cell(row, 10).value + booksheet.cell(row, 11).value, 0)))
                    # datetime(*(xldate_as_tuple(booksheet.cell(row, 10).value, 0)))

                    use_day = date.strftime('%Y/%m/%d %H:%M:%S')
                else:
                    use_day = booksheet.cell(row, 10).value

                # if time_type == 3:
                #     date = datetime(*(xldate_as_tuple(booksheet.cell(row, 11).value, 0)))
                #     use_time = date.strftime('%Y/%d/%m %H:%M:%S')
                # else:
                #     use_time = booksheet.cell(row, 10).value

                print(userid, sex, job, rank, use_day, question, bzquestion)
                if userid in info.keys():
                    count = info[userid].get('count', 0)
                    info[userid]['q&a'][count] = '{}:{}\n{}\n{}'.format(use_day, question, bzquestion, reply)
                    info[userid]['count'] = count + 1
                else:
                    info[userid] = {}
                    info[userid]['count'] = 1
                    info[userid]['sex'] = sex
                    info[userid]['job'] = job
                    info[userid]['rank'] = rank
                    info[userid]['q&a'] = {}
                    info[userid]['q&a'][0] = '{}:{}\n{}\n{}'.format(use_day, question, bzquestion, reply)
        return info

    def _get_content_qa(self, path_list):
        info = {}
        for path in path_list:
            workbook = xlrd.open_workbook(path)
            tmp = None
            for name in workbook.sheet_names():
                if name in [r'Sheet1', r'标准问题和多渠道答案']:
                    booksheet = workbook.sheet_by_name(name)
                else:
                    continue
                for row in range(2, booksheet.nrows):
                    if name == r'标准问题和多渠道答案':
                        standard_question = booksheet.cell(row, 3).value
                        standard_question = standard_question.replace('？', '')
                        undeal_reply = booksheet.cell(row, 4).value
                    else:
                        standard_question = booksheet.cell(row, 1).value
                        standard_question = standard_question.replace('？', '').replace('?', '')
                        undeal_reply = booksheet.cell(row, 2).value
                    pat = re.compile('<[^>]+>', re.S)
                    reply = pat.sub('', undeal_reply)
                    res = reply.replace('&quot;', '').replace('&nbsp;', '').replace('\r', '').replace('\n', '').replace('您好！', '')\
                        .replace('感谢您使用小爱，请您对“小爱”的回答进行评价吧！ 满意：请点“赞” 不满意：请点“踩”', '')\
                        .replace('感谢您使用小爱机器人，请您对“小爱”的回答进行评价吧！ 满意：请点“赞” 不满意：请点“踩”', '')\
                        .replace('请您对“小爱”的回答进行评价吧！满意：请点“赞”不满意：请点“踩”, 请您对“小爱”的回答进行评价吧！满意：请点“赞”不满意：请点“踩”', '')\
                        .replace('请您对“小爱”的回答进行评价吧！满意：请点“赞”不满意：请点“踩”', '')\
                        .replace('请您对“小爱”的回答进行评价吧！满意：请点“赞”不满意：请点“踩', '')
                    # if res == tmp:
                    #     continue
                    # tmp = res
                    if standard_question not in info.keys():
                        info[standard_question] = {}
                        info[standard_question]['stand_answer'] = res
                        info[standard_question]['orgin_answer'] = undeal_reply
                    else:
                        print(standard_question)#, info[standard_question])
                    # break
                    # print(row)
        return info

    def save_answer_with_question(self, path):
        qa_dict = self._get_content_qa(path)

        with open(r'E:\intelligent_q&a\ipeg_data\all.txt', 'w', encoding='utf-8') as fw_deal:
            for idx, key in enumerate(qa_dict.keys()):#, \
                    #open(r'E:\intelligent_q&a\data\origin\{}.txt'.format(idx), 'w', encoding='utf-8') as fw_origin, \
                        #open(r'E:\intelligent_q&a\data\question\{}.txt'.format(idx), 'w', encoding='utf-8') as fw_ques:
                    stand_answer = qa_dict[key]['stand_answer']
                    orgin_answer = qa_dict[key]['orgin_answer']
                    # fw_deal.write(stand_answer)
                    # fw_origin.write(orgin_answer)
                    # fw_ques.write(key)
                    fw_deal.write(':'.join([key, stand_answer]) + '\n')
                    pass


    def split_ques_answer(self, path, res_path):
        with open(path, r'r', encoding='utf-8') as fr, open(os.path.join(res_path, 'qes.txt'), r'w', encoding='utf-8') as fw:
            idx = 0
            for line in fr:
                qes = line.strip('\n').split(':')[0]
                answer = ':'.join(line.strip('\n').split(':')[1:])
                with open(os.path.join(res_path, r'question\{}.txt'.format(idx)), r'w', encoding='utf-8') as fw_ques, \
                        open(os.path.join(res_path, r'answer\{}.txt'.format(idx)), r'w', encoding='utf-8') as fw_answer:
                    fw_ques.write(qes)
                    fw_answer.write(answer)
                fw.write(qes+'\n')
                idx += 1

    def merge_question_answer(self, path):
        for file_name in os.listdir(os.path.join(path, 'question')):
            with open(os.path.join(path, 'question', file_name), r'r', encoding='utf-8') as fr_ques,\
                    open(os.path.join(path, r'answer', file_name), r'r', encoding='utf-8') as fr_answer,\
                    open(os.path.join(path, r'merge', file_name), r'w', encoding='utf-8') as fw_merge:
                ques = fr_ques.read()
                answer = fr_answer.read()
                fw_merge.write('____'.join([answer, ques]))


    def test(self, path):
        # info = self._get_content(path)
        # with open(r'E:\intelligent_q&a\data\chats.json', 'w', encoding='utf-8') as fw:
        #     json.dump(info, fw, ensure_ascii=False)

        with open(r'E:\intelligent_q&a\data\chats.json', 'r', encoding='utf-8') as fr:
            fileJson = json.load(fr)
            count = 0
            id = -1
            count_1 = 0
            for item in fileJson:
                if fileJson[item]['count'] > count:
                    count = fileJson[item]['count']
                    id = item

                if fileJson[item]['count'] > 20:
                    count_1 += 1
            print(count, count_1)
            dict = sorted(fileJson[id]['q&a'].items(), key=lambda d: int(d[0]), reverse=False)
            for item in dict:
                idx, cont = item
                info = cont.split('\n')
                print('{}\n{}'.format(info[0], info[2]))

def demo():
    # from selenium import webdriver
    # mobile_emulation = {'deviceName': 'iPhone X'}
    # options = webdriver.ChromeOptions()
    # options.add_experimental_option('mobileEmulation', mobile_emulation)
    # drivers = webdriver.Chrome(chrome_options=options)
    # drivers.maximize_window()
    # drivers.get("http://www.baidu.com")
    pass


if __name__ == '__main__':
    df = DealFile()
    # df.test(r'D:\Users\H2408627\Desktop\ZZ903-923聊天記錄.xlsx')
    res = df.save_answer_with_question([r'D:\WORK_FILE\小爱机器人\機器人知識點（全）\加工區知識點匯總.xlsx']) #r'D:\WORK_FILE\小爱机器人\知识点.xlsx'])#, r'D:\WORK_FILE\小爱机器人\機器人知識點（全）\加工區知識點匯總.xlsx'])
    # df.split_ques_answer(r'D:\WORK_FILE\小爱机器人\ipeg.txt', r'E:\intelligent_q&a\ipeg_data')
    # df.merge_question_answer(r'E:\intelligent_q&a\ipeg_data')