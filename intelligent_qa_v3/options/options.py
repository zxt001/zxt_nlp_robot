import argparse

class Options(object):
    def __init__(self):
        self.opt = None
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument('--subject_term', type=str, default=r'../utils/dict.txt', help=r'subject term file path')
        self.parser.add_argument('--simility_term', type=str, default=r'../utils/simility.txt', help=r'simility term file path')
        self.parser.add_argument('--stop_words', type=str, default=r'../utils/stop_word.txt', help=r'stop term file path')
        self.parser.add_argument('--question', type=str, default=r'../utils/ques.txt', help=r'question file path')
        self.parser.add_argument('--dictionary', type=str, default=r'/golden.dic', help=r'dictionary file path')
        self.parser.add_argument('--corpus', type=str, default='/corpus.mm', help=r'dictionary file path')
        self.parser.add_argument('--tfidf', type=str, default='/model.tfidf', help=r'dictionary file path')
        self.parser.add_argument('--similarity', type=str, default='/similarity.sim', help=r'dictionary file path')
        self.parser.add_argument('--lsi', type=str, default='/model.lsi', help=r'dictionary file path')
        self.parser.add_argument('--quesdic',type=str,default='/quesdic.json',help=r'quedic file path')
        self.parser.add_argument('--similarity_lsi', type=str, default='/similarity_lsi.sim', help=r'dictionary file path')
        self.parser.add_argument('--lsi_corpus', type=str, default='/lsi_corpus.mm', help=r'dictionary file path')
        self.parser.add_argument('--documents', type=str, default='/documents.mm', help=r'documents file path')
        self.parser.add_argument('--invert', type=str, default='/invert.mm', help=r'invert file path')
        self.parser.add_argument('--modelpath',type=list,default=['../modelA','../modelB'],help=r'model document path')
        self.parser.add_argument('--modelpath_kw',type=list,default=['../modelA_kw','../modelB_kw'],help=r'kwass_model document path')
        self.parser.add_argument('--model_log',type=str,default=r'log/model_log.log',help='model updata flag log')
        self.parser.add_argument('--relationship',type=str,default=r'log/relationship.txt',help='Relationship between question id and solution id ')
        self.parser.add_argument('--portID',type=int,default=2018,help='listen portID')
        self.parser.add_argument('--fasttextpath', type=str, default=r"../utils/fasttext_stop_01.model.bin")
        self.parser.add_argument('--feidict', type=str, default=r"../utils/feihanxuan_dict.txt")


    def parse(self):
        self.opt = self.parser.parse_args()
        return self.opt
