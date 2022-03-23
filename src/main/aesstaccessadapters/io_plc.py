'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


from opcua import Client
from opcua import ua
import os
import glob

try:
    from abstract.assetendpointhandler import AsssetEndPointHandler
except ImportError:
    from main.abstract.assetendpointhandler import AsssetEndPointHandler


class AsssetEndPointHandler(AsssetEndPointHandler):

    def __init__(self, saas, ip, port, username, password, propertylist):
        super(AsssetEndPointHandler, self).__init__(saas, ip, port, username, password, propertylist)
 
        self.plc_opcua_Client = Client("opc.tcp://" + ip + ":" + port + "/")
        
        if (self.username != "-"):
            self.plc_opcua_Client._username = self.username
            self.plc_opcua_Client._password = self.password

    def read(self, nodeID):
        
        MW_VALUE = 0
        
        try:
            self.plc_opcua_Client.connect() 
            MW_VALUE = self.plc_opcua_Client.get_node(nodeID).get_value()
        
        except Exception as e:
            print(e)
            self.plc_opcua_Client.disconnect()
            MW_VALUE = 1 
        
        finally:
            self.plc_opcua_Client.disconnect()
            return MW_VALUE
    
    def write(self, nodeID, value):
        
        MW_VALUE = 0
        
        try:
            self.plc_opcua_Client.connect() 
            plcnode = self.plc_opcua_Client.get_node(nodeID)
            plcnode.set_value(value)

        except:
            self.plc_opcua_Client.disconnect()
            MW_VALUE = 1 
        
        finally:
            self.plc_opcua_Client.disconnect()
            return MW_VALUE
   
