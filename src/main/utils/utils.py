'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


from jsonschema import validate
import uuid

try:
    from utils.i40data import Generic
except ImportError:
    from main.utils.i40data import Generic

class ExecuteDBModifier(object):
    def __init__(self,pyAAS):
        self.instanceId = str(uuid.uuid1())
        self.pyAAS = pyAAS
            
    def executeModifer(self,instanceData):
        self.pyAAS.dataManager.pushInboundMessage({"functionType":1,"instanceid":self.instanceId,
                                                            "data":instanceData["data"],
                                                            "method":instanceData["method"]})
        vePool = True
        while(vePool):
            if (len(self.pyAAS.dataManager.outBoundProcessingDict.keys())!= 0):
                if (self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId] != ""):
                    modiferResponse = self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId]
                    del self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId]
                    vePool = False
        return modiferResponse

class AASDescriptor(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def createAASDescriptorElement(self,desc,aasDescriptor,aasxData):
        try:
            aasDescriptor[desc] = aasxData["assetAdministrationShells"][0][desc]
        except Exception as E:
            aasDescriptor[desc] = None
        return aasDescriptor

    def createSubmodelDescriptorElement(self,desc,sumodelDescriptor,submodel):
        try:
            sumodelDescriptor[desc] = submodel[desc]
        except:
            pass
        return sumodelDescriptor
    
    def createndPoint(self,desc,interface):
        endPoint =    {"protocolInformation":{
                                "endpointAddress" : desc,
                                "endpointProtocol" : "http",
                                        "endpointProtocol": None,
                                        "endpointProtocolVersion": None,
                                        "subprotocol": None,
                                        "subprotocolBody": None,
                                        "subprotocolBodyEncoding": None
                                },
                        "interface": interface
                        }
        return endPoint
    
    
    def createDescriptor(self):
        aasxData = self.pyAAS.aasConfigurer.jsonData
        aasDescriptor = {}
        
        descList = ["idShort","description"]
        for desc in descList:
            aasDescriptor = self.createAASDescriptorElement(desc,aasDescriptor,aasxData)
        try:
            aasDescriptor["identification"] =  aasxData["assetAdministrationShells"][0]["identification"]["id"]
        except:
            aasDescriptor["identification"] = None
            
        ip = self.pyAAS.lia_env_variable["LIA_AAS_ADMINSHELL_CONNECT_IP"]
        port = self.pyAAS.lia_env_variable["LIA_AAS_RESTAPI_PORT_EXTERN"]
        descString = "http://"+ip+":"+port+"/aas/"+self.pyAAS.AASID 
        endpointsList = []

        
        endpointsList.append(self.createndPoint(descString, "AAS-1.0"))
        endpointsList.append(self.createndPoint("http://"+ip+":"+port+"/i40commu","communication"))  
  
        aasDescriptor["endpoints"]  =  endpointsList
        submodelDescList = []
        
        for submodel in aasxData["submodels"]:
            sumodelDescriptor = {}
            for desc in descList:
                sumodelDescriptor = self.createSubmodelDescriptorElement(desc, sumodelDescriptor, submodel)
            
            try:
                sumodelDescriptor["identification"]  = submodel["identification"]["id"]
            except:
                sumodelDescriptor["identification"]  = None
            sumodelDescriptor = self.createSubmodelDescriptorElement("semanticId", sumodelDescriptor, submodel)
            submodeldescString = descString +"/submodels/"+sumodelDescriptor["idShort"]
            sumodelDescriptor["endpoints"]  = [self.createndPoint(submodeldescString,"SUBMODEL-1.0")] 
            submodelDescList.append(sumodelDescriptor)
        
        aasDescriptor["submodelDescriptors"] = submodelDescList
        return aasDescriptor


class DescriptorValidator(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def valitdateAASDescriptor(self,aasDescData):
        try :
            aasDescSchema = self.pyAAS.aasConfigurer.aasDescSchema
            if(not validate(instance = aasDescData, schema= aasDescSchema)):
                return True
            else:
                return False
        except Exception as E:
            return False
    
    def valitdateSubmodelDescriptor(self,submodelDescData):
        try :
            submodelDescSchema = self.pyAAS.aasConfigurer.submodelDescSchema
            if(not validate(instance = submodelDescData, schema= submodelDescSchema)):
                return True
            else:
                return False
        except Exception as E:
            return False

class AASMetaModelValidator(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def valitdateAAS(self,aasData):
        try :
            aasJsonSchema = self.pyAAS.aasConfigurer.aasJsonSchema
            if(not validate(instance = aasData, schema= aasJsonSchema)):
                return True
            else:
                return False
        except Exception as E:
            return False
    
    def valitdateSubmodel(self,submodelData):
        try :
            submodelJsonSchema = self.pyAAS.aasConfigurer.submodelJsonSchema
            if(not validate(instance = submodelData, schema= submodelJsonSchema)):
                return True
            else:
                return False
        except:
            return False

    def valitdateAsset(self,assetData):
        try :
            assetJsonSchema = self.pyAAS.aasConfigurer.assetJsonSchema
            if(not validate(instance = assetData, schema= assetJsonSchema)):
                return True
            else:
                return False
        except:
            return False       

class ExecuteDBRetriever(object):
    def __init__(self,pyAAS):
        self.instanceId = str(uuid.uuid1())
        self.pyAAS = pyAAS
            
    def execute(self,instanceData):
        self.pyAAS.dataManager.pushInboundMessage({"functionType":1,"instanceid":self.instanceId,
                                                            "data":instanceData["data"],
                                                            "method":instanceData["method"]})
        vePool = True
        while(vePool):
            if (len(self.pyAAS.dataManager.outBoundProcessingDict.keys())!= 0):
                if (self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId] != ""):
                    response = self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId]
                    del self.pyAAS.dataManager.outBoundProcessingDict[self.instanceId]
                    vePool = False
        return response

class EndpointObject(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def insert(self,aasD,query):
        try:
            deleteResult = self.pyAAS.dba.AAS_Database_Server.remove("aasDescEndPointVWS_RIC",{ "$or": [ { "aasId":query["aasId"] }, { "aasetId":query["aasId"]},{"idShort":query["aasId"]} ] })
            for endpoint in aasD["endpoints"]:
                if endpoint["interface"] == "communication":
                    protocol = endpoint["protocolInformation"]["endpointProtocol"]
                    if protocol == "http" or protocol == "https": 
                        self.pyAAS.httpEndPointsDict[aasD["identification"]] = endpoint["protocolInformation"]["endpointAddress"]
                        query["endpoint"] = endpoint["protocolInformation"]["endpointAddress"]
                        query["ASYNC"] = "N"                        
                    elif protocol == "coap":
                        self.pyAAS.coapEndPointsDict[aasD["identification"]] = endpoint["protocolInformation"]["endpointAddress"]
                        query["endpoint"] = endpoint["protocolInformation"]["endpointAddress"]
                        query["ASYNC"] = "N"
                    self.pyAAS.dba.insertDescriptorEndPoint(query)
                    return True
            return False    
        except Exception as E:
            return False

class ConnectResponse(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
        self.StatusResponseSM = self.pyAAS.dba.getAAsSubmodelsbyId(self.pyAAS.AASID,"StatusResponse")["message"]        
    
    def creatIframeData(self,senderId,coversationId,messageType,protType):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": "www.admin-shell.io/interaction/"+protType, 
                            "idType": 'IRI'
                        }
                        ]
                    }, 
                    "type": messageType,
                    "messageId": str(uuid.uuid1()), 
                    "sender": {
                        "identification": {
                            "id": "AASpillarbox",
                            "idType": "idShort"
                        }, 
                        "role": {
                            "name": "HeartBeatHandler"
                            }
                        },
                    "receiver": {
                        "identification": {
                            "id": senderId,
                            "idType": "IRI"
                        }, 
                        "role": {
                            "name": "AASHeartBeatHandler"
                            }
                        },
                    "replyBy": 000000,
                    "inReplyTo":"",
                    "conversationId": coversationId
                }
        
        return {"frame":frame, "interactionElements": []}  
      
    def creatHeartBeatRestResponse(self,senderId,_senderidType,coversationId):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": "www.admin-shell.io/interaction/heartbeat", 
                            "idType": "IRI"
                        }
                        ]
                    }, 
                    "type": "HeartBeatAck",
                    "messageId": str(uuid.uuid1()), 
                    "sender": {
                        "identification": {
                            "id": "AASpillarbox",
                            "idType": "idShort"
                        }, 
                        "role": {
                            "name": "HeartBeatHandler"
                            }
                        },
                    "receiver": {
                        "identification": {
                            "id": senderId,
                            "idType": _senderidType
                        }, 
                        "role": {
                            "name": "AASHeartBeatHandler"
                            }
                        },
                    "replyBy": 000000,
                    "inReplyTo":"",  
                    "conversationId": coversationId
                }
        return {"frame":frame, "interactionElements": []}  

    def creatHeartBeatMQTTResponse(self,senderId,_senderidType,coversationId):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": "www.admin-shell.io/interaction/heartbeat", 
                            "idType": "IRI"
                        }
                        ]
                    }, 
                    "type": "HeartBeatAck",
                    "messageId": str(uuid.uuid1()), 
                    "sender": {
                        "identification": {
                            "id": "AASpillarbox",
                            "idType": "idShort"
                        }, 
                        "role": {
                            "name": "HeartBeatHandler"
                            }
                        },
                    "receiver": {
                        "identification": {
                            "id": senderId,
                            "idType":_senderidType
                        }, 
                        "role": {
                            "name": "AASHeartBeatHandler"
                            }
                        },
                    "replyBy": 000000,
                    "inReplyTo":"",
                    "conversationId": coversationId
                }
        return {"frame":frame, "interactionElements": []}     
    
    def createHeartBeatNegativeMQTTResponse(self,senderId,_senderidType, coversationId):
        self.StatusResponseSM[0]["submodelElements"][0]["value"] = "S"
        self.StatusResponseSM[0]["submodelElements"][1]["value"] = "200"
        self.StatusResponseSM[0]["submodelElements"][2]["value"] = "The AAS is not registered, please provide descriptors"        
        returnData = self.creatHeartBeatMQTTResponse(senderId,_senderidType, coversationId)
        returnData["interactionElements"] = self.StatusResponseSM
        return returnData

    def creatHeartBeatCoapResponse(self,senderId,_senderidType, coversationId):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": "www.admin-shell.io/interaction/heartbeat", 
                            "idType": "IRI"
                        }
                        ]
                    }, 
                    "type": "HeartBeatAck",
                    "messageId": str(uuid.uuid1()), 
                    "sender": {
                        "identification": {
                            "id": "AASpillarbox",
                            "idType": "idShort"
                        }, 
                        "role": {
                            "name": "HeartBeatHandler"
                            }
                        },
                    "receiver": {
                        "identification": {
                            "id": senderId,
                            "idType": _senderidType
                        }, 
                        "role": {
                            "name": "AASHeartBeatHandler"
                            }
                        },
                    "replyBy": 000000,
                    "inReplyTo":"",
                    "conversationId": coversationId
                }
        return {"frame":frame, "interactionElements": []}     
    
    def createHeartBeatNegativeCoapResponse(self,senderId,_senderidType, coversationId):
        self.StatusResponseSM[0]["submodelElements"][0]["value"] = "S"
        self.StatusResponseSM[0]["submodelElements"][1]["value"] = "200"
        self.StatusResponseSM[0]["submodelElements"][2]["value"] = "The AAS is not registered, please provide descriptors"        
        returnData = self.creatHeartBeatMQTTResponse(senderId,_senderidType, coversationId)
        returnData["interactionElements"] = self.StatusResponseSM
        return returnData    

    def createHeartBeatNegativeHTTPResponse(self,senderId,_senderidType, coversationId):
        self.StatusResponseSM[0]["submodelElements"][0]["value"] = "S"
        self.StatusResponseSM[0]["submodelElements"][1]["value"] = "200"
        self.StatusResponseSM[0]["submodelElements"][2]["value"] = "The AAS is not registered, please provide descriptors"        
        returnData = self.creatHeartBeatRestResponse(senderId,_senderidType, coversationId)
        returnData["interactionElements"] = self.StatusResponseSM
        return returnData
    
    def _createNewIframeData(self,senderId,coversationId):
        return self.creatIframeData(senderId,coversationId,"HeartBeatAck","heartbeatAck")
    
    def createRegistrerData(self,senderId,coversationId):
        return self.creatIframeData(senderId,coversationId,"getDirectory","getDirectory")