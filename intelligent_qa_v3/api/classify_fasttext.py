# -*- coding: utf-8 -*-

import sys
sys.path.append('./')
sys.path.append('../')
import logging
import fasttext
from options.options import Options
import jieba
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)



class QueClassifyFastText(object):

    def __init__(self):
        self.opt = Options().parse()
        self.model_path = self.opt.fasttextpath
        self.dict_path = self.opt.subject_term
        self.stop_word_path = self.opt.stop_words
        self.fei_dict_path = self.opt.feidict
        self.stopwords = self.stopwordslist(self.stop_word_path)
        self.fei_dict_list = self.fei_dict_load(self.fei_dict_path)
        self.classifier = fasttext.load_model(self.model_path, label_prefix='__label__')
    
        jieba.load_userdict(self.dict_path)
    
    def fei_dict_load(self,dict_path):
        with open(dict_path, 'r',encoding='utf-8') as ff:
            fei_dict = [i.strip() for i in ff.readlines()]
        return fei_dict



    def stopwordslist(self,filepath):
        with open(filepath, 'r',encoding='utf-8') as fs:
            stopwords = [line.strip() for line in fs.readlines()]
        return stopwords


    def seg_sentence(self,sentence):
        sentence_seged = jieba.cut(sentence.strip())
        outstr = " "
        for word in sentence_seged:
            if word not in self.stopwords:
                if word != '\t':
                    outstr += word
                    outstr += " "
        return outstr


    def pred_que_category(self,question):
        res = {}
        que_str = self.seg_sentence(question)
        for i in [que_str]:
            que_list = i.split()
        fei_same_words = list(set(self.fei_dict_list).intersection(set(que_list)))
        
        label = self.classifier.predict([que_str])[0][0]
        if label == '寒暄问' and len(fei_same_words)==0 :
            
            category = '寒暄问'
        else:
            category = '非寒暄问'
        return category

if __name__ == '__main__':
    qct = QueClassifyFastText()
    str = '我想要一个好妈妈，好爸爸，好爷爷 '
    label = qct.pred_que_category(str)
    print(label)
    pass
        