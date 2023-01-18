'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import logging
import os
import requests
import threading
import uuid

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from src.main.abstract.endpointhandler import AASEndPointHandler

import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

try:
    from utils.utils import ExecuteDBModifier, ExecuteDBRetriever, DescriptorValidator, ConnectResponse
except ImportError:
    from src.main.utils.utils import ExecuteDBModifier, ExecuteDBRetriever, DescriptorValidator, ConnectResponse


class AASEndPointHandler(AASEndPointHandler):

    def __init__(self, pyAAS, msgHandler):
        self.pyAAS = pyAAS
        self.topicname = pyAAS.AASID
        self.msgHandler = msgHandler

    def on_connect(self, client, userdata, flags, rc):
        self.pyAAS.service_logger.info("MQTT channels are succesfully connected.")

    def configure(self):
        self.ipaddressComdrv = self.pyAAS.lia_env_variable["LIA_AAS_MQTT_HOST"]
        self.portComdrv = int(self.pyAAS.lia_env_variable["LIA_AAS_MQTT_PORT"])

        self.client = mqtt.Client(client_id=str(uuid.uuid4()))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.retrieveMessage

    def update(self, channel):
        self.client.subscribe(channel)
        self.client.loop_forever()

    def start(self, pyAAS, tpn):
        self.pyAAS = pyAAS
        self.tpn = "AASpillarbox"  # tpn
        try:
            self.client.connect(self.ipaddressComdrv, port=(self.portComdrv))
            mqttClientThread1 = threading.Thread(target=self.update, args=(self.tpn,))
            mqttClientThread1.start()

        except Exception as e:
            self.pyAAS.service_logger.info('Unable to connect to the mqtt server ' + str(e))
            os._exit(0)

        self.pyAAS.service_logger.info("MQTT channels are started")

    def stop(self):
        try:
            self.client.loop_stop(force=False)
            self.client.disconnect()

        except Exception as e:
            self.pyAAS.service_logger.info('Error disconnecting to the server ' + str(e))

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
                self.client.publish(publishTopic, str(json.dumps(send_Message)))
        except Exception as e:
            self.pyAAS.service_logger.info("Unable to publish the message to the mqtt server", str(e))

    def retrieveMessage(self, client, userdata, msg):
        try:
            msg1 = str(msg.payload, "utf-8")
            jsonMessage = json.loads(msg1)
            _type = jsonMessage["frame"]["type"]
            if (_type == "HeartBeat"):
                _sender = jsonMessage["frame"]["sender"]["identification"]["id"]
                _senderIdType = jsonMessage["frame"]["sender"]["identification"]["idType"]
                cr = ConnectResponse(self.pyAAS)
                if (_sender in self.pyAAS.mqttGateWayEntries):
                    self.pyAAS.aasBotsDict[_sender] = (datetime.now() + timedelta(hours=2)).strftime(
                        "%Y-%m-%d %H:%M:%S")
                    mqttResponse = cr.creatHeartBeatMQTTResponse(_sender, _senderIdType,
                                                                 jsonMessage["frame"]["conversationId"])
                    self.dispatchMessage(mqttResponse)
                else:
                    mqttResponse = cr.createHeartBeatNegativeMQTTResponse(_sender, _senderIdType,
                                                                          jsonMessage["frame"]["conversationId"])
                    self.dispatchMessage(mqttResponse)
            else:
                if "receiver" not in list(jsonMessage["frame"].keys()):
                    self.pyAAS.msgHandler.putBroadCastMessage(jsonMessage)
                elif jsonMessage["frame"]["receiver"]["identification"]["id"] == "AASpillarbox":
                    self.msgHandler.putIbMessage(jsonMessage)
                else:
                    _receiver = jsonMessage["frame"]["receiver"]["identification"]["id"]
                    if _receiver in list(self.pyAAS.connectBotsDict.keys()):
                        self.pyAAS.connectBotsDict[_receiver]["iframesList"].append(jsonMessage)
                    else:
                        self.pyAAS.idDict[_receiver] = str(
                            datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]
                        self.pyAAS.msgHandler.putTransportMessage(jsonMessage)
        except Exception as E:
            print(str(E))
            # spass

    def sendBroadCatMessage(self, send_Message, aasId):
        try:
            self.client.publish(aasId, str(json.dumps(send_Message)))
            print("A new broadcast message is sent to the AAS " + aasId)
        except Exception as E:
            pass

    def dispatchBroadCastMessage(self, send_Message):
        for x in self.pyAAS.mqttGateWayEntries:
            bCThread = threading.Thread(target=self.sendBroadCatMessage, args=(send_Message, x))
            bCThread.start()
