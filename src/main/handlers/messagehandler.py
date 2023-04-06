'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


import json
import requests
import  threading
import time
import uuid

try:
    import queue as Queue
except ImportError:
    import Queue as Queue 

try:
    from datastore.datamanager import DataManager
except ImportError:
    from src.main.datastore.datamanager import DataManager

try:
    from utils.aaslog import serviceLogHandler,LogList
except ImportError:
    from src.main.utils.aaslog import serviceLogHandler,LogList


class MessageHandler(object):
    '''
    classdocs
    '''

    def __init__(self, pyAAS):
        '''
        Constructor
        '''
        self.pyAAS = pyAAS
        self.inBoundQueue = Queue.Queue()
        self.outBoundQueue = Queue.Queue()
        
        self.transportQueue = Queue.Queue()
        self.transportP1Queue = Queue.Queue()
        self.transportP2Queue = Queue.Queue()
        self.connectQueue = Queue.Queue()
        self.broadCastMessage = Queue.Queue()
        
        self.RegistryHandlerLogList = LogList()
        self.RegistryHandlerLogList.setMaxSize(maxSize= 200)

        
        self.logListDict = {
                              "RegistryHandler" : self.RegistryHandlerLogList
                            }
        
        self.POLL = True
        
    def start(self, skillName, AASendPointHandlerObjects):
        self.skillName = skillName
        self.AASendPointHandlerObjects = AASendPointHandlerObjects
           
        while self.POLL:

            if (self.broadCastMessage).qsize() != 0:
                broadCastThread = threading.Thread(target=self.__processbroadCastMessage__,args=(self.getBroadCastMessage(),))
                broadCastThread.start()      
                
            if (self.transportQueue).qsize() != 0:
                transportThread = threading.Thread(target=self.__sendTransportMessage_,args=(self.getTransportMessage(),))
                transportThread.start()
            
            if (self.transportP1Queue).qsize() != 0:
                transportP1Thread = threading.Thread(target=self.__sendTransportP1Message_,args=(self.getTransportP1Message(),))
                transportP1Thread.start()

            if (self.transportP2Queue).qsize() != 0:
                transportP2Thread = threading.Thread(target=self.__sendTransportP2Message_,args=(self.getTransportP2Message(),))
                transportP2Thread.start()
            
            if (self.connectQueue).qsize() != 0:
                connectProtThread = threading.Thread(target=self.__processCprotMessage__,args=(self.getConnectMessage(),))
                connectProtThread.start()

            if (self.outBoundQueue).qsize() != 0:
                obThread = threading.Thread(target=self.sendOutBoundMessage, args=(self.getObMessage(),))     
                obThread.start()
            
            if (self.inBoundQueue).qsize() != 0:
                ibThread = threading.Thread(target=self._receiveMessage_, args=(self.getIbMessage(),))     
                ibThread.start()
            
                
    def stop(self):
        self.POLL = False
        
    def putIbMessage(self, message):
        self.inBoundQueue.put((message))
    
    def getIbMessage(self):
        return self.inBoundQueue.get()
    
    def putObMessage(self, message):
        self.outBoundQueue.put(message)
    
    def getObMessage(self):
        return self.outBoundQueue.get()
    
    def getTransportMessage(self):
        return self.transportQueue.get()
    
    def putTransportMessage(self,message):
        self.transportQueue.put(message)
    
    def getTransportP1Message(self):
        return self.transportP1Queue.get()
    
    def putTransportP1Message(self,message):
        self.transportP1Queue.put(message)
    
    def getTransportP2Message(self):
        return self.transportP2Queue.get()
    
    def putTransportP2Message(self,message):
        self.transportP2Queue.put(message)
    
    def putConnectMessage(self,message):
        self.connectQueue.put(message)
    
    def getConnectMessage(self):
        return self.connectQueue.get()

    def putBroadCastMessage(self,message):
        self.broadCastMessage.put(message)
    
    def getBroadCastMessage(self):
        return self.broadCastMessage.get()    
    
    def assigntoSkill(self, _skillName):
        return self.skillName[_skillName]
    
    def createNewUUID(self):
        return uuid.uuid4()
        
    def _receiveMessage_(self, jMessage):
        try:
            _skillName = jMessage["frame"]["receiver"]["role"]["name"]
            return self.assigntoSkill(_skillName).receiveMessage(jMessage)
        except:
            for skillName in self.skillName.keys():
                return self.assigntoSkill(skillName).receiveMessage(jMessage)

    
    def fetchDataAdaptor(self,ob_Message):
        try:
            receiverId = ob_Message["frame"]["receiver"]["id"]
            if receiverId in self.pyAAS.mqttGateWayEntries:
                return "MQTT"
            if receiverId in self.pyAAS.httpEndPointsDict:
                return "RESTAPI"
            elif receiverId in self.pyAAS.coapEndPointsDict:
                return "COAP"
            else :
                return "Empty"
        except Exception as E:
            return "Empty"

    def sendOutBoundMessage(self, ob_Message):
        try:
            adaptorType = self.fetchDataAdaptor(ob_Message)
            if (adaptorType != "Empty"):
                self.AASendPointHandlerObjects[adaptorType].dispatchMessage(ob_Message)
        except Exception as E:
            self.putIbMessage(ob_Message)

    def __sendTransportMessage_(self,oT_Message):
        targetAdaptor = self.fetchDataAdaptor(oT_Message)
        if (targetAdaptor != "Empty"):
            if targetAdaptor == "RESTAPI" :
                try :
                    targetResponse = self.AASendPointHandlerObjects["RESTAPI"].dispatchMessage(oT_Message)
                    if targetResponse:
                        pass
                    else:
                        time.sleep(2)
                        self.putTransportP1Message(oT_Message)
                except Exception as E:
                    time.sleep(2)
                    self.putTransportP1Message(oT_Message)
            elif targetAdaptor == "COAP":
                try :
                    targetResponse = self.AASendPointHandlerObjects["COAP"].dispatchMessage(oT_Message)
                    if targetResponse:
                        pass
                    else:
                        time.sleep(2)
                        self.putTransportP1Message(oT_Message)
                except Exception as E:
                    time.sleep(2)
                    self.putTransportP1Message(oT_Message)
            else:
                targetResponse = self.AASendPointHandlerObjects["MQTT"].dispatchMessage(oT_Message)
            
    def __sendTransportP1Message_(self,oT_P1Message):
        targetAdaptor = self.fetchDataAdaptor(oT_P1Message)
        if (targetAdaptor != "Empty"):
            if  targetAdaptor == "RESTAPI":
                try :
                    targetResponseP1 = self.AASendPointHandlerObjects["RESTAPI"].dispatchMessage(oT_P1Message)
                    if targetResponseP1:
                        pass
                    else:
                        time.sleep(2)
                        self.putTransportP2Message(oT_P1Message)
                except Exception as E:
                    time.sleep(2)
                    self.putTransportP2Message(oT_P1Message)
                      
            elif targetAdaptor == "COAP":
                try :
                    targetResponseP1 = self.AASendPointHandlerObjects["COAP"].dispatchMessage(oT_P1Message)
                    if targetResponseP1:
                        pass
                    else:
                        time.sleep(2)
                        self.putTransportP2Message(oT_P1Message)
                except Exception as E:
                    time.sleep(2)
                    self.putTransportP2Message(oT_P1Message)   
    

    def __sendTransportP2Message_(self,oT_P2Message):
        targetAdaptor = self.fetchDataAdaptor(oT_P2Message)
        if (targetAdaptor != "Empty"):
            if targetAdaptor == "RESTAPI":
                try :
                    self.AASendPointHandlerObjects["RESTAPI"].dispatchMessage(oT_P2Message)
                except Exception as E:
                    pass
            else:
                try :
                    self.AASendPointHandlerObjects["COAP"].dispatchMessage(oT_P2Message)
                except Exception as E:
                    pass     
                   
    def __processCprotMessage__(self,cpMessage):
        try:
            data =  cpMessage["data"]
            timeStamp = cpMessage["timestamp"]
            Id = data["frame"]["sender"]["id"]
            if Id not in list(self.pyAAS.connectBotsDict.keys()):
                botDict = {"id" :Id,"timeStamp" : timeStamp, "iframesList" : [] }
                self.pyAAS.connectBotsDict[Id] = botDict
            else:
                self.pyAAS.connectBotsDict[Id]["timeStamp"] = timeStamp
            self.connectHeader = {"content-type": "application/json"}
            
            for Im in data["interactionElements"]:
                jsonData = json.loads(Im)

                if "receiver" not in list(jsonData["frame"].keys()):
                    self.putBroadCastMessage(jsonData)
                
                elif (jsonData["frame"]["receiver"]["id"] == "VWS_RIC"):
                    if  jsonData["frame"]["type"] == "register" :
                        descriptorData = json.loads(jsonData["interactionElements"][0])
                        descUrl = "http://localhost:9021/api/v1/registry/"+descriptorData["idShort"]
                        _putRegistryResponse = requests.put(descUrl,data=json.dumps(descriptorData),headers=self.connectHeader)
                        self.pyAAS.service_logger.info("AASID : "+ descriptorData["idShort"] +_putRegistryResponse.text)
                else:
                    _receiver = data["frame"]["receiver"]["id"]
                    if _receiver in list(self.pyAAS.connectBotsDict.keys()):
                        self.pyAAS.connectBotsDict[_receiver]["iframesList"].append(Im)
                    else:
                        self.putTransportMessage(jsonData)   
                
        except Exception as E:
            self.pyAAS.service_logger.info("ERROR OCCURED " + str(E))
    
    def __processbroadCastMessage__(self,bcMessage):
        self.pyAAS.service_logger.info("A new broadcasting message has arrived")
        restAPIThread = threading.Thread(target=self.AASendPointHandlerObjects["RESTAPI"].dispatchBroadCastMessage(bcMessage))
        restAPIThread.start()
        MQTTThread = threading.Thread(target=self.AASendPointHandlerObjects["MQTT"].dispatchBroadCastMessage(bcMessage))
        MQTTThread.start()
        coapThread = threading.Thread(self.AASendPointHandlerObjects["COAP"].dispatchBroadCastMessage(bcMessage))
        coapThread.start() 
        
        for key in list(self.pyAAS.connectBotsDict.keys()):
            self.pyAAS.connectBotsDict[key]["iframesList"].append(bcMessage)