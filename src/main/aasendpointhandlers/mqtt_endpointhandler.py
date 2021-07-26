'''
Copyright (c) 2021-2022 OVGU LIA
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import os
import threading
import asyncio
 
import hbmqtt.client
import hbmqtt.mqtt

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from main.abstract.endpointhandler import AASEndPointHandler

from datetime import datetime,timedelta

try:
    from utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse
except ImportError:
    from main.utils.utils import ExecuteDBModifier,ExecuteDBRetriever,DescriptorValidator,ConnectResponse

class AASEndPointHandler(AASEndPointHandler):
    
    def __init__(self, pyAAS, msgHandler):
        self.pyAAS = pyAAS
        self.topicname = pyAAS.AASID
        self.msgHandler = msgHandler
    
    @asyncio.coroutine
    def subscribe(self,channel) -> None:
        self.client = hbmqtt.client.MQTTClient()
        yield from self.client.connect('mqtt://localhost:1883/')#connect("mqtt://"+(self.ipaddressComdrv)+":"+ (self.portComdrv)+"/")
        print("Connected")
        yield from self.client.subscribe([
            (channel, hbmqtt.mqtt.constants.QOS_1)
        ])
        print("Subscribed")
        try:
            while True:
                message = yield from self.client.deliver_message()
                packet = message.publish_packet
                receivedMessage = (packet.payload.data).decode("utf-8")
                mqttClientThread1 = threading.Thread(target=self.retrieveMessage, args=(receivedMessage,))
                mqttClientThread1.start() 
        except Exception as E:
            self.pyAAS.serviceLogger.info('Unable to connect to the mqtt server ' + E)
        
    
    def on_connect(self, client, userdata, flags, rc):
        self.pyAAS.serviceLogger.info("MQTT channels are succesfully connected.")
        
    def configure(self):
        self.ipaddressComdrv = str(self.pyAAS.lia_env_variable["LIA_AAS_MQTT_HOST"])
        self.portComdrv = str(self.pyAAS.lia_env_variable["LIA_AAS_MQTT_PORT"])

    def update(self,chaneel):
        try :
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.Task(self.subscribe(chaneel))
            asyncio.get_event_loop().run_forever()
        except Exception as e:
            self.pyAAS.serviceLogger.info('Unable to connect to the mqtt server ' + str(e))
            os._exit(0)    
    
    def start(self, pyAAS, tpn):
        self.pyAAS = pyAAS
        self.tpn = tpn
        try :
            mqttClientThread1 = threading.Thread(target=self.update, args=(tpn,))
            mqttClientThread1.start() 
        except Exception as e:
            self.pyAAS.serviceLogger.info('Unable to connect to the mqtt server ' + str(e))
            os._exit(0)

        self.pyAAS.serviceLogger.info("MQTT channels are started")
            
 
    def stop(self):
        try: 
            yield from self.client.unsubscribe(['$SYS/broker/uptime', '$SYS/broker/load/#'])
            yield from self.client.disconnect()
             
        except Exception as e:
            self.pyAAS.serviceLogger.info('Error disconnecting to the server ' + str(e))

    @asyncio.coroutine
    def dispatch(self,publishTopic,send_Message):
        yield from self.client.publish(publishTopic, str(json.dumps(send_Message)).encode("utf-8"))         

    def dispatchMessage(self, send_Message): 
        publishTopic = self.pyAAS.BroadCastMQTTTopic
        try:
            publishTopic = send_Message["frame"]["receiver"]["identification"]["id"]
        except Exception as E:
            pass
        try:
            if (publishTopic == self.pyAAS.AASID):
                self.msgHandler.putIbMessage(send_Message)
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                asyncio.Task(self.dispatch(publishTopic,send_Message))
                asyncio.get_event_loop().run_forever()                
        except Exception as e:
            self.pyAAS.serviceLogger.info("Unable to publish the message to the mqtt server", str(e))
            
    def retrieveMessage(self,msg): 
        try:
            jsonMessage = json.loads(msg)  
            _type = jsonMessage["frame"]["type"]
            if (_type == "HeartBeat"):
                _sender = jsonMessage["frame"]["sender"]["identification"]["id"]
                _senderIdType = jsonMessage["frame"]["sender"]["identification"]["idType"]
                cr = ConnectResponse(self.pyAAS)
                if (_sender in self.pyAAS.mqttGateWayEntries):
                    self.pyAAS.aasBotsDict[_sender] = (datetime.now()+ timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
                    mqttResponse = cr.creatHeartBeatMQTTResponse(_sender,_senderIdType, jsonMessage["frame"]["conversationId"])
                    self.dispatchMessage(mqttResponse) 
                else:
                    mqttResponse = cr.createHeartBeatNegativeMQTTResponse(_sender,_senderIdType, jsonMessage["frame"]["conversationId"])
                    self.dispatchMessage(mqttResponse)
            else:       
                if "receiver" not in list(jsonMessage["frame"].keys()):
                    self.pyAAS.msgHandler.putBroadCastMessage(jsonMessage)
                elif jsonMessage["frame"]["receiver"]["identification"]["id"] == "VWS_RIC":
                    self.msgHandler.putIbMessage(jsonMessage)
                else:
                    _receiver = jsonMessage["frame"]["receiver"]["identification"]["id"]
                    if _receiver in list(self.pyAAS.connectBotsDict.keys()):
                        self.pyAAS.connectBotsDict[_receiver]["iframesList"].append(jsonMessage)
                    else:
                        self.pyAAS.idDict[_receiver] = str(datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]
                        self.pyAAS.msgHandler.putTransportMessage(jsonMessage)
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))
            #spass
    
    def sendBroadCatMessage(self,send_Message,aasId):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.Task(self.dispatch(aasId,send_Message))
            asyncio.get_event_loop().run_forever()                    
        except Exception as E:
            self.pyAAS.serviceLogger.info(str(E))        
    
    def dispatchBroadCastMessage(self,send_Message):
        for x in self.pyAAS.mqttGateWayEntries:
            bCThread = threading.Thread(target=self.sendBroadCatMessage,args=(send_Message,x))
            bCThread.start() 
