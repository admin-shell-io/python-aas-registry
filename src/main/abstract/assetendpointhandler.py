'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import abc



class AsssetEndPointHandler(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, saas, ip, port, username, password, propertylist):
        self.saas = saas
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password 
        self.propertylist = propertylist
        
    def add_raw_channel_ref(self, ref_id, address):
        self.raw_channel_refs[ref_id] = address

    def configure(self, ioAdaptor):
        pass

    @abc.abstractmethod
    def read(self, address):
        pass

    @abc.abstractmethod
    def write(self, address, value):
        pass
