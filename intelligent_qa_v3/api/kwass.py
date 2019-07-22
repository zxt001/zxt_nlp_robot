#coding=utf-8
import sys
sys.path.append('../')
import jieba
from options.options import Options
import collections
from langconv import *
from functools import reduce
from gensim import corpora, models, similarities
from model_updata.SQL_data import dic_merge
import json
from datetime import datetime
import time

class InvertedIndex_kw(object):
    def __init__(self,model='modelA'):
        self.opt = Options().parse()
        if model=='modelA':
            self.modelpath=self.opt.modelpath_kw[0]
        else:
            self.modelpath=self.opt.modelpath_kw[1]
        self.inverted = {}
        self.documents = {}
        self.simility_dict = {}
        self.ques_dic={}
        jieba.load_userdict(self.opt.subject_term)
        self._load_basicinfo()
        self._load_lsi_model()
        self.load_inverted()

    def _load_basicinfo(self):
        with open(self.modelpath+self.opt.quesdic, 'r', encoding='utf-8') as jsonf:
            self.ques_dic=json.load(jsonf)
            #print(len(self.ques_dic))

        with open(self.opt.simility_term, 'r', encoding='utf-8') as fr:
            for line in fr:
                words = line.strip().split(' ')
                for idx in range(0, len(words) - 1):
                    self.simility_dict.setdefault(words[idx], words[-1])

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
            if item in self.simility_dict.keys():
                item = self.simility_dict[item]
            if item in counter:
                counter[item] += 1
            else:
                counter.setdefault(item, 0) != 0
            res.append((len(res), (text.index(origin, counter[item]*len(item)), item)))
        return res

    def _cut_doc(self, doc):
        res = ''
        wordlist=[]
        for item in jieba.cut(doc):
            if item in self.simility_dict.keys():
                item = self.simility_dict[item]
            res=res+item
        for word in res:
            wordlist.append(word)
        return wordlist
        
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
            #print(self.documents)
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
        
    def _gen_json(self, sim_list, flag=1):
        res = {}
        res['result'] = {}
        res['result']['IsOK'] = '1' if flag else '0'
        res['result']['Msg'] = r'request sucess' if flag else r'request failed'
        res['result']['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res['result']['similarity_question'] = sim_list
        return res

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
        return (self.sim_lsi[self.model_lsi[query_d2b]], res[0:50])


    def get_answer(self, query):
        query = Converter('zh-hans').convert(query)
        result_docs = self.search(query)
        lsi_res, sim_res = self._get_simility_question(query)
        answer=[]
        answer_backup=[]
        #print(sim_res)
        for idx,score in sim_res:
            tmp_dict = {}
            if score>0.1:
                stranswer=self.ques_dic[str(idx)][1].replace('\n', ' ')
                s=''
                if not ''.join(set(stranswer)&set(query))==s.strip():
                    tmp_dict['score'] = str(score)
                    answer_list=self.ques_dic.get(str(idx))
                    tmp_dict['hit_question'] = answer_list[1]
                    tmp_dict['solution_id']=answer_list[0]
                    answer.append(tmp_dict)
                    if len(answer)==5:
                        break
                else:
                    tmp_dict['score'] = str(score)
                    answer_list=self.ques_dic.get(str(idx))
                    tmp_dict['hit_question'] = answer_list[1]
                    tmp_dict['solution_id']=answer_list[0]
                    answer_backup.append(tmp_dict)
        if len(answer)<5:
            answer=answer+answer_backup[0:4-len(answer)]
        #print(answer)
        try:
            answer_json = json.dumps(self._gen_json(answer))
        except:
            #logging.error('err: {}'.format(err))
            return json.dumps(self._gen_json([],0))
        return answer_json

if __name__=="__main__":
    abc=InvertedIndex_kw('modelA')
    print(abc.documents)
    abc=InvertedIndex_kw('modelB')
    print(abc.documents) 
    start=time.time()
    abc.get_answer('3月份薪资')
    print(time.time()-start)
