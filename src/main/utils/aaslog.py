'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import logging


class LogList(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.maxSize = 100000000
        
    def setMaxSize(self,maxSize):
        self.maxSize = maxSize
    
    def getCotent(self):
        returnCotent = "\n".join(self)
        return returnCotent
    
    def getTailCotnent(self,numRecords):
        returnCotent = "\n".join(self[-numRecords:])
        return returnCotent
    
    def getHeadContent(self,numRecords):
        returnCotent = "\n".join(self[0:numRecords])
        return returnCotent
    
    def getCurrentSize(self):
        return len(self)
    
    def getMaxSize(self):
        return self.maxSize

class serviceLogHandler(logging.Handler):
    def __init__(self,loglist):
        logging.Handler.__init__(self)
        self.loglist = loglist
        
    def emit(self,record):
        try:
            if len(self.loglist) ==  self.loglist.maxSize:
                self.loglist.pop(0)
            self.loglist.append(str(self.format(record)))
        except Exception:
            self.handleError(record)
