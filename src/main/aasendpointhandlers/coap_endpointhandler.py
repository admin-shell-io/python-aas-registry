'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import logging
import threading
import asyncio
from aiocoap import *
from aiocoap import resource
import aiocoap
try:
    from utils.i40data import Generic
except ImportError:
    from main.utils.i40data import Generic

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from main.abstract.endpointhandler import AASEndPointHandler

try:
    from aasendpointhandlers.coap_endpointresources import RetrieveMessageCoap,HandleConnectProtocolCoap,HandleConnectCoap
except ImportError:
    from main.aasendpointhandlers.coap_endpointresources import RetrieveMessageCoap,HandleConnectProtocolCoap,HandleConnectCoaps

class AASEndPointHandler(AASEndPointHandler):
    
    def __init__(self, pyAAS,msgHandler):
        self.pyAAS = pyAAS
        self.msgHandler = msgHandler
        self.targetHeader = {"content-type": "application/json"} 
        
    def configure(self):
        
        self.ipaddressComdrv = "127.0.0.1"#'0.0.0.0'
        self.portComdrv = self.pyAAS.lia_env_variable["LIA_AAS_COAP_PORT_INTERN"]
        self.root = resource.Site()

        self.root.add_resource(["i40commu"],RetrieveMessageCoap(self.pyAAS))
        self.root.add_resource(["publish"], HandleConnectProtocolCoap(self.pyAAS))
        self.root.add_resource(["connect"], HandleConnectCoap(self.pyAAS))
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("coap-server").setLevel(logging.DEBUG)
        
                
    def update(self, channel):
        pass
    
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.Task(aiocoap.Context.create_server_context(self.root,bind = (self.ipaddressComdrv,int(self.portComdrv))))
        self.pyAAS.serviceLogger.info("COAP namespaces are started")
        self.pyAAS.serviceLogger.info("COAP REST API namespaces are configured========================================")
        asyncio.get_event_loop().run_forever()
    
    def start(self, pyAAS, uID):
        restServerThread = threading.Thread(target=self.run)
        restServerThread.start()

    def stop(self):
        self.pyAAS.serviceLogger.info("REST API namespaces are stopped.")

    
    async def dispatch(self,uri,payload):
        protocol = await Context.create_client_context()
        request = Message(code=2,uri=uri,payload=payload)
        try:
            self.response = await protocol.request(request).response
        except Exception as e:
            self.response = None    
    
    def dispatchMessage(self, send_Message): 
        try:
            targetID = send_Message["frame"]["receiver"]["identification"]["id"]
            targetAAS_URI = self.pyAAS.coapEndPointsDict[targetID]
            payload = json.dumps(send_Message).encode("utf-8")
            asyncio.get_event_loop().run_until_complete(self.dispatch(targetAAS_URI,payload))
            if (self.response == None):
                return False
            else:
                code = self.response.code
                self.response = None
                if (code == Code.CHANGED):
                    return True
                else:
                    return False
        except Exception as e:
            return False

    def sendBroadCatMessage(self,sendMessage,key):
        targetAAS_URI = self.pyAAS.coapEndPointsDict[key]
        try:
            payload = json.dumps(sendMessage).encode("utf-8")
            asyncio.get_event_loop().run_until_complete(self.dispatch(targetAAS_URI,payload))
        except Exception as E:
            pass
                            
    def dispatchBroadCastMessage(self,send_Message):
        for key in self.pyAAS.coapEndPointsDict.keys():
            (threading.Thread(target=self.sendBroadCatMessage,args=(send_Message,key))).start()     
             
    def sendExceptionMessageBack(self,ErrorMessage):
        I40FrameData = {
                                "semanticProtocol": "Register",
                                "type" : "registerAck",
                                "messageId" : "registerAck_1",
                                "SenderAASID" : self.pyAAS.AASID,
                                "SenderIdType" : "idShort",
                                "SenderRolename" : "HTTP_ENDPoint",
                                "conversationId" : "AASNetworkedBidding",
                                "replyBy" :  "",
                                "replyTo" :  "",                                
                                "ReceiverAASID" :  self.pyAAS.AASID,
                                "ReceiverIdType" : "idShort",
                                "ReceiverRolename" : "Register"
                        }
        self.gen = Generic()
        self.frame = self.gen.createFrame(I40FrameData)
        
        self.InElem = self.pyAAS.dba.getAAsSubmodelsbyId(self.pyAAS.AASID,"StatusResponse")["message"][0]
        
        self.InElem["submodelElements"][0]["value"] = "E"
        self.InElem["submodelElements"][1]["value"] = "E009. delivery-error"
        self.InElem["submodelElements"][2]["value"] = ErrorMessage
         
        registerAckMessage ={"frame": self.frame,
                                "interactionElements":[self.InElem]}
        
        self.pyAAS.msgHandler.putIbMessage(registerAckMessage)
        
    
    def retrieveMessage(self, testMesage):  # todo
        pass

