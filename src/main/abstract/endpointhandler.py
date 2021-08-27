'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''
import abc


class AASEndPointHandler(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, pyAAS, msgHandler):
        self.saas = pyAAS
        self.ipaddressComdrv = "ipaddressComdrv"
        self.portComdrv = "portComdrv"
        self.msgHandler = msgHandler

    @abc.abstractmethod
    def configure(self):
        pass

    # @abc.abstractmethod
    def update(self, channel):
        pass

    @abc.abstractmethod
    def start(self, saas):
        pass

    @abc.abstractmethod 
    def stop(self):
        pass
    
    @abc.abstractmethod
    def dispatchMessage(self, tMessage):
        pass
    
    @abc.abstractmethod
    def retrieveMessage(self, testMesage):
        pass
