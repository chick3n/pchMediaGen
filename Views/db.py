from threading import Thread
from Queue import Queue

import sqlite3 as lite

class SingleThreadOnly(object):
    def __init__(self, db):
        self.cnx = lite.connect(db, detect_types=lite.PARSE_DECLTYPES)
        self.cursor = self.cnx.cursor()
    def execute(self, req, arg=None):
        self.cursor.execute(req, arg or tuple())
    def select(self, req, arg=None):
        self.execute(req, arg)
        for raw in self.cursor:
            yield raw
    def close(self):
        self.cnx.close()

class MultiThreadOK(Thread):
    def __init__(self, db):
        super(MultiThreadOK, self).__init__()
        self.db=db
        self.reqs=Queue()
        self.start()
    def run(self):
        cnx = lite.connect(self.db, detect_types=lite.PARSE_DECLTYPES)
        cursor = cnx.cursor()
        while True:
            req, arg, res = self.reqs.get()
            if req=='--close--': break
            try:
                cursor.execute(req, arg)
                if res:
                    for rec in cursor:
                        res.put(rec)
                    res.put('--no more--')
            except:
                pass
        cnx.close()
    def execute(self, req, arg=None, res=None):
        self.reqs.put((req, arg or tuple(), res))
    def select(self, req, arg=None):
        res=Queue()
        self.execute(req, arg, res)
        while True:
            rec=res.get()
            if rec=='--no more--': break
            yield rec
    def close(self):
        self.execute('--close--')
    def kill(self):
        self.execute('--close--')
        self.join()