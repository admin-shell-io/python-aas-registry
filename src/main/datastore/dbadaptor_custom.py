'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

try:
    from utils.utils import EndpointObject
except ImportError:
    from main.utils.utils import EndpointObject
try:
    from datastore.aas_database_server import AAS_Database_Server
except ImportError:
    from main.datastore.aas_database_server import AAS_Database_Server

class DB_ADAPTOR(object):
    '''
    classdocs
    '''

    def __init__(self,pyAAS):
        '''
        Constructor
        '''
        self.pyAAS = pyAAS
        self.AAS_Database_Server = AAS_Database_Server(self.pyAAS)   

        self.mongocol_aas = self.AAS_Database_Server.createNewDataBaseColumn("aas_"+self.pyAAS.AASID)
        self.mongocol_Messages = self.AAS_Database_Server.createNewDataBaseColumn("messages_"+self.pyAAS.AASID)
        self.mongocol_aasDesc = self.AAS_Database_Server.createNewDataBaseColumn("aasDesc"+self.pyAAS.AASID)
        self.mongocol_aasDescEndPoint = self.AAS_Database_Server.createNewDataBaseColumn("aasDescEndPoint"+self.pyAAS.AASID)
        self.mongocol_submodelDesccriptors =self.AAS_Database_Server.createNewDataBaseColumn("submodelDesccriptors"+self.pyAAS.AASID)
        
        
