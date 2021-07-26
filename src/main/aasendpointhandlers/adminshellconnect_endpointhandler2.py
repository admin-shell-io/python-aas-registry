'''
Copyright (c) 2021-2022 OVGU LIA
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import logging
import os
import requests
import threading
import time

try:
    from utils.i40data import Generic
except ImportError:
    from main.utils.i40data import Generic

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from main.abstract.endpointhandler import AASEndPointHandler



    
class AASEndPointHandler(AASEndPointHandler):
    
    def __init__(self, pyAAS,msgHandler):
        self.pyAAS = pyAAS
        
        self.msgHandler = msgHandler
        
    def configure(self):
        
        self.ipaddressComdrv = self.pyAAS.lia_env_variable["LIA_AAS_ADMINSHELL_CONNECT_IP"]
        self.portComdrv = self.pyAAS.lia_env_variable["LIA_AAS_ADMINSHELL_CONNECT_PORT"]
        
        self.connectionHandler = True
        self.hb_Message = {"source":self.pyAAS.AASID,"data":[]}
        self.adminShellConnectURI = "https://" + self.ipaddressComdrv + ":" + self.portComdrv + "/publish"
        self.connectHeader = {"content-type": "application/json"}
        
        self.pyAAS.serviceLogger.info("ADMINSHELL Connect Adaptor is configured")
                
    def update(self, channel):
        pass
    
    def run(self):
        while self.connectionHandler:
            try:
                r = requests.post(self.adminShellConnectURI, json=(self.hb_Message), headers=self.connectHeader)
                if (r.text != ""):
                    directoryData = json.loads(r.text)
                    for entry in directoryData["data"]:
                        if (entry["destination"] == self.pyAAS.AASID  and entry["type"] == "register" ):
                            descriptorData = json.loads(entry["publish"][0])
                            descUrl = "http://localhost:9021/api/v1/registry/"+descriptorData["idShort"]
                            _putRegistryResponse = requests.put(descUrl,data=json.dumps(descriptorData),headers=self.connectHeader)
                else:
                    pass#self.pyAAS.serviceLogger.info(r.text)
            except Exception as E:
                self.pyAAS.serviceLogger.info(str(E) + "ADMIn SHELL CONNECT ERROR")
            time.sleep(1)

    
    def start(self, pyAAS, uID):
        restServerThread = threading.Thread(target=self.run)
        restServerThread.start()

    def stop(self):
        self.connectionHandler = False
        self.pyAAS.serviceLogger.info("ADMINSHELL Connect Adaptor is stopped.")
    
    def dispatchMessage(self, send_Message): 
        self.pyAAS.serviceLogger.info("A new message is dispatched.")
    
    
    def retrieveMessage(self, message):  # todo
        self.pyAAS.serviceLogger.info("A new message is arrived .")
