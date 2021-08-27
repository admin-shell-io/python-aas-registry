'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import logging
import random
import sys
import time
import uuid

from datetime import datetime

try:
    import queue as Queue
except ImportError:
    import Queue as Queue 


try:
    from utils.i40data import Generic
except ImportError:
    from main.utils.i40data import Generic
try:
    from utils.submodelupdate import SubmodelUpdate,SubmodelElement
except ImportError:
    from main.utils.submodelupdate import SubmodelUpdate,SubmodelElement
try:
    from utils.aaslog import serviceLogHandler,LogList
except ImportError:
    from main.utils.aaslog import serviceLogHandler,LogList

'''
    The skill generator extracts all the states from the transitions list.
    For each STATE, a seperate python class is created. This python class has two main
    functions run() and the next(). The run method is required to execute a set
    of instructions so that the class which represents a state could exhibit a specific behavior. 
    The next method defines the next class that has to be executed.
    
    Each transition is attributed by input document and outpput document.
    
    In the case of  input document, the class is expected to wait for the 
    arrival of a specific document type. While for the output document, the class
    is expected to send out the output document.
    
    This source-code consists of a base class and the all the classes each pertaining 
    to definite state of the skill state-machine. The base class represents the skill 
    and coordinates the transition from one state to another.
    
    The baseclass is responsible for collecting the documents from the external
    world (either from other skill that is part of the AAS or a skill part of 
    of another AAS). For this the baseclass maintains a queue one for each class. 
    
    The communication between any two skills of the same AAS or the skills of 
    different AAS is done in I4.0 language.
    
    An I4.0 message packet consists of a frame header and the interactionElements
    detail part. The frame element consists of Sender and Receiver elements. Under
    this the AASID's and respective skillnames can be specified.
    
    Also  every message packet is associated with a type, the type information is 
    specified in the Input and Output property tags under Transition collection in
    the AASx package.
    
    Based on the receive information in the frame header, the message is routed appropriate
    Skill. The base-class maintains a specific InboundQueue, into the messages dropped by the
    messagehandler. 
    
    A class specific inbound queue is defined in the baseclass for the classes defined in this
    source-code. A dictionary is also manitained, with key representing the messagetype and the
    value being the class specific inboundqueue.
    
    Every inbound message to the skill, is routed to the specific class based on its message type
    from the base CLaas.  
    
    For operational purposes, a dictionary variable is defined for each message type that this skill
    expects. 

    StateName_In         
    StateName_Queue 
        
    The sendMessage method in the baseclass submits an outbound message to the message handler so that
    it could be routed to its destination. Every class can access this method and publish the outbound
    messgae.  
    
    Accessing the asset entry within a specific class
        For accessing the asset, a developer has to write specific modules in the assetaccessadaptors
        package. In this version of LIAPAAS framework PLC OPCUA adaptor for reading and writing OPCUA
        variables is provided.
        
        The asset access information like IP address, port, username, password and the opcua variables
        are defined in the AASx configuration file.
        
        The module and the related OPCUA variable definitions with thin the skill.
        
        MODULE_NAME = "PLC_OPCUA"
        #Accessing the specifc assetaaccess adaptor 
        self.plcHandler = self.baseClass.saas.assetaccessEndpointHandlers[MODULE_NAME] # 1
        
        #accessing the list property variables Dictionary are specified in the configuration file.  
        self.propertyDict = self.plcHandler.propertylist # 2
        
        PLC_OPCUA represents the module specific to opcua adaptor to access the PLC
        
        The code snippets 1 and 2 need to be initialized in the constructor of the class        
        
    def StateName_Logic(self):
        self.plcHandler.read(self.propertyDict["sPermission"])
        self.plcHandler.write(self.propertyDict["sPermission"],"value")
        time.sleep(10)
      
       The propertylist is the dictionary, that has asset specific keys *OPCUA variables and the respective
        addresses.
    
    creating an outbound I40 message.
    
    Note : The communication between the skills that are part of the same AAS, or different
    AAS should happen within the I40 data format structure.
    
    A generic class is provided within the package utils.i40data (it is imported in the code).
    
    code snippet
    
    self.gen = Generic()
    self.frame = self.gen.createFrame(I40FrameData)
    
    
    If the receiver is a skill within the same AAS, the ReceiverAASID would be same as SenderAASID
    where the ReceiverRolename would be specific skill Name 
    
    The ReceiverAASID and ReceiverRolename could be obtained from sender part of the incoming message
    and these are to be provided empty, if there is no receiver.
    receiverId = self.baseClass.StateName_In["frame"]["sender"]["identification"]["id"]
    receiverRole = self.baseClass.StateName_In["frame"]["sender"]["role"]["name"]
    
    I40FrameData is a dictionary
    
    language : English, German
    format : Json, XML //self.baseClass.saas.preferredCommunicationFormat
    reply-to : HTTP,MQTT,OPCUA (endpoint) // self.baseClass.saas.preferedI40EndPoint
    serviceDesc : "short description of the message"
    
    {
        "type" : ,
        "messageId":messageId,
        "SenderAASID" : self.baseClass.AASID,
        "SenderRolename" : "{{MetaData/Name}}",
        "conversationId" : "AASNetworkedBidding",
        "replyBy" :  "",
        "ReceiverAASID" :  receiverId,
        "ReceiverRolename" : receiverRole,
        "params" : {},
        "serviceDesc" : "",
        "language" : "",
        "format" : "",
        "reply-to" : ""       
    } # In proposal needs to be confirmed
    
    the interactionElements part of the I40 frame usually contain the submodel elements,
    the respective the submodel element could be fetched from the submodel dictionary.
    
    The fetching of the submodel elements is done dynamically from the database.
    
    example Boring (should be same as the one specified in AASX file.)
    boringSubmodel = self.baseClass.saas.dba.getSubmodelsbyId("BoringSubmodel")
    # result is list
    I40OutBoundMessage = {
                            "frame" : frame,
                            "interactionElements" : boringSubmodel
                        }
                        
    Saving the inbound and outbound messages into the datastore
    
    example :
    
    def retrieveMessage(self):
        self.baseClass.StateName_In = self.baseClass.StateName_Queue.get()
    
    def saveMessage(self,message):
        self.instanceId = str(uuid.uuid1())
        self.baseClass.saas.dataManager.pushInboundMessage({"functionType":3,"data":message,"instanceid":self.instanceId,
                                                            "messageType":message["frame"]["type"]})
        
    
'''
    
