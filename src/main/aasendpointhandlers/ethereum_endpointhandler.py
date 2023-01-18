'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


import json
import os
import sys
import threading
import time
import web3

from web3 import Web3,HTTPProvider

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from main.abstract.endpointhandler import AASEndPointHandler

try:
    from utils.i40data import Generic
except ImportError:
    from main.utils.i40data import Generic


class AASEndPointHandler(AASEndPointHandler):
    
    def __init__(self, pyAAS,msgHandler):
        self.pyAAS = pyAAS
        self.topicname = pyAAS.AASID
        self.msgHandler = msgHandler
        self.eventListner = True
        self.gen = Generic()
        
    def update(self,event_filter, poll_interval):
        while self.eventListner:
            for event in event_filter.get_new_entries():
                self.retrieveMessage(event)
                time.sleep(poll_interval)

    def configure(self):
        self.ipaddressComdrv = self.pyAAS.lia_env_variable["LIA_AAS_ETHEREUM_HOST"]
        self.portComdrv = int(self.pyAAS.lia_env_variable["LIA_AAS_ETHEREUM_PORT"])
        
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.web3 = Web3(HTTPProvider("http://"+self.ipaddressComdrv+":"+str(self.portComdrv)))
        self.defaultAccount = self.web3.eth.accounts[0]
        self.web3.eth.defaultAccount = self.defaultAccount
        with open(self.script_dir+'/resources/messageStorage.json') as json_file:
            self.data = json.load(json_file)
        self.abi=self.data["abi"]
        self.address =  self.web3.toChecksumAddress(self.data["networks"]["5777"]["address"])
        self.eth_Contract = self.web3.eth.contract(abi =self.abi,address=self.address)
        self.eth_block_filter = self.web3.eth.filter({'fromBlock':'latest', 'address':self.web3.toChecksumAddress(self.address)})
        self.pyAAS.serviceLogger.info("Ethereum message event listner is configured")

    def start(self, pyAAS, tpn):
        self.pyAAS = pyAAS
        self.tpn = tpn
        try :
            ethClientThread1 = threading.Thread(target=self.update, args=(self.eth_block_filter,1,))
            ethClientThread1.start()
          
        except Exception as e:
            self.pyAAS.serviceLogger.info('Unable to connect to Ethereum Network ' + str(e))
            os._exit(0)
        self.pyAAS.serviceLogger.info("Ethereum message event listner is started")
                    
    def stop(self):
        self.eventListner = False
        self.pyAAS.serviceLogger.info('Ethereum message event listner is stopped.')

    def dispatchMessage(self, send_Message): 
        publishTopic = self.pyAAS.BroadCastMQTTTopic
        try:
            if (publishTopic == self.pyAAS.AASID):
                self.msgHandler.putIbMessage(send_Message)
            else:
                message = self.createOutMessage(send_Message)
                #self.web3.geth.personal.unlockAccount(self.web3.toChecksumAddress(self.defaultAccount),"12345")
                trx_hash = self.eth_Contract.functions.createNewMessage(
                            message[0],message[1],message[2],message[3],message[4],
                            message[5],message[6],message[7],message[8],message[9],message[10],
                            message[11]).transact()
        except Exception as e:
            self.pyAAS.serviceLogger.info("Unable to publish the message to the Ethereum Chain", str(e))
    
    def createOutMessage(self,outMessage):
        return self.gen.createEthereumOutMessage(outMessage)
    
    def createInMessage(self,newMesage):
        return self.gen.createEthereumInMessage(newMesage)
    
    def retrieveMessage(self,event):
        receipt = self.web3.eth.waitForTransactionReceipt(event['transactionHash'])
        eventMessage = self.eth_Contract.events.newMessage().processReceipt(receipt)  
        message = (self.eth_Contract.functions.getMessage(eventMessage[0]["args"]["messageID"]).call()) 
        senderId = self.toString(message[0])
        try:
            if (senderId == self.pyAAS.AASID):
                pass
            else:
                newMessage = {}
                newMessage["senderId"] = self.gen.toString(message[0])
                newMessage["receiverId"] = self.gen.toString(message[1]) 
                newMessage["senderRole"] = self.gen.toString(message[2])
                newMessage["receiverRole"] = self.gen.toString(message[3])
                newMessage["msgType"] = self.gen.toString(message[4])
                newMessage["messageId"] = (message[5])
                newMessage["propertyX"] = self.gen.toString(message[6])
                newMessage["propertyY"] = self.gen.toString(message[7])
                newMessage["listPrice"] = self.gen.toString(message[8])
                newMessage["conversationId"] = self.gen.toString(message[9])
                self.jsonMessage = self.gen.createInMessage(newMessage)
                self.msgHandler.putIbMessage(self.jsonMessage)
                self.pyAAS.serviceLogger.info("A new Message received from the sender " + self.jsonMessage["frame"]["sender"]["identification"]["id"])
        except Exception as e:
            self.pyAAS.serviceLogger.info("Exception " + str(e))
