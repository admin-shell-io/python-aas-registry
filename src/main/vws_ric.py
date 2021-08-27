'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import sys
import time
import threading
import logging
import os

from dotenv import load_dotenv
from datetime import  datetime
from importlib import import_module
from dotenv.main import find_dotenv


try:
    from abstract.channel import Channel
except ImportError:
    from main.abstract.channel import Channel

try:
    from datastore.datamanager import DataManager
except ImportError:
    from main.datastore.datamanager import DataManager

try:
    from handlers.messagehandler import MessageHandler
except ImportError:
    from main.handlers.messagehandler import MessageHandler
    
try:
    from config.aasxconfig import ConfigParser
except ImportError:
    from main.config.aasxconfig  import ConfigParser


try:
    from datastore.dbadaptor_custom import DB_ADAPTOR
except ImportError:
    from main.datastore.dbadaptor_custom import DB_ADAPTOR 

try:
    from utils.aaslog import serviceLogHandler,LogList
except ImportError:
    from main.utils.aaslog import serviceLogHandler,LogList

class vws_ric(object):

    def __init__(self):
        self.reset()
        self.endPointmodules = {}
        self.AASendPointHandles = {}
        self.assetaccessEndpointHandlers = {}
        self.aasSkillHandles = {}
        self.AASID = ''
        self.BroadCastMQTTTopic = ''
        self.msgHandler = MessageHandler(self)
        self.skillDetailsDict = {}
        self.skillInstanceDict = {}
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.lia_env_variable = {} 
        self.idDict = {}
        self.mCount = 0
    def reset(self):
        self.channels = {}
        self.io_adapters = {}
        self.AASendPointHandles = {}   
        self.scheduler = None

    def reconfigure(self):
        self.stop()
        self.reset()
        self.configure()
        self.start()
    
    ######## Configure Service Entities ##################
    
    def configureLogger(self):
        
        self.ServiceLogList = LogList()
        self.ServiceLogList.setMaxSize(maxSize= 200)
        
        self.serviceLogger = logging.getLogger(str(self.__class__.__name__) + ' Service Instance' )
        self.serviceLogger.setLevel(logging.DEBUG)
        
        self.commandLogger_handler = logging.StreamHandler()
        self.commandLogger_handler.setLevel(logging.DEBUG)

        self.fileLogger_Handler = logging.FileHandler(self.base_dir+"/logs/vws_ric.LOG")
        self.fileLogger_Handler.setLevel(logging.DEBUG)
        
        self.listHandler_Handler = serviceLogHandler(self.ServiceLogList)
        self.listHandler_Handler.setLevel(logging.DEBUG)
        
        self.Handler_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')

        self.commandLogger_handler.setFormatter(self.Handler_format)
        self.listHandler_Handler.setFormatter(self.Handler_format)
        self.fileLogger_Handler.setFormatter(self.Handler_format)
        
        self.serviceLogger.addHandler(self.commandLogger_handler)
        self.serviceLogger.addHandler(self.listHandler_Handler)
        self.serviceLogger.addHandler(self.fileLogger_Handler)
        
        self.serviceLogger.info('The service Logger is Configured.')
    
    def configureAASConfigureParser(self):
        self.aasConfigurer = ConfigParser(self)
    
    def configureExternalVariables(self):
        load_dotenv(find_dotenv())
        self.aasConfigurer.setExternalVariables(os.environ)
        self.serviceLogger.info('External Variables are configured.')
        
    def configureAASID(self):
        self.AASID = self.aasConfigurer.setAASID()
        self.serviceLogger.info('The AAS ID is configured.')

    def configureInternalVariables(self):
        self.registryAPI = ""
        self.productionSequenceList = []
        self.productionStepList = []
        self.conversationIdList = []
        self.submodelPropertyDict = self.aasConfigurer.getSubmodePropertyDict()
        self.httpEndPointsDict = {}
        self.coapEndPointsDict = {}
        self.connectBotsDict = {}
        self.aasBotsDict = {}
        self.aasBotsDict[self.AASID] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        self.mqttGateWayEntries = set()
    
    def configureDataAdaptor(self):
        self.dba = DB_ADAPTOR(self)

    def configureAASData(self):    
        configStatus = self.aasConfigurer.configureAASJsonData()
        if (configStatus):
            self.serviceLogger.info('The External DB is configured')
        else:
            self.shutDown()
            
    def confiureDataManager(self):
        self.dataManager = DataManager(self)

    def configureEndPoints(self):
        # configure Industrie 4.0 communication drivers
        aasEndPoints = self.aasConfigurer.getAASEndPoints()
        for endPoint in aasEndPoints:
            name = endPoint["Name"]
            module = endPoint["Module"]
            if module not in sys.modules:
                self.endPointmodules[module] = import_module("aasendpointhandlers"+module)
            
            endPoint0 = self.endPointmodules[module].AASEndPointHandler(self,self.msgHandler)
            self.AASendPointHandles[name] = endPoint0

            endPoint0.configure()
        
        self.serviceLogger.info('The AAS I40 End Points are configured')
 
        
    def configurePropertyRefChannels(self,channelRefList):
        # configure the channels
        for channelRefs in channelRefList:
            for channelRef in channelRefs["propertyReferences"]: 
                channel = Channel(self)
                channel.configure(channelRef)
                self.channels[channel.id] = channel
        
        self.serviceLogger.info('The property channels are configured')
        
    def configureAssetAccessPoints(self):
        # configure the IOAdapters
        assetAccessEndPointsList = self.aasConfigurer.getAssetAccessEndPoints()
        for accessEndPointConfig in assetAccessEndPointsList:

            name = accessEndPointConfig["Name"]
            module = accessEndPointConfig["Module"]
            ip = accessEndPointConfig["ipaddress"]
            port = accessEndPointConfig["port"]
            username = accessEndPointConfig["username"]
            password = accessEndPointConfig["password"]
            porpertyList = accessEndPointConfig["PropertyList"]
            
            if module not in sys.modules:
                self.assetmodule = import_module("aesstaccessadapters"+module)
                endPoint0 = self.assetmodule.AsssetEndPointHandler(self,ip,port,username,password,porpertyList)
                self.assetaccessEndpointHandlers[name] = endPoint0
        
        self.serviceLogger.info('The Asset Access points are configured')
       
    def configureSkills(self): 
        #configure skills
        self.skillDetailsDict = self.aasConfigurer.GetAAsxSkills()
        for skill in self.skillDetailsDict.keys():
            skillModule = import_module("." + skill, package="skills")
            skillBaseclass_ = getattr(skillModule, skill)
            skillInstance = skillBaseclass_(self)
            self.skillInstanceDict[skill] = skillInstance
        self.serviceLogger.info('The skills are configured')
    
    def configureSkillWebList(self):
        self.skillListDict = self.skillDetailsDict
        self.skillListWeb = list(self.skillListDict.keys())
        i = 0
        for skillWeb in self.skillListWeb:
            if skillWeb == "ProductionManager":
                del self.skillListWeb[i]
                break
            i = i + 1
            
    def getSubmodelProperties(self):
        self.submodelPropertyDict = self.aasConfigurer.getSubmodePropertyDict() 
        return self.submodelPropertyDict
    
    def getSubmodelPropertyListDict(self):
        self.submodelPropertyListDict = self.aasConfigurer.getSubmodelPropertyListDict()
        return self.submodelPropertyListDict
        
    def getSubmodelList(self):
        self.submodelList = self.aasConfigurer.getSubmodelPropertyList()
        return self.submodelList
    ####### Start Service Entities ################
        
    def startEndPoints(self):
        self.AASendPointHandlerObjects = {}
        for module_name, endPointHandler in self.AASendPointHandles.items():
            try:
                endPointHandler.start(self,self.AASID)
                self.AASendPointHandlerObjects[module_name] = endPointHandler
            except Exception as E:
                self.serviceLogger.info('The AAS end Points are Started' + str(E))
            
        self.serviceLogger.info('The AAS end Points are Started')
        
    def startAssetEndPoints(self):
        self.serviceLogger.info('The Asset end Points are Started')
    
    def startMsgHandlerThread(self):
        msgHandlerThread = threading.Thread(target=self.msgHandler.start, args=(self.skillInstanceDict,self.AASendPointHandlerObjects,))     
        msgHandlerThread.start()
    
        self.serviceLogger.info('The message handler started')
    
   
    def startSkills(self):      
        # Start remaining skills that are part of the skill instance list
        for skill in self.skillInstanceDict.keys():
            skillInstanceTh = threading.Thread(target=self.skillInstanceDict[skill].Start, args=(self.msgHandler, self.skillDetailsDict[skill],))
            skillInstanceTh.start()
        
        self.serviceLogger.info('The Skills are Started')
    
    def startDataManager(self):
        dataManagerThread = threading.Thread(target=self.dataManager.start, args=())     
        dataManagerThread.start()
    
        self.serviceLogger.info('The message handler started')
    
    def configure(self):
        
        self.commList = [] # List of communication drivers
        self.skilLList = [] # List of Skills
        self.skillInstanceList = {} # List consisting of instances of skills

        #configure Service Logger
        self.configureLogger()
        self.serviceLogger.info('Configuring the Service Entities.')
        #configure AASXConfigParser
        self.configureAASConfigureParser() 
        #configure AASID
        self.configureAASID()
        #configure External Variables
        self.configureExternalVariables()
        #configure registryAPI
        self.configureInternalVariables()
        self.serviceLogger.info("Configuration Parameters are Set.")

        #configure Data Adaptor
        self.configureDataAdaptor()
        #configure the Data Manager
        self.confiureDataManager()
        self.configureAASData()
        #configure EndPoints
        self.configureEndPoints()
        #configure IA Adaptors
        self.configureAssetAccessPoints()
        #configure Skill
        self.configureSkills()
        self.configureSkillWebList()
   
    def testingThread(self):
        self.rcidsList = []
        
        self.sequenceList = [200]
        self.rcidsList_HTTP = ["AASId_"+str(i) for i in range(53400,53400+200)]
        self.rcidsList_MQTT = ["AASId_"+str(i)+"_MQTT" for i in range(53400,53400+200)]

        i = 0
        k = self.sequenceList[0]
        while True :
            time.sleep(5)
            if len(list(self.idDict.keys())) == 200:
                temp_HTTP = []
                temp_MQTT = []
                
                for j in range(0,200):
                    temp_HTTP.append(self.idDict[self.rcidsList_HTTP[j]])
                #for j in range(0,200):
                #    temp_MQTT.append(self.idDict[self.rcidsList_MQTT[j]])                    
                
                #===============================================================
                # with open("C:\\Users\\pakala\\eclipse-workspace1\\RIC_Testing\\TestNew\\"+str(k)+"\\log_"+str(k)+"_rcv_vws_http.csv", "w") as outfile:
                #     outfile.write("\n".join(temp_HTTP))
                # 
                # with open("C:\\Users\\pakala\\eclipse-workspace1\\RIC_Testing\\TestNew\\"+str(k)+"\\log_"+str(k)+"_rcv_vws_mqtt.csv", "w") as outfile:
                #     outfile.write("\n".join(temp_MQTT))
                #===============================================================
                
                self.idDict = {}
                i = i + 1
                if (i > 20):
                    break
                
    def start(self):
        
        self.serviceLogger.info('Starting the Service Entities')
        
        self.cdrivers = {}
        self.cdrv_mqtt = None
        #start the Data Manager
        self.startDataManager()
        #start the communication drivers
        self.startEndPoints()
        #start the message handler thread
        self.startMsgHandlerThread()
        #start the skills
        self.startSkills()
        #start the testing Schedular thread
        #testingSThread = threading.Thread(target=self.testingThread)     
        #testingSThread.start()
                
    def stop(self):
        self.scheduler.stop()
        for module_name, cdrv in self.cdrvs.items():
            cdrv.stop()
    
    def shutDown(self):
        self.serviceLogger.info("The Service Logger is shutting down.")
        os._exit(0)

if __name__ == "__main__":
    pyAAS = vws_ric()
    pyAAS.configure()
    pyAAS.start()
    print('Press Ctrl+{0} to exit'.format('C'))
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        pyAAS.stop()