{{#each StateANDTransitionList}}
class {{StateName}}(object):
    
    def __init__(self, baseClass):
        '''
        '''
        self.baseClass = baseClass
        
        #Transition to the next state is enabled using the targetState specific Boolen Variable
        # for each target there will be a separate boolean variable
                
        {{#each ConditionList}}
        self.{{targetstate}}_Enabled = True
        {{/each}}
    
    {{#each IDCYes}}
    def retrieve_{{StateName}}_Message(self):
        self.baseClass.{{StateName}}_In = self.baseClass.{{StateName}}_Queue.get()
    
    def saveMessage(self):
        inboundQueueList = list(self.baseClass.{{StateName}}_Queue.queue) # in case for further processing is required
        # else creation of the new queue is not required.
        for i in range (0, self.baseClass.{{StateName}}_Queue.qsize()):
            message = inboundQueueList[i]
            self.instanceId = str(uuid.uuid1())
            self.baseClass.saas.dataManager.pushInboundMessage({"functionType":3,"instanceid":self.instanceId,
                                                            "conversationId":message["frame"]["conversationId"],
                                                            "messageType":message["frame"]["type"],
                                                            "messageId":message["frame"]["messageId"],
                                                            "message":message})
            
    {{/each}}

    def {{StateName}}_Logic(self):
        pass # The developer has to write the logic that is required for the 
             # for the execution of the state

    {{#each ODCYes}}
    def create_Outbound_Message(self):
        self.oMessages = "{{oMessage}}".split("/")
        outboundMessages = []
        for oMessage in self.oMessages:
            message = self.baseClass.StateName_In
            self.gen = Generic()
            #receiverId = "" # To be decided by the developer
            #receiverRole = "" # To be decided by the developer
            
            # For broadcast message the receiverId and the 
            # receiverRole could be empty 
            
            # For the return reply these details could be obtained from the inbound Message
            receiverId = message["frame"]["sender"]["identification"]["id"]
            receiverRole = message["frame"]["sender"]["role"]["name"]
            
            # For sending the message to an internal skill
            # The receiver Id should be
            
            I40FrameData =      {
                                    "semanticProtocol": self.baseClass.semanticProtocol,
                                    "type" : oMessage,
                                    "messageId" : oMessage+"_"+str(self.baseClass.saas.dba.getMessageCount()+1),
                                    "SenderAASID" : self.baseClass.saas.AASID,
                                    "SenderRolename" : self.baseClass.skillName,
                                    "conversationId" : message["frame"]["conversationId"],
                                    "replyBy" :  self.baseClass.saas.preferedI40EndPoint,
                                    "replyTo" :  message["frame"]["replyBy"],
                                    "ReceiverAASID" :  receiverId,
                                    "ReceiverRolename" : receiverRole
                                }
        
            self.frame = self.gen.createFrame(I40FrameData)
    
            oMessage_Out = {"frame": self.frame}
            # Usually the interaction Elements are the submodels fro that particualar skill
            # the relevant submodel could be retrieved using
            # interactionElements
            
            #self.InElem = self.baseClass.saas.dba.getSubmodelsbyId("BoringSubmodel")
            #oMessage_Out ={"frame": self.frame,
            #                        "interactionElements":self.InElem["message"]}
            self.instanceId = str(uuid.uuid1())
            self.baseClass.saas.dataManager.pushInboundMessage({"functionType":3,"instanceid":self.instanceId,
                                                            "conversationId":oMessage_Out["frame"]["conversationId"],
                                                            "messageType":oMessage_Out["frame"]["type"],
                                                            "messageId":oMessage_Out["frame"]["messageId"],
                                                            "message":oMessage_Out})
            outboundMessages.append(oMessage_Out)
        return outboundMessages
    {{/each}}
    
    def run(self):
            
        self.baseClass.skillLogger.info("\n #############################################################################")
        # StartState
        self.baseClass.skillLogger.info("StartState: {{StateName}}")
        # InputDocumentType"
        InputDocument = "{{InMessageList}}"
        self.baseClass.skillLogger.info("InputDocument : " + InputDocument)
        
        {{#each IDCYes}}
        '''
            In case a class expects an input document then.
            It would need to lookup to its specific queue
            that is defined in the based class
        '''
        if (InputDocument != "NA"):
            self.messageExist = True
            i = 0
            sys.stdout.write(" Waiting for response")
            sys.stdout.flush()
            while (((self.baseClass.{{StateName}}_Queue).qsize()) == 0):
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush() 
                i = i + 1 
                if i > 10: # Time to wait the next incoming message
                    self.messageExist = False # If the waiting time expires, the loop is broken
                    break
            if (self.messageExist):
                self.saveMessage() # in case we need to store the incoming message
                self.retrieve_{{StateName}}_Message() # in case of multiple inbound messages this function should 
                                                      # not be invoked. 
        {{/each}}
        self.{{StateName}}_Logic()
        
    def next(self):
        OutputDocument = "{{OutputDocument}}"
        self.baseClass.skillLogger.info("OutputDocumentType : " + OutputDocument)
        
        {{#each ODCYes}}
        if (OutputDocument != "NA"):
            self.outboundMessages = self.create_Outbound_Message()
            for outbMessage in self.outboundMessages:
                self.baseClass.sendMessage(outbMessage)
        {{/each}}
        
        {{#each ConditionList}}
        if (self.{{targetstate}}_Enabled):
            self.baseClass.skillLogger.info("Condition :" + "{{Condition}}")
            ts = {{targetstate}}(self.baseClass)
            self.baseClass.skillLogger.info("TargettState: " + ts.__class__.__name__)
            self.baseClass.skillLogger.info("############################################################################# \n")
            return ts
        {{/each}}
        
{{/each}}


{{#each ExitState}}
class Exit(object):
    
    def __init__(self, baseClass):
        '''
        '''
        self.baseClass = baseClass
        self.I40OutBoundMessage = {}
        
    def run(self):
            
        self.baseClass.skillLogger.info("\n #############################################################################")
        # StartState
        self.baseClass.skillLogger.info("StartState: Exit")
        # InputDocumentType"
        '''
            In case a class expects an input document then.
            It would need to lookup to its specific queue
            that is defined in the based class
        '''

    def next(self):
        '''
                  If the condition is soecified is specified as '-' in the config file
                  please replace it with the needed condition usually True or False
        '''
        if (True):
            self.baseClass.skillLogger.info("Condition :" + "-")
            self.baseClass.skillLogger.info("############################################################################# \n")
            return None
{{/each}}        

class {{MetaData/Name}}(object):
    '''
    classdocs
    '''

        
    def initstateSpecificQueueInternal(self):
        
        self.QueueDict = {}
        
        {{# each StateANDTransitionList}}
        self.{{StateName}}_Queue = Queue.Queue()
        {{/each}}
        
                
        self.QueueDict = {
            {{#each IDCList}}
              "{{IDC}}": self.{{StateName}}_Queue,
            {{/each}}
            }
    
    def initInBoundMessages(self):
        {{#each InputMessageTypeList}}
            self.{{StateName}}_In = {}
        {{/each}}
    
    def createStatusMessage(self):
        self.StatusDataFrame =      {
                                "semanticProtocol": self.semanticProtocol,
                                "type" : "StausChange",
                                "messageId" : "StausChange_1",
                                "SenderAASID" : self.saas.AASID,
                                "SenderRolename" : self.skillName,
                                "conversationId" : "AASNetworkedBidding",
                                "replyBy" :  "",
                                "replyTo" :"",
                                "ReceiverAASID" :  self.saas.AASID + "/"+self.skillName,
                                "ReceiverRolename" : "SkillStatusChange"
                            }
        self.statusframe = self.gen.createFrame(self.StatusDataFrame)
        self.statusInElem = self.saas.dba.getAAsSubmodelsbyId(self.saas.AASID,"StatusResponse")
        self.statusMessage ={"frame": self.statusframe,
                                "interactionElements":self.statusInElem["message"]}
        
        
    def createOrderMessage(self):    
        DataFrame =      {
                                "semanticProtocol": self.semanticProtocol,
                                "type" : "Order",
                                "messageId" : "Order_1",
                                "SenderAASID" : self.saas.AASID,
                                "SenderRolename" : "InternalRequester",
                                "conversationId" : "AASNetworkedBidding",
                                "replyBy" :  "MQTT",
                                "replyTo" :"MQTT",
                                "ReceiverAASID" :  self.saas.AASID + "/"+self.skillName,
                                "ReceiverRolename" : "ProductionManager"
                            }
        frame = self.gen.createFrame(DataFrame)
        return {"frame": frame}        
    
    def __init__(self, saas):
        '''
        Constructor
        '''
        
        self.SKILL_STATES = {
                        {{#each StatesList}}  "{{StateName}}": "{{StateName}}",{{/each}}
                       }
        
        self.saas = saas
        self.skillName = "{{MetaData/Name}}"
        self.initstateSpecificQueueInternal()
        self.initInBoundMessages()

        
        self.enabledStatus = {"Y":True, "N":False}
        self.enabledState = self.enabledStatus["{{enabled}}"]
        
        self.semanticProtocol = "{{semanticProtocol}}"

        self.skillLogger = logging.getLogger(str(self.__class__.__name__) + ' Service Instance' )
        self.skillLogger.setLevel(logging.DEBUG)
        self.gen = Generic()
        self.createStatusMessage()
        self.productionStepSeq = []
        self.responseMessage = {}
        
    def Start(self, msgHandler, skillDetails):
        self.msgHandler = msgHandler
        
        self.commandLogger_handler = logging.StreamHandler(stream=sys.stdout)
        self.commandLogger_handler.setLevel(logging.DEBUG)
        
        self.fileLogger_Handler = logging.FileHandler(self.saas.base_dir+"/logs/"+self.skillName+".LOG")
        self.fileLogger_Handler.setLevel(logging.DEBUG)
        
        self.listHandler = serviceLogHandler(self.msgHandler.{{MetaData/Name}}LogList)
        self.listHandler.setLevel(logging.DEBUG)
        
        self.Handler_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')
        
        self.listHandler.setFormatter(self.Handler_format)
        self.commandLogger_handler.setFormatter(self.Handler_format)
        self.fileLogger_Handler.setFormatter(self.Handler_format)
        
        self.skillLogger.addHandler(self.listHandler)
        self.skillLogger.addHandler(self.commandLogger_handler)
        self.skillLogger.addHandler(self.fileLogger_Handler)
        
        self.skillDetails = skillDetails
        {{initialState}}_1 = {{initialState}}(self)
        self.stateChange("{{initialState}}")
        currentState = {{initialState}}_1
        self.enabledState = self.skillDetails["enabled"]
        
        self.StatusResponseSM = self.saas.dba.getAAsSubmodelsbyId(self.saas.AASID,"StatusResponse")["message"]
        
        while (True):
            if ((currentState.__class__.__name__) == "{{initialState}}"):
                if(self.enabledState):
                    currentState.run()
                    ts = currentState.next()
                    self.stateChange(ts.__class__.__name__)
                    currentState = ts
            else:
                currentState.run()
                ts = currentState.next()
                if not (ts):
                    break
                else:
                    self.stateChange(ts.__class__.__name__)
                    currentState = ts
    
    def geCurrentSKILLState(self):
        return self.SKILL_STATE
    
    def getListofSKILLStates(self):
        return self.SKILL_STATES
    
    
    def stateChange(self, STATE):
        self.statusMessage["interactionElements"][0]["submodelElements"][0]["value"] = "I"
        self.statusMessage["interactionElements"][0]["submodelElements"][1]["value"] = "A006. internal-status-change"
        self.statusMessage["interactionElements"][0]["submodelElements"][2]["value"] = str(datetime.now()) +" "+STATE
        self.sendMessage(self.statusMessage)
    
    def sendMessage(self, sendMessage):
        self.msgHandler.putObMessage(sendMessage)
    
    def receiveMessage(self,inMessage):
        try:    
            messageType = str(inMessage['frame']['type'])
            if messageType == "StatusUpdate":
                try:
                    statusSubmodel = inMessage["interactionElements"][0]["submodelElements"][0]["value"]
                    if statusSubmodel == "Enable":
                        self.enabledState = True
                        try:
                            self.QueueDict["Order"].put(self.createOrderMessage())
                        except Exception as e:
                            pass
                    else:
                        self.enabledState = False
                except:
                    pass
            else:
                try:
                    self.QueueDict[messageType].put(inMessage)
                except:
                    pass
            
        except:
            self.skillLogger.info("Raise an Exception")



if __name__ == '__main__':
    
    lm2 = {{MetaData/Name}}()
    lm2.Start('msgHandler')