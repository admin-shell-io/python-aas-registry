'''
Copyright (c) 2021-2022 OVGU LIA
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
from datetime import datetime,timedelta
from requests.utils import unquote
from flask_restful import Resource,request
from flask import render_template,Response,make_response


try:
    from utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse
except ImportError:
    from main.utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse
#

#### AAS Descriptor Information Start##############

## All AAS ShellDescriptors  
class AASDescriptors(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self):
        try:
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData"},"method":"getAllDesc"})
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)

# A specific AAS Descriptor
class AASDescriptorsbyId(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self,aasId):
        try:
            escapeId = unquote(aasId)
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData","aasId":escapeId},"method":"getAASDescByID"})            
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)
    
    def getDescParams(self,descData):
        params = {"aasId":"","aasetId":"","idShort":""}
        try:
            params["aasId"] = descData["identification"]["id"]
        except :
            pass
        
        try:
            params["aasetId"] = descData["assets"][0]["identification"]["id"]
        except :
            pass
        
        try:
            params["idShort"] = descData["idShort"]
        except :
            pass
        return params
    
    def put(self,aasId):
        descValid = DescriptorValidator(self.pyAAS)
        escapeId = unquote(aasId)
        try:
            data = request.json
            if "interactionElements" in data:
                return self.pyAAS.skillInstanceDict["RegistryHandler"].restAPIHandler(data)
            else:
                if(descValid.valitdateAASDescriptor(data)):
                    descParams = self.getDescParams(data)
                    if (escapeId == descParams["aasId"] or escapeId == descParams["aasetId"] or escapeId == descParams["idShort"] ):
                        edm = ExecuteDBModifier(self.pyAAS)
                        dataBaseResponse = edm.executeModifer({"data":{"updateData":data,"aasId":escapeId},"method":"putAASDescByID"})              
                        return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
                    else:
                        return make_response("TThe aas-identifier in the uri and in descriptor do not match",500)
                else :
                    return make_response("The syntax of the passed Asset Administration Shell descriptor is not valid or malformed request",500)
        except Exception as E:
            print(str(E))
            return make_response("Unexpected Internal Server Error",500)
        
    def delete(self,aasId):
        escapeId = unquote(aasId)
        try:
            edm = ExecuteDBModifier(self.pyAAS)
            dataBaseResponse = edm.executeModifer({"data":{"updateData":"emptyData","aasId":escapeId},"method":"deleteAASDescById"})              
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)

# Submodel Descriptors of a specific AAS Descriptor
class AASbyIdSubmodelDescriptors(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self,aasId):
        try:
            escapeId = unquote(aasId)
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData","aasId":escapeId},"method":"getSubmodelDescsByAASId"})
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)
 

#### AAS Descriptor Information End##############

#### Submodel Descriptor Information Start##############

# All Submodel Descriptors
class SubModelDescriptors(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self):
        try:
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData"},"method":"getSubmodelDescriptors"})
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)

# A specific Submodel Descriptor
class SubModelDescriptorsbyId(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS

    def getSubmodelDescriptorParams(self,descData):
        params = {"identificationId":"","idShort":""}
        try:
            params["identificationId"] = descData["identification"]["id"]
        except :
            pass

        try:
            params["idShort"] = descData["idShort"]
        except:
            pass
        return params
        
    def get(self,submodelId):
        try:
            escapeId = unquote(submodelId)
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData","submodelId":escapeId},"method":"getSubmodelDescriptorsById"})
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500) 

    def delete(self,submodelId):
        try:
            escapeId = unquote(submodelId)            
            edm = ExecuteDBModifier(self.pyAAS)
            dataBaseResponse = edm.executeModifer({"data":{"updateData":"emptyData","submodelId":escapeId},"method":"deleteSubmodelDescriptorsById"})              
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)       

    def put(self,submodelId):
        try:
            escapeId = unquote(submodelId)
            descValid = DescriptorValidator(self.pyAAS)            
            data = request.json
            if "interactionElements" in data:
                pass
            else:
                message = {"submodelDescriptors":[data]}
                if(descValid.valitdateSubmodelDescriptor(message)):
                    descParams = self.getSubmodelDescriptorParams(data)
                    if (escapeId == descParams["identificationId"]  or escapeId == descParams["idShort"] ):
                        edm = ExecuteDBModifier(self.pyAAS)
                        dataBaseResponse = edm.executeModifer({"data":{"updateData":data,"submodelId":escapeId},"method":"putSubmodelDescriptorsById"})            
                        return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
                    else:
                        return make_response("The submodel-identifier in the uri and in descriptor do not match",500)  
                else :
                    return make_response("The syntax of the passed submodel descriptor is not valid or malformed request",500)
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)         

#### Submodel Descriptor Information End##############


#### Connect Protocol server for AASx Server Start###########
class HandleConnectProtocol(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def post(self):
        heartBeat = request.json
        try:
            messageType = heartBeat["frame"]["type"]
            if (messageType == "HeartBeat"):
                timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                data = {"timestamp":timestamp,"data":heartBeat}
                self.pyAAS.msgHandler.putConnectMessage(data)
                _senderId = heartBeat["frame"]["sender"]["identification"]["id"]
                self.pyAAS.aasBotsDict[_senderId] = timestamp
                cResponse = ConnectResponse(self.pyAAS)
                _iframedata = cResponse._createNewIframeData(_senderId,"ksks") 
                if _senderId in list(self.pyAAS.connectBotsDict.keys()):
                    for iMessage in  self.pyAAS.connectBotsDict[_senderId]["iframesList"]:
                        _iframedata["interactionElements"].append(json.dumps(iMessage))
                    self.pyAAS.connectBotsDict[_senderId]["iframesList"].clear()
                return make_response(_iframedata,200)
            else:
                return make_response("Unexpected Internal Server Error",500)
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+ str(E),500)

class HandleConnect(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def post(self):
        return make_response("OK",200)

#### Connect Protocol server for AASx Server End###########

class StatusUI(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self):
        self.pyAAS.aasBotsDict[self.pyAAS.AASID] = (datetime.now()+ timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        return Response(render_template('status.html',connectstatusDict = self.pyAAS.aasBotsDict))
    
    def post(self):
        self.pyAAS.aasBotsDict[self.pyAAS.AASID] = (datetime.now()+ timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        return make_response(self.pyAAS.aasBotsDict,200)

class RefreshUI(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self):
        try:
            self.sendGetDirectory()
            return make_response("OK",200)
        except Exception as E:
            print(str(E))
            
    def sendGetDirectory(self):
        cr = ConnectResponse(self.pyAAS)
        for key in self.pyAAS.connectBotsDict.keys():
            getDirectoryMessage = cr.createRegistrerData(key,"tempCon")
            self.pyAAS.connectBotsDict[key]["iframesList"].append(getDirectoryMessage)

####### RIC Receiver End point Class Start#####################

class RetrieveMessage(Resource):    
    def __init__(self, pyAAS):
        self.pyAAS = pyAAS
        
    def post(self):
        try:
            tMessage = request.json
            _type = tMessage["frame"]["type"]
            if (_type == "HeartBeat"):
                _sender = tMessage["frame"]["sender"]["identification"]["id"]
                _senderidType = tMessage["frame"]["sender"]["identification"]["idType"]
                cr = ConnectResponse(self.pyAAS)
                if _sender in list(self.pyAAS.httpEndPointsDict.keys()):
                    self.pyAAS.aasBotsDict[_sender] = (datetime.now()+ timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
                    restResponse = cr.creatHeartBeatRestResponse(_sender,_senderidType, tMessage["frame"]["conversationId"])
                    return make_response(restResponse,200)
                else:
                    restResponse = cr.createHeartBeatNegativeHTTPResponse(_sender,_senderidType, tMessage["frame"]["conversationId"])
                    return make_response(restResponse,200)                    
            else :
                if "receiver" not in list(tMessage["frame"].keys()):
                    self.pyAAS.msgHandler.putBroadCastMessage(tMessage)
                elif tMessage["frame"]["receiver"]["identification"]["id"] == "VWS_RIC" and tMessage["frame"]["type"] == "register":
                    return make_response(self.pyAAS.skillInstanceDict["RegistryHandler"].restAPIHandler(tMessage),200)
                else:
                    _receiver = tMessage["frame"]["receiver"]["identification"]["id"]
                    if _receiver in list(self.pyAAS.connectBotsDict.keys()):
                        self.pyAAS.connectBotsDict[_receiver]["iframesList"].append(tMessage)
                    else:
                        self.pyAAS.mCount = self.pyAAS.mCount + 1
                        self.pyAAS.idDict[_receiver] = str(datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]
                        self.pyAAS.msgHandler.putTransportMessage(tMessage)
        except Exception as E:
            self.pyAAS.serviceLogger.info("Error noticed." + str(E))
            return make_response("Unexpected Internal Server Error.",500)
        
####### RIC Receiver End point Class End#####################




# Specific Submodel Descriptor  of a specific AAS Descriptor
# Needs to be deprectated
class AASbyIdSubmodelDescriptorbyId(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self,aasId,submodelId):
        try:
            escapeId = unquote(aasId)
            edbR = ExecuteDBRetriever(self.pyAAS)
            dataBaseResponse = edbR.execute({"data":{"updateData":"emptyData","aasId":escapeId,"submodelId":submodelId},"method":"getSubmodelDescByID"})            
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except:
            return make_response("Unexpected Internal Server Error",500)
                
    def put(self,aasId,submodelId):
        descValid = DescriptorValidator(self.pyAAS)
        try:
            escapeId = unquote(aasId)
            data = request.json
            if "interactionElements" in data:
                pass
                #return self.pyAAS.skillInstanceDict["RegistryHandler"].restAPIHandler(data)
            else:
                message = {"submodelDescriptors":data}
                if(descValid.valitdateSubmodelDescriptor(message)):
                    if (submodelId == data["idShort"]):
                        edm = ExecuteDBModifier(self.pyAAS)
                        dataBaseResponse = edm.executeModifer({"data":{"updateData":data,"aasId":escapeId,"submodelId":submodelId},"method":"putSubmodelDescByID"})            
                        return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
                    else:
                        return make_response("The Namespace SubmodelId value and the IdShort value in the data are not matching",500)  
                else :
                    return make_response("The syntax of the passed Asset Administration Shell is not valid or malformed request",200)
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)

    def delete(self,aasId,submodelId):
        try:
            escapeId = unquote(aasId)
            edm = ExecuteDBModifier(self.pyAAS)
            dataBaseResponse = edm.executeModifer({"data":{"updateData":"emptyData","aasId":escapeId,"submodelId":submodelId},"method":"deleteSubmodelDescByID"})              
            return make_response(dataBaseResponse["message"][0],dataBaseResponse["status"])
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),500)



class DescriptorSchema(Resource):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
    
    def get(self,descriptorId):
        try:
            escapeId = unquote(descriptorId) 
            if (escapeId == "shellDescriptor"):
                return make_response(self.pyAAS.aasConfigurer.aasDescSchema,200)
            elif (escapeId == "submodelDescriptor"):
                return make_response(self.pyAAS.aasConfigurer.submodelDescSchema,200)
            else:
                return make_response("Invalid",200)
        except Exception as E:
            return make_response("Unexpected Internal Server Error"+str(E),200)