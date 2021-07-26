'''
Copyright (c) 2021-2022 OVGU LIA
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''
## Not more used need to be refactored or removed

import pymongo
try:
    from utils.utils import EndpointObject
except ImportError:
    from main.utils.utils import EndpointObject

class DB_ADAPTOR(object):
    '''
    classdocs
    '''

    def __init__(self,pyAAS):
        '''
        Constructor
        '''
        self.pyAAS = pyAAS
        self.db_host = self.pyAAS.lia_env_variable['LIA_MONGO_HOST']
        self.db_port = self.pyAAS.lia_env_variable['LIA_MONGO_PORT']
        self.db_user = self.pyAAS.lia_env_variable['LIA_MONGO_USER']
        self.db_password = self.pyAAS.lia_env_variable['LIA_MONGO_PASSWORD']
        self.db_auth_db = self.pyAAS.lia_env_variable['LIA_MONGO_AUTH_DB']
        self.mongoclient = pymongo.MongoClient("mongodb://rovaduser:MDOVLIAD123!@localhost:26018/?authSource=DBNAME1")
        #self.mongoclient = pymongo.MongoClient("mongodb://"+self.db_user+":"+self.db_password+"@"+self.db_host+":"+self.db_port+"/?authSource="+self.db_auth_db)
        
        self.mongodb = self.mongoclient["AASXRegistry_"+self.pyAAS.AASID]
        self.mongocol_aas = self.mongodb["aas_"+self.pyAAS.AASID]
        self.mongocol_Messages = self.mongodb["messages_"+self.pyAAS.AASID]
        self.mongocol_aasDesc = self.mongodb["aasDesc"+self.pyAAS.AASID]
        self.mongocol_aasDescEndPoint = self.mongodb["aasDescEndPoint"+self.pyAAS.AASID]
        
        self.mongocol_submodelDesccriptors = self.mongodb["submodelDesccriptors"+self.pyAAS.AASID]
     
        
## AAS related Entries
    def getAAS(self,data):
        returnMessageDict = {}
        resultList = []

        try:
            AAS = self.mongocol_aas.find({ 
                                        "assetAdministrationShells.0.idShort" : data["aasId"]
                                    },
                                    { 
                                        "_id" : 0.0
                                    })
            for aas in AAS:
                resultList.append(aas)

            if len(resultList) == 0:
                returnMessageDict = {"message":["No Asset Administration Shell with passed id found"],"status":400}
            else :
                returnMessageDict = {"message": resultList,"status":200}
            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict
    
    def deleteAASByID(self,data):
        aasId = data["aasId"]
        returnMessageDict = {}
        try:
            deleteResult = self.mongocol_aas.remove({ 
                                    "assetAdministrationShells.0.idShort" : aasId
                                                })
            if (deleteResult["n"] == 0):
                returnMessageDict = {"message" : ["No Asset Administration Shell with passed id found"], "status": 400}
            else:
                returnMessageDict = {"message" : ["The Asset Administration Shell was deleted successfully"], "status": 200}            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict
    
    def putAAS(self,data):
        returnMessageDict = {}
        aas = data["updateData"]
        try:
            response = self.deleteAASByID(data)
            if (response["status"] == 200):
                self.mongocol_aas.insert_one(aas)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfully renewed"],"status":200}
            elif(response["status"] == 400):
                self.mongocol_aas.insert_one(aas)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfull"],"status":200}
            else:
                returnMessageDict = response
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict
    


## Message Level Entries

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

    def saveSkillMessage(self,skillMessage,messageType):
        returnMessageDict = {}
        self.mongocol_messageType = self.mongodb[messageType]
        try:
            self.mongocol_messageType.insert_one(skillMessage)
            returnMessageDict = {"message": ["The details are successfully recorded"],"status":200}
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict  
    
    def checkforConversationDbExistence(self):
        returnMessageDict = {}
        try:
            resultList = self.mongocol_Messages.find({'coversationId': "AAS_Orders"})
            returnMessageDict = {"message": [int(resultList.count())],"status":200}
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict
    
    def createConversationDataBase(self):
        returnMessageDict = {}
        message = self.checkforConversationDbExistence()
        if (message["status"] == 200):
            if (message["message"] > 0):
                returnMessageDict = {"message": ["Data Already Exisiting."],"status":200}                
                return returnMessageDict
            else:
                return self._createConversationDataBase()
        else :
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        
    def _createConversationDataBase(self):
        returnMessageDict = {}
        baseConversation = {
                    "coversationId":"AAS_Orders", 
                    "messages":   [
                                        {
                                            "messageType" :"Order",
                                            "message_Id" :"OrderId_123",
                                            "message" :{
                                                "frame":  {},
                                                "interactionElements":{}
                                                }
                                        }
                                    ]
                    }
        try:
            self.mongocol_Messages.insert_one(baseConversation)
            returnMessageDict = {"message": ["The conversation database is setup "],"status":200}            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict
    
    def createNewConversation(self,coversationId):
        returnMessageDict = {}
        coversationId = coversationId
        newConversation = {
                "coversationId":coversationId, 
                "messages":   []
            }
        try:
            self.mongocol_Messages.insert_one(newConversation)
            returnMessageDict = {"message": ["The details are successfully recorded"],"status":200}            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict
    
    def saveNewConversationMessage(self,coversationId,messageType,messageId,message):
        message = {
                    "messageType" :messageType,
                    "message_Id" :messageId,
                    "message" :message
                }
        returnMessageDict = {}
        try:
            self.mongocol_Messages.update_one({'coversationId': coversationId},
                                              {"$push": {"messages": message}})
            returnMessageDict = {"message": ["The details are successfully recorded"],"status":200}            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict    

    def getConversationCount(self):
        returnMessageDict = {}
        try:
            result = int(self.mongocol_Messages.find().count())
            returnMessageDict = {"message": [result],"status":200}            
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict  
    
    def getConversationsById(self,coversationId):
        returnMessageDict = {}
        try:
            resultList = []
            message = self.mongocol_Messages.find({'coversationId': coversationId})
            for mg in message:
                resultList.append(mg) 
            if len(resultList) > 0: 
                returnMessageDict = {"message": resultList,"status":200}
            else:
                returnMessageDict = {"message": ["No conversation found"],"status":400}                
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict    
    
    def getMessagebyId(self,messageId,conversationId,messageType):
        try:
            messagesList = self.mongocol_Messages.find({'coversationId': conversationId})
            for message in messagesList:
                for mg in message["messages"]:
                    if (mg["message_Id"] == messageId):
                        returnMessageDict = {"message": [mg["message"]],"status":200}
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict 
            
    def getMessageCount(self):
        count = 0
        try:
            messagesList = self.mongocol_Messages.find()
            for message in messagesList:
                count = count + len (message["messages"])
            returnMessageDict = {"message": [count],"status":200}
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Error"],"status":500}
        return returnMessageDict 

#### AASDescritpors Registry Start ######################
    def getDescParams(self,descData):
        params = {}
        try:
            params["aasId"] = descData["identification"]["id"]
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            params["aasId"] = ""
        
        try:
            params["aasetId"] = descData["assets"][0]["identification"]["id"]
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            params["aasetId"] = ""
        
        try:
            params["idShort"] = descData["idShort"]
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            params["idShort"] = ""
        return params
    
    def getAllDesc(self,data):
        data = data
        returnMessageDict = {}
        resultList = []
        try:
            aasDescriptors = self.mongocol_aasDesc.find({},
                                            { 
                                                "_id" : 0.0
                                            })
            
            for desriptor in aasDescriptors:
                resultList.append(desriptor["data"])

            if len(resultList) == 0:
                returnMessageDict = {"message":["No Asset Administration Shell with passed identifier found"],"status":200}
            else :
                resultDict = {}
                i = 0
                for result in resultList:
                    resultDict[i] = result
                    i = i + 1
                returnMessageDict = {"message": [resultDict],"status":200}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

#### AASDescriptors End ######################


##### AASDescriptorsbyId Start ###############

##### Get a New Descriptor Start ###################

    def getAASDescByID(self,data):
        returnMessageDict = {}
        query = { "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] }
        resultList = []
        try:
            AAS = self.mongocol_aasDesc.find(query,
                                            { 
                                                "_id" : 0.0
                                            })
            for aas in AAS:
                resultList.append(aas["data"])

            if len(resultList) == 0:
                returnMessageDict = {"message":["No Asset Administration Shell with passed identifier found"],"status":200}
            else :
                returnMessageDict = {"message": resultList,"status":200}

        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict

##### Get a New Descriptor End ###################

##### Delete a New Descriptor Start ###################

    def deleteAASDescById(self,data):
        returnMessageDict = {}
        try:
            deleteResult = self.mongocol_aasDesc.remove({ "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] })
            if (deleteResult["n"] == 0):
                returnMessageDict = {"message" : ["No Asset Administration Shell with passed identifier found"], "status": 200}
            else:
                returnMessageDict = {"message" : ["The Asset Administration Shell Descriptor was deleted successfully"], "status": 200}
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
            if (response["message"][0] == "The Asset Administration Shell Descriptor was deleted successfully"):
                self.mongocol_aasDesc.insert_one(descInsertData)
                query = self.getDescriptorIndexData(descData) 
                httpEdpStatus = epO.insert(descData,query)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfully renewed"],"status":200}
            elif(response["message"][0] == "The Asset Administration Shell Descriptor was deleted successfully"):
                self.mongocol_aasDesc.insert_one(descInsertData)
                query = self.getDescriptorIndexData(descData) 
                httpEdpStatus = epO.insert(descData,query)
                returnMessageDict = {"message" : ["The Asset Administration Shell's registration was successfull"],"status":200}
            else:
                returnMessageDict = response
            if (not httpEdpStatus):
                query = self.getDescriptorIndexData(descData) 
                self.deleteDescriptorEndPoint(query)
                query["endpoint"] = descData["identification"]["id"]
                query["ASYNC"] = "Y"
                self.insertDescriptorEndPoint(query)
                self.pyAAS.mqttGateWayEntries.add(descData["identification"]["id"])
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message": ["Unexpected Internal Server Error"],"status":500}
        return returnMessageDict    

    def getSubmodelDescByAASId(self,data):
        returnMessageDict = {}
        resultList = []
        query = { "$or": [ { "aasId":data["aasId"] }, { "aasetId":data["aasId"]},{"idShort":data["aasId"]} ] }
        try:
            AAS = self.mongocol_aasDesc.find(query,
                                            { 
                                                "_id" : 0.0
                                            })
            i = 0 
            for aas in AAS:
                i = i + 1
                for submodeDesc in (aas["data"]["submodelDescriptors"]):
                    resultList.append(submodeDesc)
            if (i == 0):
                returnMessageDict = {"message":["No Asset Administration Shell with passed identifier found"],"status":400}
            else:
                if len(resultList) == 0:
                    returnMessageDict = {"message":["The Asset Administration Shell Descriptors does not have any submodel descriptors"],"status":400}
                else :
                    returnMessageDict = {"message" : [{"submodelDescriptors":resultList}], "status":200}

        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
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
            aasetId  = aasD["assets"][0]["identification"]["id"]
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
            self.mongocol_aasDescEndPoint.insert_one(data)
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
    
    def deleteDescriptorEndPoint(self,queryI):
        try:
            self.mongocol_aasDescEndPoint.remove(queryI)
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))        
        
    def getDescriptorEndPoint(self):
        returnMessageDict = {}
        resultList = []
        try:
            AAS = self.mongocol_aasDescEndPoint.find({},
                                            { 
                                                "_id" : 0.0
                                            })
            
            for aasD in AAS:
                resultList.append(aasD)
            returnMessageDict = {"message": resultList,"status":200}

        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"], "status":500}
        return returnMessageDict        
        



### Submodel Descriptor Registry


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
        resultList = []
        try:
            submodelDescriptors = self.mongocol_submodelDesccriptors.find({},
                                            { 
                                                "_id" : 0.0
                                            })
            
            for desriptor in submodelDescriptors:
                resultList.append(desriptor["data"])

            if len(resultList) == 0:
                returnMessageDict = {"message":["No submodel shell descriptors are yet registered"],"status":200}
            else :
                resultDict = {}
                i = 0
                for result in resultList:
                    resultDict[i] = result
                    i = i + 1
                returnMessageDict = {"message": [resultDict],"status":200}

        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            returnMessageDict = {"message" : ["Unexpected Internal Server Error"+str(E)], "status":500}
        return returnMessageDict

    def getSubmodelDescriptorsById(self,data):
        returnMessageDict = {}
        query = { "$or": [ { "submodelId":data["submodelId"] },{"idShort":data["submodelId"]} ] }
        resultList = []
        try:
            submodelDescriptors = self.mongocol_submodelDesccriptors.find(query,
                                            { 
                                                "_id" : 0.0
                                            })
            for desriptor in submodelDescriptors:
                resultList.append(desriptor["data"])

            if len(resultList) == 0:
                returnMessageDict = {"message":["No submodel descriptor with the passed identifier found"],"status":200}
            else :
                returnMessageDict = {"message": resultList,"status":200}

        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
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
                self.mongocol_submodelDesccriptors.insert_one(submodeldescInsertData)
                returnMessageDict = {"message" : ["The submodel descriptor successfully renewed"],"status":200}
            elif(response["message"][0] == "The submodel descriptor with passed identifier not found"):
                self.mongocol_submodelDesccriptors.insert_one(submodeldescInsertData)
                returnMessageDict = {"message" : ["The submodel descriptor is successfully registered"],"status":200}
            else:
                returnMessageDict = response
        except Exception as E:
            returnMessageDict = {"message": ["Unexpected Internal Server Error" + str(E)],"status":500}
        return returnMessageDict       
   
    def deleteSubmodelDescriptorsById(self,data):
        returnMessageDict = {}
        try:
            deleteResult = self.mongocol_submodelDesccriptors.remove({ "$or": [ { "submodelId":data["submodelId"] }, { "idShort":data["submodelId"]} ] })
            if (deleteResult["n"] == 0):
                returnMessageDict = {"message" : ["The submodel descriptor with passed identifier not found"], "status": 200}
            else:
                returnMessageDict = {"message" : ["The submodel Descriptor is successfully unregistered"], "status": 200}
        except Exception as E:
            returnMessageDict = {"message" : ["Unexpected Internal Server Error" + str(E)], "status":500}
        return returnMessageDict

######### Submodel Registry API Services End###############################


   
if __name__ == "__main__":
    dba = DB_ADAPTOR()
    dba.getAAS()
    