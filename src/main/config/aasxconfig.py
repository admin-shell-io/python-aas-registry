'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


import json
import os.path

try:
    from utils.utils import ExecuteDBModifier,AASDescriptor,ExecuteDBRetriever,AASMetaModelValidator,DescriptorValidator,ConnectResponse
except ImportError:
    from src.main.utils.utils import ExecuteDBModifier,AASDescriptor,ExecuteDBRetriever,AASMetaModelValidator,DescriptorValidator,ConnectResponse


script_dir = os.path.dirname(os.path.realpath(__file__))
repository = os.path.join(script_dir, "../../../config")
dataPath = os.path.join(script_dir, "../../../data")
aas_json__path = os.path.join(repository, "VWS_RIC.json")

enabledState = {"Y":True, "N":False}

class ConfigParser(object):
    def __init__(self,pyAAS):
        self.pyAAS = pyAAS
        self.jsonData = {}
        with open(aas_json__path) as json_file:
            self.jsonData = json.load(json_file)
        with open(os.path.join(repository,"ass_JsonSchema.json")) as json_file_aas:
            self.aasJsonSchema  = json.load(json_file_aas)
        with open(os.path.join(repository,"asset_JsonSchema.json")) as json_file_asset:
            self.assetJsonSchema  = json.load(json_file_asset)
        with open(os.path.join(repository,"submodel_JsonSchema.json")) as json_file_submodel:
            self.submodelJsonSchema  = json.load(json_file_submodel)
        with open(os.path.join(script_dir,"status.json")) as statusFile:
            self.submodel_statusResponse_path  = json.load(statusFile)
        with open(os.path.join(repository,"aasDescSchema.json")) as json_file_aasDesc:
            self.aasDescSchema  = json.load(json_file_aasDesc)
        with open(os.path.join(repository,"submodelDescSchema.json")) as json_file_submodelDesc:
            self.submodelDescSchema  = json.load(json_file_submodelDesc)    
        with open(os.path.join(dataPath,"database.json")) as json_file_dataBase:
            self.dataBaseFile  = json.load(json_file_dataBase)                
    def setAASID(self):
        return self.jsonData["assetAdministrationShells"][0]["idShort"]
    
    def saveToDatabase(self,dataJ):
        with open(os.path.join(dataPath,"database.json"), 'w', encoding='utf-8') as databaseFile:
            json.dump(dataJ, databaseFile, ensure_ascii=False, indent=4)        
  
    def setExternalVariables(self,environ):
        for env_variable in environ.keys():
            try:
                if (env_variable.split("_")[0] == "LIA"):
                    self.pyAAS.lia_env_variable[env_variable] = os.environ[env_variable]
            except Exception as E:
                pass
    
    def updateEndPointDict(self):
        AASDescDataDB = self.pyAAS.dba.getDescriptorEndPoint()
        if (AASDescDataDB["status"] == 200 and type(AASDescDataDB["message"][0]) != str):
            data = AASDescDataDB["message"]
            for entry in data:
                _asyncType = entry["ASYNC"]
                URI = entry["endpoint"]
                if _asyncType == "Y":
                    self.pyAAS.mqttGateWayEntries.add(entry["aasId"])
                else:
                    if URI.split(":")[0] == "http" or URI.split(":")[0] == "https": 
                        self.pyAAS.httpEndPointsDict[entry["aasId"]] = URI
                    elif URI.split(":")[0] == "coap":
                        self.pyAAS.coapEndPointsDict[entry["aasId"]] = URI
             
    def configureAASJsonData(self):
        AASDataDB = self.pyAAS.dba.getAAS({"aasId":self.pyAAS.AASID})
        if (AASDataDB["status"] == 200 and type(AASDataDB["message"][0]) !=str):
            self.jsonData = AASDataDB["message"][0]
            self.updateEndPointDict()
            return True
            
        elif (AASDataDB["message"][0] == "No Asset Administration Shell with passed id found"):
            data = {"updateData" :self.jsonData,"aasId":self.pyAAS.AASID}
            AASDataDB_1 = self.pyAAS.dba.putAAS(data)
            if AASDataDB_1["status"] == 500:
                self.pyAAS.service_logger.info('Status Message ' + AASDataDB_1["message"][0])
                return False
            else:
                aaD = AASDescriptor(self.pyAAS)
                desc = aaD.createDescriptor()
                descdata = {"updateData" :desc,"aasId":self.pyAAS.AASID}
                descResponse = self.pyAAS.dba.putAssetAdministrationShellDescriptorById(descdata)
                
                if (descResponse["status"] == 500):
                    return False
                else:
                    return True
                
        elif (AASDataDB["status"] == 500):
            self.pyAAS.service_logger.info('Error configuring the database ' + AASDataDB["message"][0])
            return False
        
        return False

    def getAASEndPoints(self):
        aasEndpointsList = []
        moduleDict = {"MQTT":".mqtt_endpointhandler","RESTAPI":".restapi_endpointhandler",
                      "COAP":".coap_endpointhandler"}
        for moduleName in moduleDict.keys():
            aasEndpointsList.append({"Name":moduleName,"Module":moduleDict[moduleName]})
        return aasEndpointsList


    def getAssetAccessEndPoints(self):
        IoAdaptorSubmodels = self.getRelevantSubModel("AssetAccessPoints",0)
        AssetAccessEndPointList = []
        moduleDict = {"PLC_OPCUA":".io_plc"}
        try:
            if (not IoAdaptorSubmodels):
                return AssetAccessEndPointList
        except Exception as E:
            for eachAdaptorEntry in IoAdaptorSubmodels["submodelElements"]:
                assetEndPointDict = {}
                assetEndPointDict["Name"] = eachAdaptorEntry["idShort"]
                assetEndPointDict["Module"] = moduleDict[eachAdaptorEntry["idShort"]]
                for entryProperties in eachAdaptorEntry["value"]:
                    propertyList = {}
                    if (entryProperties["idShort"] == "PropertyList"):
                        for propertL in entryProperties["value"]:
                            propertyList[propertL["idShort"]] = propertL["value"]
                        assetEndPointDict["PropertyList"] = propertyList
                    else:
                        assetEndPointDict[entryProperties["idShort"]] = entryProperties["value"]
                AssetAccessEndPointList.append(assetEndPointDict)
            return AssetAccessEndPointList
    
    def GetAAsxSkills(self):
        Skills = self.getRelevantSubModel("Skills",0)
        skillsDict = {}
        if (not Skills):
            pass
        for eachskill in Skills["submodelElements"]:
            skillName = ""
            skill = {}
            for skillDetails in eachskill["value"]: 
                if (skillDetails["idShort"] == "SkillName"):
                    skill[skillDetails["idShort"]] = skillDetails["value"]
                    skillName = skillDetails["value"]
                if (skillDetails["idShort"] == "SkillService"):
                    skill[skillDetails["idShort"]] = skillDetails["value"]
                if (skillDetails["idShort"] == "InitialState"):
                    skill[skillDetails["idShort"]] = skillDetails["value"]
                if (skillDetails["idShort"] == "enabled"):
                    skill[skillDetails["idShort"]] = enabledState[skillDetails["value"]] 
                skillsDict[skillName] = skill
            if (self.checkForOrderExistence(skill)):
                self.pyAAS.productionStepList.append(skillName)
        return skillsDict 

    
    def getRelevantSubModel(self,relIdShort,indexNumber):
        checkVar = True
        if (indexNumber == 0):
            for submodel in self.jsonData["submodels"]:         
                if (submodel["idShort"] == relIdShort):
                    checkVar = False
                    return submodel
        else:
            for submodel in self.jsonData["submodels"]:         
                if (submodel["idShort"][indexNumber:] == relIdShort):
                    checkVar = False
                    return submodel
        if(checkVar):
            return False
        
    def getRelevantSubModelElement(self,submodel,relIdShort,indexNumber):
        checkVar = True
        for submodelElem in submodel["submodelElements"]:         
            if (submodelElem["idShort"][indexNumber:] == relIdShort):
                return submodelElem["value"]
        if(checkVar):
            return False
    
    def GetAAS(self):
        return self.jsonData
    
    
    def getSubModelbyID(self,sbIdShort):
        checkVar = True
        for submodel in self.jsonData["submodels"]:         
            if (submodel["idShort"] == sbIdShort):
                checkVar = False
                return submodel
        if(checkVar):
            return {"message": "Submodel with the given IdShort is not part of this AAS","status": 400}
    
    
    ## Retrieve the Submodel Property list Dict ##########
    
    def getSubmodePropertyDict(self):
        submodelProperetyDict = {}
        submodel = self.getRelevantSubModel("Submodel",-8)
        try:
            if ( not submodel):
                return submodelProperetyDict
        except Exception as E:
            for eachProperty in submodel["submodelElements"]:
                submodelProperetyDict[eachProperty["idShort"]] = eachProperty["value"]
            return submodelProperetyDict
    
    def getSubmodelPropertyList(self):
        submodeList = []

        for submodel in self.jsonData["submodels"]:         
            if (submodel["idShort"][-8:] == "Submodel"):
                submodeList.append(submodel["idShort"][0:-8])
        return submodeList
    
    def getSubmodelPropertyListDict(self):
        submodelPropertyListDict = {}
        i = 0
        for submodel in self.jsonData["submodels"]:         
            if (submodel["idShort"][-8:] == "Submodel"):
                submodel = self.getRelevantSubModel(submodel["idShort"], 0)
                submodelProperetyDict =  {}
                for eachProperty in submodel["submodelElements"]:
                    submodelProperetyDict[eachProperty["idShort"]] = eachProperty["value"]
                status = " "
                if (i == 0):
                    status = " fade show active"
                    i = 1           
                submodelPropertyListDict[submodel["idShort"]] = {
                                                                    "status" : status,
                                                                    "data" : submodelProperetyDict
                                                                  }
        return submodelPropertyListDict
    
    def configureDescriptor(self):
        aasDesc = AASDescriptor(self.pyAAS)
        return aasDesc.createDescriptor()
    
    ## Retrieve all the
    def checkForOrderExistence(self,skill):
        if (skill["InitialState"] == "WaitforNewOrder"):
            return True
        else :
            return False