## AAS related Entries

    def getAASParams(self,aas):
        params = {}
        try:
            params["aasId"] = aas["assetAdministrationShells"][0]["identification"]["id"]
        except:
            params["aasId"] = ""
        
        try:
            params["aasetId"] = aas["assets"][0]["identification"]["id"]
        except:
            params["aasetId"] = ""
        
        try:
            params["idShort"] = aas["assetAdministrationShells"][0]["idShort"]
        except:
            params["idShort"] = ""
        return params

    def getAAS(self,data):
        returnMessageDict = {}
        try:
            query = { "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] }
            AAS = self.AAS_Database_Server.find(self.mongocol_aas,query)
            if AAS["message"] ==  "failure":
                returnMessageDict = {"message":["No Asset Administration Shell with passed id found"],"status":200}
            elif AAS["message"] ==  "success":
                returnMessageDict = {"message": [AAS["data"]["data"]],"status":200}
            else:
                returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Server Error"+str(E)],"status":500}
        return returnMessageDict
    
    def deleteAASByID(self,data):
        returnMessageDict = {}
        query = { "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] }
        try:
            deleteResult = self.AAS_Database_Server.remove(self.mongocol_aas,query)
            if (deleteResult["message"] == "failure"):
                returnMessageDict = {"message" : ["No Asset Administration Shell with passed id found"], "status": 200}
            elif (deleteResult["message"] == "success"):
                returnMessageDict = {"message" : ["The Asset Administration Shell was deleted successfully"], "status": 200}
            else:
                returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Server Error"+str(E)],"status":500}
        return returnMessageDict
    
    def putAAS(self,data):
        returnMessageDict = {}
        aas = data["updateData"]
        try:
            response = self.deleteAASByID(data)
            if (response["message"][0] == "No Asset Administration Shell with passed id found"):
                _insertdata = self.getAASParams(aas)
                _insertdata["data"] = aas
                self.AAS_Database_Server.insert_one(self.mongocol_aas,_insertdata)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfully renewed"],"status":200}
            elif(response["message"][0] == "The Asset Administration Shell was deleted successfully"):
                _insertdata = self.getAASParams(aas)
                _insertdata["data"] = aas
                self.AAS_Database_Server.insert_one(self.mongocol_aas,_insertdata)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfull"],"status":200}
            else:
                returnMessageDict = response
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict
    

    def getAAsSubmodelsbyId(self,aasId,submodelId):
        if (submodelId == "StatusResponse"):
            return {"message":[self.pyAAS.aasConfigurer.submodel_statusResponse_path],"status":200}
        
        returnMessageDict = {}
        resultList = []
        resultListTemp = []

        try:
            aasSubmodels = self.mongocol_aas.find({
                                        "assetAdministrationShells.0.identification.id": aasId, 
                                    }, 
                                    { 
                                        "submodels" : 1.0,
                                        "_id" : 0.0
                                    }
                                    )
            
            for aas in aasSubmodels:
                for submodel in aas["submodels"]:
                    resultListTemp.append(submodel)

            if len(resultListTemp) == 0:
                message = []
                message.append("E007. internal-error")
                message.append("Currently no AAS with the given ID has registered with the registry")
                returnMessageDict = {"message":message,"status":400}
                
            else :
                for submodel in resultListTemp:
                    if submodel["idShort"] == submodelId:
                        resultList.append(submodel)
                if len(resultList) == 0:
                    message = []
                    message.append("E007. internal-error")
                    message.append("The AAS does not contain the specified submodel")
                    returnMessageDict = {"message":message,"status":400}
                else:
                    returnMessageDict = {"message": resultList,"status":200}
                
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict 


## Message Level Entries

    def saveNewConversationMessage(self,coversationId,messageType,messageId,message):
        message = {
                    "messageType" :messageType,
                    "message_Id" :messageId,
                    "message" :message
                }
        returnMessageDict = {}
        try:
            response = self.AAS_Database_Server.insert_one(self.mongocol_Messages, message)
            returnMessageDict = {"message": ["The details are successfully recorded"],"status":200}            
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict    

    
    def getMessageCount(self):
        try:
            messages = self.AAS_Database_Server.find(self.mongocol_Messages,{})
            if (messages["message"] == "success"):
                returnMessageDict = {"message": [len(messages["data"])],"status":200}
            else:
                returnMessageDict = {"message": [0],"status":200}
        except:
            returnMessageDict = {"message": [0],"status":500}
        return returnMessageDict   

## Message Level Entries


#### AASDescritpors Registry Start ######################

    def getDescParams(self,descData):
        params = {}
        try:
            params["aasId"] = descData["identification"]["id"]
        except:
            params["aasId"] = ""
        
        try:
            params["aasetId"] = descData["globalAssetId"]["keys"][0]["value"]
        except:
            params["aasetId"] = ""
        
        try:
            params["idShort"] = descData["idShort"]
        except:
            params["idShort"] = ""
        return params
    
    def getAllDesc(self,data):
        data = data
        returnMessageDict = {}
        resultDict = {}
        try:
            aasDescriptors = self.AAS_Database_Server.find(self.mongocol_aasDesc,{})
            if (aasDescriptors["message"] == "success"):
                i = 0
                for aasdesc in aasDescriptors["data"]:
                    resultDict[i] = aasdesc["data"]
                    i = i + 1
                returnMessageDict = {"message":[resultDict],"status":200}
            elif (aasDescriptors["message"] == "failure"):
                returnMessageDict = {"message":["No Asset Administration Shell descriptors are yet registered"],"status":200}
            else :
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

##### Get a New Descriptor Start ###################

    def getAASDescByID(self,data):
        returnMessageDict = {}
        try:
            aasDescriptors = self.AAS_Database_Server.find(self.mongocol_aasDesc,{ "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] })
            if (aasDescriptors["message"] == "success"):
                returnMessageDict = {"message":[aasDescriptors["data"]["data"]],"status":200}
            elif (aasDescriptors["message"] == "failure"):
                returnMessageDict = {"message":["No Asset Administration Shell with passed identifier found"],"status":200}
            else :
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

##### Get a New Descriptor End ###################

##### Delete a New Descriptor Start ###################

    def deleteAASDescById(self,data):
        returnMessageDict = {}
        try:
            deleteResult = self.AAS_Database_Server.remove(self.mongocol_aasDesc,{ "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] })
            if (deleteResult["message"] == "failure"):
                returnMessageDict = {"message" : ["No Asset Administration Shell with passed identifier found"], "status": 200}
            elif (deleteResult["message"] == "success"):
                returnMessageDict = {"message" : ["The Asset Administration Shell Descriptor was deleted successfully"], "status": 200}
            else:
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

##### Delete a New Descriptor End ###################

##### Put a New Descriptor Start ###################

    def putAASDescByID(self,data):
        returnMessageDict = {}
        descData = data["updateData"]
        descInsertData = self.getDescParams(descData)
        descInsertData["data"] = descData
        try:
            response = self.deleteAASDescById(data)
            epO = EndpointObject(self.pyAAS)
            httpEdpStatus = True
            if (response["message"][0] == "No Asset Administration Shell with passed identifier found"):
                self.AAS_Database_Server.insert_one(self.mongocol_aasDesc,descInsertData)
                query = self.getDescriptorIndexData(descData) 
                httpEdpStatus = epO.insert(descData,query)
                returnMessageDict = {"message" : ["The Asset Administration Shell's descriptor registration is successfull"],"status":200}
            elif(response["message"][0] == "The Asset Administration Shell Descriptor was deleted successfully"):
                self.AAS_Database_Server.insert_one(self.mongocol_aasDesc,descInsertData)
                query = self.getDescriptorIndexData(descData) 
                httpEdpStatus = epO.insert(descData,query)
                returnMessageDict = {"message" : ["The Asset Administration Shell's descriptor registration is successfully renewed"],"status":200}
            else:
                returnMessageDict = response
            if (not httpEdpStatus):
                query = self.getDescriptorIndexData(descData)
                deleteResult = self.AAS_Database_Server.remove("aasDescEndPointVWS_RIC",{ "$or": [ { "aasId":query["aasId"] }, { "aasetId":query["aasId"]},{"idShort":query["aasId"]} ] })
                query["endpoint"] = ""
                query["ASYNC"] = "Y" 
                self.insertDescriptorEndPoint(query)
                self.pyAAS.mqttGateWayEntries.add(descData["identification"]["id"])
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict    

    def getSubmodelDescsByAASId(self,data):
        returnMessageDict = {}
        resultDict = {}
        try:
            aasDescriptors = self.AAS_Database_Server.find(self.mongocol_aasDesc,{ "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] })
            if (aasDescriptors["message"] == "success"):
                i = 0
                for submodelDesc in aasDescriptors["data"]["data"]["submodelDescriptors"]:
                    resultDict[i] = submodelDesc
                    i = i + 1
                returnMessageDict = {"message":[resultDict],"status":200}
            elif (aasDescriptors["message"] == "failure"):
                returnMessageDict = {"message":["No Asset Administration Shell with passed identifier found"],"status":200}
            else :
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict


#===============================================================================
# ##### Put a New Descriptor End ###################
# 
# #### AASDescritpors Registry End ######################    
#===============================================================================

    
    def getDescriptorIndexData(self,aasD):
        try:
            aasId  = aasD["identification"]["id"]
        except:
            aasId = ""
        try:
            aasetId  = aasD["globalAssetId"]["keys"][0]["value"]
        except:
            aasetId = ""
        try:
            idShort  = aasD["idShort"]
        except:
            idShort = ""
        descQuery = {"aasId" : aasId, "aasetId":aasetId, "idShort" : idShort}
        return descQuery
        
    def getSubmodelDescByID(self,data):
        returnMessageDict = {}
        submodelId =data["submodelId"]
        try:
            response = self.getAASDescByID(data)
            if (response["status"] == 200):
                present = False
                for submodelDesc in response["message"][0]["submodelDescriptors"]:
                    if submodelDesc["idShort"] == submodelId:
                        returnMessageDict = {"message" : [submodelDesc], "status": 200}
                        present = True
                if (not present):
                    returnMessageDict = {"message" : ["Submodel with passed id not found"], "status": 200}
            else:
                returnMessageDict = response
        except Exception as E:
            self.pyAAS.serviceLogger.info()
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

    def putSubmodelDescByID(self,data):
        try:
            returnMessageDict = {}
            descData = data["updateData"]
            response1 = self.getSubmodelDescByID(data)
            if (response1["status"] == 200):
                response2 = self.deleteSubmodelDescByID(data)
                if (response2["status"] == 200):
                    response3 = self.getAASDescByID(data) 
                    if (response3["status"] == 200):
                        aasDescdataNew = response3["message"][0]
                        aasDescdataNew["submodelDescriptors"].append(descData)
                        response4 = self.putAASDescByID({"updateData":aasDescdataNew,"aasId":data["aasId"]})
                        if (response4["status"] == 200):
                            returnMessageDict = {"message" : ["The Submodel descriptor was successfully renewed"],"status":200}
                        else :
                            returnMessageDict = response4
                    else:
                        returnMessageDict = response3
                else:
                    returnMessageDict = response2 
            elif response1["status"] == 400:
                response5 = self.getAASDescByID(data) 
                if (response5["status"] == 200):
                    aasDescdataNew1 = response5["message"][0]
                    aasDescdataNew1["submodelDescriptors"].append(descData)
                    response6 = self.putAASDescByID({"updateData":aasDescdataNew1,"aasId":data["aasId"]})
                    if (response6["status"] == 200):
                        returnMessageDict = {"message" : ["The Submodel descriptor was created successfully"],"status":200}
                    else :
                        returnMessageDict = response6
            else:
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        return returnMessageDict

    def deleteSubmodelDescByID(self,data):
        returnMessageDict = {}
        submodelId = data["submodelId"]
        aasId = data["aasId"]
        try:
            response = self.getAASDescByID(data)
            if (response["status"] == 200):
                aasDescData = response["message"][0]
                aasSubmodelDescData = response["message"][0]["submodelDescriptors"]
                i = 0
                present = False
                for submodelDesc in response["message"][0]["submodelDescriptors"]:
                    if submodelDesc["idShort"] == submodelId:
                        del aasSubmodelDescData[i]
                        present = True
                        break
                    i = i + 1
                if (not present):
                    returnMessageDict = {"message" : ["Submodel Descriptor with passed id not found"], "status": 400}
                else:
                    aasDescData["submodelDescriptors"] = aasSubmodelDescData
                    response2 = self.putAASDescByID({"updateData" :aasDescData,"aasId":aasId})
                    if response2["status"] == 200:
                        returnMessageDict = {"message" : ["The Submodel Descriptor was successfully unregistered"], "status": 200}
                    else:
                        returnMessageDict = response2
            else:
                returnMessageDict = response
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        return returnMessageDict    
    
    def insertDescriptorEndPoint(self,data):
        try:
            self.AAS_Database_Server.insert_one(self.mongocol_aasDescEndPoint,data)
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
    
    def deleteDescriptorEndPoint(self,queryI):
        try:
            self.AAS_Database_Server.remove(self.mongocol_aasDescEndPoint,queryI)
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))        
        
    def getDescriptorEndPoint(self):
        returnMessageDict = {}
        try:
            query = { }
            descriptorEndpoint = self.AAS_Database_Server.find(self.mongocol_aasDescEndPoint,query)            
            returnMessageDict = {"message": descriptorEndpoint["data"],"status":200}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict        


######### Submodel Registry API Services Start###############################


    def getSubmodelDescParams(self,submodelDescData):
        params = {}
        try:
            params["submodelId"] = submodelDescData["identification"]["id"]
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            params["submodelId"] = ""
                
        try:
            params["idShort"] = submodelDescData["idShort"]
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            params["idShort"] = ""
        return params

    def getSubmodelDescriptors(self,data):
        data = data
        returnMessageDict = {}
        resultDict = {}
        try:
            submodelDescriptors = self.AAS_Database_Server.find(self.mongocol_submodelDesccriptors,{})
            if (submodelDescriptors["message"] == "success"):
                i = 0
                for submodeldesc in submodelDescriptors["data"]:
                    resultDict[i] = submodeldesc["data"]
                    i = i + 1
                returnMessageDict = {"message":[resultDict],"status":200}
            elif (submodelDescriptors["message"] == "failure"):
                returnMessageDict = {"message": ["No submodel shell descriptors are yet registered"],"status":200}

        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

    def getSubmodelDescriptorsById(self,data):
        returnMessageDict = {}
        query = { "$or": [ { "submodelId":data["submodelId"] },{"idShort":data["submodelId"]} ] }
        try:
            submodelDescriptors = self.AAS_Database_Server.find(self.mongocol_submodelDesccriptors,query)
            if submodelDescriptors["message"] == "failure":
                returnMessageDict = {"message":["No submodel descriptor with the passed identifier found"],"status":200}
            elif submodelDescriptors["message"] == "success":
                returnMessageDict = {"message": [submodelDescriptors["data"]["data"]],"status":200}
            else:
                returnMessageDict =  {"message": ["Unexpected Internal Server Error"],"status":500}
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Server Error" + str(E)],"status":500}
        return returnMessageDict   
   
    def putSubmodelDescriptorsById(self,data):
        returnMessageDict = {}
        descData = data["updateData"]
        submodeldescInsertData = self.getSubmodelDescParams(descData)
        submodeldescInsertData["data"] = descData
        try:
            response = self.deleteSubmodelDescriptorsById(data)
            if (response["message"][0] == "The submodel Descriptor is successfully unregistered"):
                self.AAS_Database_Server.insert_one(self.mongocol_submodelDesccriptors,submodeldescInsertData)
                returnMessageDict = {"message" : ["The submodel descriptor successfully renewed"],"status":200}
            elif(response["message"][0] == "The submodel descriptor with passed identifier not found"):
                self.AAS_Database_Server.insert_one(self.mongocol_submodelDesccriptors,submodeldescInsertData)
                returnMessageDict = {"message" : ["The submodel descriptor is successfully registered"],"status":200}
            else:
                returnMessageDict = response
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Server Error" + str(E)],"status":500}
        return returnMessageDict       
   
    def deleteSubmodelDescriptorsById(self,data):
        returnMessageDict = {}
        try:
            deleteResult = self.AAS_Database_Server.remove(self.mongocol_submodelDesccriptors,{ "$or": [ { "submodelId":data["submodelId"] }, { "idShort":data["submodelId"]} ] })
            if (deleteResult["message"] == "failure"):
                returnMessageDict = {"message" : ["The submodel descriptor with passed identifier not found"], "status": 200}
            elif (deleteResult["message"] == "success"):
                returnMessageDict = {"message" : ["The submodel Descriptor is successfully unregistered"], "status": 200}
            else:
                returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error" + str(E)], "status":500}
        return returnMessageDict

######### Submodel Registry API Services End ###############################


   
if __name__ == "__main__":
    dba = DB_ADAPTOR()
    dba.getAAS()