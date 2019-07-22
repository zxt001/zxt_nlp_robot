#coding=utf-8
import sys
sys.path.append('../')
sys.path.append('./')
import re
import os
import jieba
#import xlrd
import json
import math
from options.options import Options
import collections
from collections import defaultdict
from langconv import *
from functools import reduce
from datetime import datetime
from gensim import corpora, models, similarities
import collections
from api.classify_fasttext import QueClassifyFastText
from model_updata.SQL_data import select_que_cla

class InvertedIndex(object):
    def __init__(self,model='modelA'):
        self.qc = QueClassifyFastText()
        self.hanxuan_que_solid_list = select_que_cla()
        self.opt = Options().parse()
        if model=='modelA':
            self.modelpath=self.opt.modelpath[0]
        else:
            self.modelpath=self.opt.modelpath[1]
        self.inverted = {}
        self.documents = {}
        self.simility_dict = {}
        self.ques_dict = {}
        self.stop_word = [] #['？', '吗', '了', '的', '是', '在', '?', '能', '会', '不', '还']
        self.jsondic = {}
        jieba.load_userdict(self.opt.subject_term)
        self._load_basicinfo()
        self._load_lsi_model()
        self.load_inverted()

    def _load_basicinfo(self):
        with open(self.opt.stop_words, 'r', encoding='utf-8') as fr:
            for line in fr:
                self.stop_word.append(line.strip('\n'))

        with open(self.opt.simility_term, 'r', encoding='utf-8') as fr:
            for line in fr:
                words = line.strip().split(' ')
                for idx in range(0, len(words) - 1):
                    self.simility_dict.setdefault(words[idx], words[-1])
        with open(self.modelpath + '/relationship.json', "r") as f:
            self.jsondic = json.loads(f.read())
        with open(self.modelpath + '_kw/quesdic.json', 'r', encoding='utf-8') as fr_ques:
            tmp_dict = json.loads(fr_ques.read())
            for _, item in tmp_dict.items():
                if len(item) == 2:
                    self.ques_dict[item[1].strip('？').strip('?')] = item[0]


    def _load_simility(self, path):
        with open(path, 'r', encoding='utf-8') as fr:
            for line in fr:
                words = line.strip().split(' ')
                for idx in range(0, len(words) - 1):
                    self.simility_dict.setdefault(words[idx], words[-1])

    def _cut_text(self, text):
        res = []
        counter = {}
        text = text.upper()
        for idx, item in enumerate(jieba.cut(text, cut_all=True)):
            origin = item
            if item == '':
                continue
            if item not in self.stop_word:
                if item in self.simility_dict.keys():
                    item = self.simility_dict[item]
                if item in counter:
                    counter[item] += 1
                else:
                    counter.setdefault(item, 0) != 0
                res.append((len(res), (text.index(origin, counter[item]*len(item)), item)))
        return res

    def _cut_doc(self, doc):
        res = []
        for item in jieba.cut(doc, cut_all=True):
            if item not in self.stop_word:
                if item in self.simility_dict.keys():
                    item = self.simility_dict[item]
                res.append(item)
        return res

    def cut_doc(self, doc):
        res = []
        for item in jieba.cut(doc):
            if item not in self.stop_word:
                if item in self.simility_dict.keys():
                    item = self.simility_dict[item]
                res.append(item)
        return res

    def _load_lsi_model(self):
        self.dictionary = corpora.Dictionary.load(self.modelpath+self.opt.dictionary)
        #print(len(self.dictionary))
        self.model_lsi = models.LsiModel.load(self.modelpath+self.opt.lsi)
        self.sim_lsi = similarities.SparseMatrixSimilarity.load(self.modelpath+self.opt.similarity_lsi)
        self.model_tfidf = models.TfidfModel.load(self.modelpath+self.opt.tfidf)
        self.sim1 = similarities.SparseMatrixSimilarity.load(self.modelpath+self.opt.similarity)

    def load_inverted(self):
        with open(self.modelpath+self.opt.documents, 'r', encoding='utf-8') as fr_documents, \
                open(self.modelpath+self.opt.invert, 'r', encoding='utf-8') as fr_invert:
            self.documents = eval(fr_documents.read())
            self.inverted = eval(fr_invert.read())
            pass

    def precise(self, precise_doc_dic, doc, index_list, offset_list, range):
        phrase_index = reduce(lambda x, y: set(map(lambda old: old + range, x)) & set(y), index_list)
        phrase_index = map(lambda x: x - len(index_list) - range + 2, phrase_index)

        if len(list(phrase_index)):
            phrase_offset = []
            for po in phrase_index:
                phrase_offset.append(offset_list[0][index_list[0].index(po)])
            precise_doc_dic[doc] = 0.8
        return precise_doc_dic

    def search(self, query):
        doc_index = self._cut_text(query)
        words = [word for _, (offset, word) in doc_index if word in self.inverted]
        results = [set(self.inverted[word].keys()) for word in words]
        doc_set = reduce(lambda x, y: x & y, results) if results else []
        doc_list = []
        for tmp in results:
            doc_list += tmp

        res_counter = collections.Counter(doc_list)
        precise_doc_dic = {}
        if doc_set:
            for doc in doc_set:
                index_list = [[indoff[0] for indoff in self.inverted[word][doc]] for word in words]
                offset_list = [[indoff[1] for indoff in self.inverted[word][doc]] for word in words]

                precise_doc_dic = self.precise(precise_doc_dic, doc, index_list, offset_list, 1)  # 词组查询
                precise_doc_dic = self.precise(precise_doc_dic, doc, index_list, offset_list, 3)  # 临近查询
                precise_doc_dic = self.precise(precise_doc_dic, doc, index_list, offset_list, 4)  # 临近查询
                precise_doc_dic = self.precise(precise_doc_dic, doc, index_list, offset_list, 5)  # 临近查询
            if 0 == len(precise_doc_dic):
                for doc in doc_set:
                    precise_doc_dic.setdefault(doc, 0.7)
        else:
            if 0 < len(res_counter):
                _, m_value = res_counter.most_common(1)[0]
                m_value *= 1.5
                for doc in res_counter:# .most_common(10):
                    doc = doc
                    precise_doc_dic.setdefault(doc, res_counter[doc] / m_value)
        return precise_doc_dic

    def _get_simility_question(self, query):
        query_cut = self._cut_doc(query)
        query_d2b = self.dictionary.doc2bow(query_cut)
        sim = self.sim1[self.model_tfidf[query_d2b]]
        res = sorted(enumerate(sim), key=lambda item: -item[1])
        return (self.sim_lsi[self.model_lsi[query_d2b]], res[0:15])

    def _gen_json(self, hit_type, ques, answer, solution_id, sim_list, flag=1, transfer=0):
        res = {}
        res['result'] = {}
        res['result']['IsOK'] = '1' if flag else '0'
        res['result']['Msg'] = r'request sucess' if flag else r'request failed'
        res['result']['hit_type'] = str(hit_type)
        res['result']['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res['result']['hit_question'] = ques
        res['result']['similarity_question'] = sim_list
        res['result']['answer'] = answer
        res['result']['id'] = solution_id
        res['result']['transfer'] = str(transfer)
        return res

    def _hit_sensitve(self, query):
        res = self._cut_doc(query)
        sensitive = [r'自杀', r'跳楼', r'转人工', r'打架', r'杀人']
        for item in res:
            if item in sensitive:
                return True
        return False

    def _show_mid_result(self, result_docs, lsi_res, sim_res):
        print(result_docs)
        print('lsi_res', lsi_res)
        print([(self.jsondic[str(lsi_res[i][0])], lsi_res[i]) for i in range(len(lsi_res))])
        print('sim_res', sim_res)
        print([(self.jsondic[str(sim_res[i][0])], sim_res[i]) for i in range(len(sim_res))])

    def _get_res_by_threshold(self, sorted_dict, thresholda=0.9, thresholdb=0.35, thresholdc=0.2):
        res_list, res_dict = [], {}
        if len(sorted_dict) < 2:
            res_list += [sorted_dict[0][0]]
            res_dict[sorted_dict[0][0]] = math.ceil(sorted_dict[0][1] * 10000) / 10000
        elif math.ceil(sorted_dict[0][1] * 10000) / 10000 >= thresholda or sorted_dict[0][1] - sorted_dict[1][1] > thresholdb:
            res_list += [sorted_dict[0][0]]
            res_dict[sorted_dict[0][0]] = math.ceil(sorted_dict[0][1] * 10000) / 10000
            for idx in range(1, len(sorted_dict)):
                if math.ceil(sorted_dict[idx][1] * 10000) / 10000 >= thresholda:
                    res_list += [sorted_dict[idx][0]]
                    res_dict[sorted_dict[idx][0]] = math.ceil(sorted_dict[idx][1] * 10000) / 10000
                elif sorted_dict[0][1] - sorted_dict[idx][1] < thresholdb:
                    res_list += [sorted_dict[idx][0]]
                    res_dict[sorted_dict[idx][0]] = math.ceil(sorted_dict[idx][1] * 10000) / 10000
        else:
            for item in sorted_dict:
                if item[1] >= thresholdc:
                    res_dict[item[0]] = math.ceil(item[1] * 10000) / 10000
                    res_list.append(item[0])
        return res_list, res_dict

    def _merge_result(self, result_docs, lsi_res, sim_res):
        sim_dict = {}
        for i in range(len(sim_res)):
            itemindex = str(sim_res[i][0])
            sid = self.jsondic[itemindex]
            if sid not in sim_dict.keys():
                sim_dict[sid] = sim_res[i][1]
            else:
                sim_dict[sid] += 0.05

        result_docs_keys, sim_dict_keys = result_docs.keys(), sim_dict.keys()
        doc_list = [set(result_docs_keys), set(sim_dict_keys)]
        doc_set = reduce(lambda x, y: x & y, doc_list) if doc_list else []
        doc_dict = {}
        for item in set(list(result_docs_keys) + list(sim_dict_keys)):
            if item in doc_set:
                doc_dict[item] = result_docs[item] + 0.2 if result_docs[item] > sim_dict[item] else sim_dict[item] + 0.2
            elif item in result_docs_keys:
                doc_dict[item] = result_docs[item] #result_docs[item]
            elif item in sim_dict_keys:
                doc_dict[item] = sim_dict[item]
        if not doc_dict:
            tmp_dict = result_docs.copy()
            tmp_dict.update(sim_dict)
            sorted_dict = sorted(tmp_dict.items(), key=lambda item: item[1], reverse=True)
            res_list, res_dict = self._get_res_by_threshold(sorted_dict)
        else:
            sorted_doc_dict = sorted(doc_dict.items(), key=lambda item: item[1], reverse=True)
            res_list, res_dict = self._get_res_by_threshold(sorted_doc_dict)

        return res_list, res_dict

    def get_answer(self, query):
        def extract_text(doc):
            return self.documents[doc].replace('\n', ' ')
        query = Converter('zh-hans').convert(query).strip('？').strip('?')
        que_category = self.qc.pred_que_category(query)
        hit_type = 5
        if query in self.ques_dict.keys() and que_category =="非寒暄问":
            return json.dumps(self._gen_json(1, query, extract_text(self.ques_dict[query]).split('____')[0], str(self.ques_dict[query]), [], 0))
        if query in self.ques_dict.keys() and que_category =="寒暄问":
            return json.dumps(self._gen_json(4, query, extract_text(self.ques_dict[query]).split('____')[0], str(self.ques_dict[query]), [], 0))
        if self._hit_sensitve(query):
            return json.dumps(self._gen_json(hit_type, '', '', [], 1, 1))
        similarity_list = []
        answer = ''
        hit_question = ''
        solution_id = ''
        result_docs = self.search(query)
        lsi_res, sim_res = self._get_simility_question(query)
        # self._show_mid_result(result_docs, lsi_res, sim_res)
        res_list, res_dict = self._merge_result(result_docs, lsi_res, sim_res)
        intersection_que = list(set(self.hanxuan_que_solid_list).intersection(set(res_list)))
        print(res_dict)

        if que_category=='非寒暄问':
            if len(intersection_que)==0:
                pass
            else:
                res_list = [i for i in res_list if i not in intersection_que]
            if 10 < len(res_list):
                res_list = res_list[0:10]
            if 1 == len(res_list):
                hit_type=1
                solution_id = str(res_list[0])
                answer = extract_text(res_list[0]).split('____')[0]
                hit_question = extract_text(res_list[0]).split('____')[-1]
            elif res_list:
                hit_type = 2
                for doc in res_list:
                    tmp_dict = {}
                    tmp_dict['answer'] = ''
                    tmp_dict['score'] = str(res_dict[doc])
                    tmp_dict['id'] = str(doc)
                    tmp_dict['hit_question'] = extract_text(doc).split('____')[-1]
                    similarity_list.append(tmp_dict)
            else:
                hit_type = 3
                doc_str = ''
                answer = r'呜呜。小爱刚出生没多久，我的大脑中没有您想要的答案~~~'

        if  que_category=="寒暄问":
            if intersection_que:
                hit_type = 4
                solution_id = str(intersection_que[0])
                answer = extract_text(intersection_que[0]).split('____')[0]
                hit_question= extract_text(intersection_que[0]).split('____')[-1]
            else:
                hit_type = 3
                doc_str = ''
                answer = r'呜呜。小爱刚出生没多久，我的大脑中没有您想要的答案~~~'

        try:
            answer = json.dumps(self._gen_json(hit_type, hit_question, answer, solution_id, similarity_list))
        except:
            #logging.error('err: {}'.format(err))
            return json.dumps(self._gen_json(hit_type, '', '', '', [], 0))
        #print(hit_question)
        return answer   #query + '----' + doc_str + '----' + res




if __name__ == '__main__':
    ii = InvertedIndex('modelB')
    #print(ii.ques_dict)
    error_list = ['考勤异常','明天放假吗？','小爱，你在干嘛啊','宿舍办理']
    for item in error_list:
        #print(item, ii._cut_doc(item))
        print(json.loads(ii.get_answer(item)))
        #ii.get_answer(item)
    # print(ii.get_answer("申请婚假需要提交什么资料？"))#"辞职几个月可以领住房公积金"))
    # print(ii.get_answer("自离后住房公积金怎么提取"))
