import jieba
import os
import datetime
def demo():
    for item in jieba.cut(r'身体里有铁可以进厂吗， 自身含铁可以进车间吗'):
        print(item)

if __name__ == '__main__':
    import MySQLdb
    db = MySQLdb.connect(host="10.207.249.163", port=5120, user="xiaoai", passwd="2018@winter", db="xiaoai")
    print(db.encoding)