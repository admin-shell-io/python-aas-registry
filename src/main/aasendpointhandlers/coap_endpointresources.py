'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''



import json
from datetime import datetime
import aiocoap.resource as resource
import aiocoap
from aiocoap.numbers import Code
try:
    from utils.i40data import Generic
except ImportError:
    from src.main.utils.i40data import Generic

try:
    from utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse
except ImportError:
    from src.main.utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse

class RetrieveMessageCoap(resource.Resource):    
    def __init__(self, pyAAS):
        super().__init__()
        self.pyAAS = pyAAS
        
    async def render_post(self,request):
        tMessage = json.loads(request.payload.decode("utf-8"))
        try:
            _type = tMessage["frame"]["type"]
            if (_type == "HeartBeat"):
                _sender = tMessage["frame"]["sender"]["id"]
                _senderIdType = ""
                cr = ConnectResponse(self.pyAAS)
                if _sender in list(self.pyAAS.coapEndPointsDict.keys()):
                    self.pyAAS.aasBotsDict[_sender] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                    phbAck = cr.creatHeartBeatCoapResponse(_sender,_senderIdType, tMessage["frame"]["conversationId"])
                    message =  aiocoap.Message(code=Code.CHANGED, payload=json.dumps(phbAck).encode("utf-8"))
                else:
                    nhbAck = cr.createHeartBeatNegativeCoapResponse(_sender,_senderIdType, tMessage["frame"]["conversationId"]) 
                    message =  aiocoap.Message(code=Code.CHANGED, payload=json.dumps(nhbAck).encode("utf-8"))
            else :
                if "receiver" not in list(tMessage["frame"].keys()):
                    self.pyAAS.msgHandler.putBroadCastMessage(tMessage)
                elif tMessage["frame"]["receiver"]["id"] == "AASpillarbox" and tMessage["frame"]["type"] == "register":
                    data = self.pyAAS.skillInstanceDict["RegistryHandler"].restAPIHandler(tMessage)
                    message =  aiocoap.Message(code=Code.CHANGED, payload=json.dumps(data).encode("utf-8"))
                else:
                    _receiver = tMessage["frame"]["receiver"]["id"]
                    if _receiver in list(self.pyAAS.connectBotsDict.keys()):
                        self.pyAAS.connectBotsDict["iframesList"].append(tMessage)
                    else:
                        self.pyAAS.msgHandler.putTransportMessage(tMessage)
        except Exception as E:
            message =  aiocoap.Message(code=Code.INTERNAL_SERVER_ERROR, payload="Unexpected Internal Error".encode("utf-8"))
        return message
    
class HandleConnectProtocolCoap(resource.Resource):
    def __init__(self, pyAAS):
        super().__init__()
        self.pyAAS = pyAAS
    
    async def render_post(self,request):
        heartBeat = request.payload
        try:
            messageType = heartBeat["frame"]["type"]
            if (messageType == "HeartBeat"):
                timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                data = {"timestamp":timestamp,"data":heartBeat}
                self.pyAAS.msgHandler.putConnectMessage(data)
                _senderId = heartBeat["frame"]["sender"]["id"]
                self.pyAAS.aasBotsDict[_senderId] = timestamp
                cResponse = ConnectResponse(self.pyAAS)
                _iframedata = cResponse._createNewIframeData(_senderId,"ksks") 
                if _senderId in list(self.pyAAS.connectBotsDict.keys()):
                    for iMessage in  self.pyAAS.connectBotsDict[_senderId]["iframesList"]:
                        _iframedata["interactionElements"].append(json.dumps(iMessage))
                    self.pyAAS.connectBotsDict[_senderId]["iframesList"].clear()
                message =  aiocoap.Message(payload=json.dumps(_iframedata).encode("utf-8"),code=Code.CHANGED)
            else:
                message =  aiocoap.Message(payload="Unexpected Internal Server Error".encode("utf-8"),code=Code.INTERNAL_SERVER_ERROR)
        except Exception as E:
            message =  aiocoap.Message(payload="Unexpected Internal Server Error".encode("utf-8"),code=Code.INTERNAL_SERVER_ERROR)
        return message 

class HandleConnectCoap(resource.Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    async def render_post(self,request):
        message =  aiocoap.Message(payload="OK".encode("utf-8"),code=Code.CHANGED)       
        return message