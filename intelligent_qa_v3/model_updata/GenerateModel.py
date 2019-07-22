#coding=utf-8
import sys
sys.path.append('../')
import warnings
import json
from options.options import Options
from collections import defaultdict
from langconv import *
from datetime import datetime
import jieba
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
from gensim import corpora, models, similarities
from model_updata.SQL_data import dic_merge
import os



class GenerateModel(object):
    def __init__(self,modelpath):
    
        self.model_save_path=''
        self.opt = Options().parse()
        
    
        if not os.path.exists(self.opt.modelpath[1]):
            os.mkdir(self.opt.modelpath[1])
        if not os.path.exists(self.opt.modelpath[0]):
            os.mkdir(self.opt.modelpath[0])
            
        if modelpath=='modelA':
            self.model_save_path = self.opt.modelpath[0]
        elif modelpath=='modelB':
            self.model_save_path = self.opt.modelpath[1]

        

        self.documents = {}
        self.inverted = {}
        self.simility_dict = {}
        self.stop_word = []
        self.ques_list = []
        jieba.load_userdict(self.opt.subject_term)
        self._load_simility(self.opt.simility_term)
        self.load_basicinfo()
        self.gen_inverted()
        self.deal_question()
    def _load_simility(self, path):
        with open(path, 'r', encoding='utf-8') as fr:
            for line in fr:
                words = line.strip().split(' ')
                for idx in range(0, len(words) - 1):
                    self.simility_dict.setdefault(words[idx], words[-1])

    def load_basicinfo(self):
        with open(self.opt.stop_words, 'r', encoding='utf-8') as fr:
            for line in fr:
                self.stop_word.append(line.strip('\n'))
        self.documents, ques_list_tmp, relationship = dic_merge()
        for ques in ques_list_tmp:
            query = line.strip('\n')
            self.ques_list.append(self._cut_doc(Converter('zh-hans').convert(ques)))
        json_str = json.dumps(relationship)
        with open((self.model_save_path+'/relationship.json'), 'w') as fp:
            fp.write(json_str)
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
                res.append((len(res), (text.index(origin, counter[item]), item)))
        return res

    def inverted_index(self, text):

        word_index = self._cut_text(Converter('zh-hans').convert(text))
        doc_index = {}
        for index, (offset, word) in word_index:
            locations = doc_index.setdefault(word, [])
            locations.append((index, offset))
        return doc_index

    def inverted_index_add(self, doc_id, doc_index):
        for word, locations in doc_index.items():
            indices = self.inverted.setdefault(word, {})
            indices[doc_id] = locations


    def gen_inverted(self):
        ibegin = datetime.now()
        for doc_id, text in self.documents.items():
            doc_index = self.inverted_index(text)
            self.inverted_index_add(doc_id, doc_index)

        with open(self.model_save_path+self.opt.documents, 'w', encoding='utf-8') as fw_documents, \
                open(self.model_save_path+self.opt.invert, 'w', encoding='utf-8') as fw_invert:
            fw_documents.write(str(self.documents))
            fw_invert.write(str(self.inverted))
            pass
        print('gen incerted index time{}'.format(datetime.now() - ibegin))

    def _load_stop(self):
        with open(self.opt.stop_words, 'r', encoding='utf-8') as fr:
            for line in fr:
                self.stop_word.append(line.strip('\n'))

    def _cut_doc(self, doc):

        res = []
        for item in jieba.cut(doc):
            if item not in self.stop_word:
                if item in self.simility_dict.keys():
                    item = self.simility_dict[item]
                res.append(item)
        return res
    def _calc_frequent(self, doc_list):
        frequency = defaultdict(int)
        for doc in doc_list:
            for token in doc:
                frequency[token] += 1
        print('max frequency is {}'.format(max(frequency.values())))
        texts = [[token for token in doc if frequency[token] > 0 and frequency[token] < 1000] for doc in doc_list]
       # print([[token for token in doc if frequency[token] > 1000] for doc in doc_list])
        return texts


    def _gen_bag_word(self, texts):
        dictionary = corpora.Dictionary(texts)
        dictionary.save(self.model_save_path+self.opt.dictionary) # 'model/golden.dic')
       # print(self.model_save_path+self.opt.dictionary)
        self.dictionary = dictionary

    def _gen_corpus_tfidf(self, texts):
        self.corpus = [self.dictionary.doc2bow(doc) for doc in texts]
        corpora.MmCorpus.serialize(self.model_save_path+self.opt.corpus, self.corpus) #'model/corpus.mm'
       # print(self.model_save_path+self.opt.corpus)
        self.tfidf = models.TfidfModel(self.corpus)

        self.corpus_tfidf = self.tfidf[self.corpus]
        self.index = similarities.SparseMatrixSimilarity(self.tfidf[self.corpus], num_features=len(self.dictionary.keys()))
        self.index.save(self.model_save_path+self.opt.similarity) # 'model/similarity.sim')
        print(self.model_save_path+self.opt.similarity)
        self.tfidf.save(self.model_save_path+self.opt.tfidf) #'model/model.tfidf')
        print(self.model_save_path+self.opt.tfidf)

        self.lsi = models.LsiModel(self.corpus_tfidf)
        self.corpus_lsi = self.lsi[self.corpus_tfidf]
        self.similarity_lsi = similarities.SparseMatrixSimilarity(self.corpus_lsi, num_features=len(self.dictionary.keys()), num_best=5)
        self.similarity_lsi.save(self.model_save_path+self.opt.similarity_lsi) #'model/similarity_lsi.sim')
        print(self.model_save_path+self.opt.similarity_lsi)
        self.lsi.save(self.model_save_path+self.opt.lsi) #'model/model.lsi')
        print(self.model_save_path+self.opt.lsi)
        corpora.MmCorpus.serialize(self.model_save_path+self.opt.lsi_corpus, self.corpus_lsi) #'model/lsi_corpus.mm', self.corpus_lsi)
        print(self.model_save_path+self.opt.lsi_corpus)
        pass

    def deal_question(self):
        ques_calc = self._calc_frequent(self.ques_list) #self._load_ques_list())
        self._gen_bag_word(ques_calc)
        self._gen_corpus_tfidf(ques_calc)



# if __name__ == '__main__':
#     gm = GenerateModel('modelA')
