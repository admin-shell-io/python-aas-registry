'''
Copyright (c) 2021-2022 OVGU LIA
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
        except Exception as e:
            pass
        return aasDescriptor

    def createSubmodelDescriptorElement(self,desc,sumodelDescriptor,submodel):
        try:
            sumodelDescriptor[desc] = submodel[desc]
        except:
            pass
        return sumodelDescriptor
    
    def createDescriptor(self):
        aasxData = self.pyAAS.aasConfigurer.jsonData
        aasDescriptor = {}
        descList = ["idShort","identification","description"]
        for desc in descList:
            aasDescriptor = self.createAASDescriptorElement(desc,aasDescriptor,aasxData)

        ip = self.pyAAS.lia_env_variable["LIA_AAS_ADMINSHELL_CONNECT_IP"]
        port = self.pyAAS.lia_env_variable["LIA_AAS_RESTAPI_PORT_EXTERN"]
        descString = "http://"+ip+":"+port+"/aas/"+self.pyAAS.AASID 
        endpointsList = []
        endpointsList.append({"address": descString,"type": "restapi"})
        endpointsList.append({"address": "http://"+ip+":"+port+"/i40commu","type": "communication"})  
  
        aasDescriptor["endpoints"]  =  endpointsList
        submodelDescList = []
        
        for submodel in aasxData["submodels"]:
            sumodelDescriptor = {}
            for desc in descList:
                sumodelDescriptor = self.createSubmodelDescriptorElement(desc, sumodelDescriptor, submodel)
            sumodelDescriptor = self.createSubmodelDescriptorElement("semanticId", sumodelDescriptor, submodel)
            submodeldescString = descString +"/submodels/"+sumodelDescriptor["idShort"]
            sumodelDescriptor["endpoints"]  = [{
                                        "address": submodeldescString,
                                        "type": "restapi"
                                      }] 
            submodelDescList.append(sumodelDescriptor)
        
        aasDescriptor["submodelDescriptors"] = submodelDescList
        aasDescriptor["assets"] = aasxData["assets"]
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
            for endpoint in aasD["endpoints"]:
                if endpoint["type"] == "communication":
                    URI = endpoint["address"]
                    if URI.split(":")[0] == "http" or URI.split(":")[0] == "https": 
                        self.pyAAS.httpEndPointsDict[aasD["identification"]["id"]] = URI
                    elif URI.split(":")[0] == "coap":
                        self.pyAAS.coapEndPointsDict[aasD["identification"]["id"]] = endpoint["address"]
                    self.pyAAS.dba.deleteDescriptorEndPoint(query)
                    query["endpoint"] = endpoint["address"]
                    query["ASYNC"] = "N"
                    self.pyAAS.dba.insertDescriptorEndPoint(query)
                    return True
            return False    
        except Exception as E:
            return False

class ConnectResponse(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def creatIframeData(self,senderId,coversationId,messageType,protType):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": "ovgu.de/"+protType, 
                            "idType": "IRI"
                        }
                        ]
                    }, 
                    "type": messageType,
                    "messageId": str(uuid.uuid1()), 
                    "sender": {
                        "identification": {
                            "id": "VWS_RIC",
                            "idType": "idShort"
                        }, 
                        "role": {
                            "name": "CoonectProtocolServer"
                            }
                        },
                    "receiver": {
                        "identification": {
                            "id": senderId,
                            "idType": "IRI"
                        }, 
                        "role": {
                            "name": "CoonectProtocolServer"
                            }
                        },                    
                    "replyBy": "RESTHTTP",
                    "replyTo": "RESTHTTP",
                    "conversationId": coversationId
                }
        
        return {"frame":frame, "interactionElements": []}  
      
    def _createNewIframeData(self,senderId,coversationId):
        return self.creatIframeData(senderId,coversationId,"HeartBeatAck","heartbeatAck")
    
    def createRegistrerData(self,senderId,coversationId):
        return self.creatIframeData(senderId,coversationId,"getDirectory","getDirectory")
    