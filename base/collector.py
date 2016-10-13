# encoding=utf8
import sys
sys.path.append("..")

import threading
import time
import base.constance as Constance

import utils.tools as tools

mylock = threading.RLock()

class Singleton(object):
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls,'_inst'):
            cls._inst=super(Singleton,cls).__new__(cls,*args,**kwargs)

        return cls._inst

class Collector(threading.Thread, Singleton):
    _db = tools.connectDB()
    _threadStop = False
    _urls = []
    _interval = int(tools.getConfValue("collector", "sleep_time"))

    #初始时将正在做的任务至为未做
    _db.urls.update({'status':Constance.DOING}, {'$set':{'status':Constance.TODO}}, multi=True)

    def __init__(self):
        super(Collector, self).__init__()

    def run(self):
        while not Collector._threadStop:
            self.__inputData()
            time.sleep(Collector._interval)

    def stop(self):
        Collector._threadStop = False

    def __inputData(self):
        if len(Collector._urls) > int(tools.getConfValue("collector", "max_size")):
            return
        mylock.acquire() #加锁

        site = tools.getConfValue("collector", "site")
        depth = int(tools.getConfValue("collector", "depth"))
        urlCount = int(tools.getConfValue("collector", "url_count"))
        if site == 'all':
            urlsList = Collector._db.urls.find({"status":Constance.TODO, "depth":{"$lte":depth}},{"url":1, "_id":0,"depth":1, "site":1}).sort([("depth",1)]).limit(urlCount)#sort -1 降序 1 升序
        else:
            urlsList = Collector._db.urls.find({"status":Constance.TODO, "site":site, "depth":{"$lte":depth}},{"url":1, "_id":0,"depth":1, "site":1}).sort([("depth",1)]).limit(urlCount)

        Collector._urls.extend(urlsList)

        #更新已取到的url状态为doing
        for url in Collector._urls:
            Collector._db.urls.update(url, {'$set':{'status':Constance.DOING}})

        mylock.release()


    def getUrls(self, count):
        mylock.acquire() #加锁

        urls = Collector._urls[:count]
        del Collector._urls[:count]

        mylock.release()

        return urls




