from GenerateModel import GenerateModel
from GenerateQueModel import GenerateQueModel
import fcntl
import time as T
import os
from SQL_data import trigger_log,trigger_delete
from datetime import  datetime, timedelta


def updata_model():
    if not os.path.exists('../log/flag.txt'):
        os.mknod('../log/flag.txt')
    fp = open('../log/flag.txt', 'r+', encoding='utf-8')
    fcntl.flock(fp, fcntl.LOCK_EX)
    line = fp.read()
    if line == '':
        #print('***************  Start updata model  ****************')
        starttime = T.time()
        try:
            gm = GenerateModel('modelA')
            kw=GenerateQueModel('modelA')
        except Exception as e:
            print(e)
        endtime = T.time()
        runtime = endtime - starttime
        fp.write('modelA')
        write_time = T.strftime("%Y-%m-%d %H:%M:%S", T.localtime())
        #print('{} ModelA have updata,takes time {}s'.format(write_time, runtime))
        #print('****************  Successful model update  ****************')
    else:
        if 'modelA' in line:
            #print('***************  Start updata model ****************')
            starttime = T.time()
            gm = GenerateModel('modelB')
            kw=GenerateQueModel('modelB')
            endtime = T.time()
            runtime = endtime - starttime
            fp.seek(0)
            fp.truncate()
            fp.write('modelB')
            write_time = T.strftime("%Y-%m-%d %H:%M:%S", T.localtime())
            #print('{} ModelB have updata,takes time {}s'.format(write_time, runtime))
            #print('****************  Successful model update  ****************')
        if 'modelB' in line:
            #print('****************  Start updata model  ****************')
            starttime = T.time()
            gm = GenerateModel('modelA')
            kw=GenerateQueModel('modelA')
            endtime = T.time()
            runtime = endtime - starttime
            fp.seek(0)
            fp.truncate()
            fp.write('modelA')
            write_time = T.strftime("%Y-%m-%d %H:%M:%S", T.localtime())
            #print('{} ModelA have updata,takes time {}s'.format(write_time, runtime))
            #print('****************  Successful model update  ****************')
    fp.flush()

    fcntl.flock(fp, fcntl.LOCK_UN)
    fp.close()

def work():
    trigger_data = trigger_log()
    if trigger_data != ():
        updata_model()
        trigger_delete()
    else:
        pass

def run_work(work, day=0, hour=0, min=0, second=0):
    now = datetime.now()
    strnow = now.strftime('%Y-%m-%d %H:%M:%S')
    #print("now:", strnow)
    period = timedelta(days=day, hours=hour, minutes=min, seconds=second)
    next_time = now + period
    strnext_time = next_time.strftime('%Y-%m-%d %H:%M:%S')
    #print("next run:", strnext_time)
    while True:
        iter_now = datetime.now()
        iter_now_time = iter_now.strftime('%Y-%m-%d %H:%M:%S')
        #print("start work: %s" % iter_now_time)
        work()
        #print("task done.")
        iter_time = iter_now + period
        strnext_time = iter_time.strftime('%Y-%m-%d %H:%M:%S')
        #print("next_iter: %s" % strnext_time)
        T.sleep(min*60)
def main():
    #try:
    run_work(work=work, min=5)




if __name__ == '__main__':
    main()
    #updata_model()
