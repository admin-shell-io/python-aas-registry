'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import os
import requests
import threading
from datetime import datetime
from flask import Flask
from flask_restful import Api

try:
    from utils.i40data import Generic
except ImportError:
    from src.main.utils.i40data import Generic

try:
    from abstract.endpointhandler import AASEndPointHandler
except ImportError:
    from src.main.abstract.endpointhandler import AASEndPointHandler

try:
    from aasendpointhandlers.rstapi_endpointresources import RetrieveMessage, HandleConnectProtocol, StatusUI, \
        HandleConnect, RefreshUI, DescriptorSchema, AssetAdministrationShellDescriptorById, SubmodelDescriptorById, \
        AssetAdministrationShellDescriptor, SubmodelDescriptor
except ImportError:
    from src.main.aasendpointhandlers.rstapi_endpointresources import RetrieveMessage, HandleConnectProtocol, StatusUI, \
        HandleConnect, RefreshUI, DescriptorSchema, AssetAdministrationShellDescriptorById, SubmodelDescriptorById, \
        AssetAdministrationShellDescriptor, SubmodelDescriptor

drv_rst_app = Flask(__name__)
drv_rst_app.secret_key = os.urandom(24)
drv_rst_api = Api(drv_rst_app)
drv_rst_app.debug = False


class AASEndPointHandler(AASEndPointHandler):

    def __init__(self, pyAAS, msgHandler):
        self.pyAAS = pyAAS

        self.msgHandler = msgHandler
        self.targetHeader = {"content-type": "application/json"}

    def configure(self):

        self.ipaddressComdrv = '0.0.0.0'#self.pyAAS.lia_env_variable["LIA_AAS_RESTAPI_HOST_EXTERN"]
        self.portComdrv = self.pyAAS.lia_env_variable["LIA_AAS_RESTAPI_PORT_INTERN"]

        # COMMUNICATION END POINT
        drv_rst_api.add_resource(RetrieveMessage, "/i40commu", resource_class_args=tuple([self.pyAAS]))
        drv_rst_api.add_resource(HandleConnectProtocol, "/publish", resource_class_args=tuple([self.pyAAS]))
        drv_rst_api.add_resource(HandleConnect, "/connect", resource_class_args=tuple([self.pyAAS]))

        # UI API
        drv_rst_api.add_resource(StatusUI, "/status", resource_class_args=tuple([self.pyAAS]))
        drv_rst_api.add_resource(RefreshUI, "/refresh", resource_class_args=tuple([self.pyAAS]))

        # Resgitry API
        # ShellDescriptors API
        drv_rst_api.add_resource(AssetAdministrationShellDescriptorById, "/registry/shell-descriptors/<path:aasId>",
                                 resource_class_args=tuple([self.pyAAS]))
        drv_rst_api.add_resource(SubmodelDescriptorById,
                                 "/registry/shell-descriptors/<path:aasId>/submodel-descriptors/<path:submodelId>",
                                 resource_class_args=tuple([self.pyAAS]))

        drv_rst_api.add_resource(AssetAdministrationShellDescriptor, "/registry/shell-descriptors",
                                 resource_class_args=tuple([self.pyAAS]))
        drv_rst_api.add_resource(SubmodelDescriptor, "/registry/shell-descriptors/<path:aasId>/submodel-descriptors",
                                 resource_class_args=tuple([self.pyAAS]))

        # Submodel ShellDescriptors API
        # drv_rst_api.add_resource(SubModelDescriptors, "/registry/submodel-descriptors", resource_class_args=tuple([self.pyAAS]))
        # drv_rst_api.add_resource(SubModelDescriptorsbyId, "/registry/submodel-descriptors/<path:submodelId>", resource_class_args=tuple([self.pyAAS]))

        drv_rst_api.add_resource(DescriptorSchema, "/descriptor/<path:descriptorId>",
                                 resource_class_args=tuple([self.pyAAS]))
        self.pyAAS.service_logger.info("REST API namespaces are configured")

    def update(self, channel):
        pass

    def run(self):
        drv_rst_app.run(host=self.ipaddressComdrv, port=self.portComdrv,ssl_context=(self.pyAAS.lia_env_variable["LIA_PATH2AUTHCERT"], self.pyAAS.lia_env_variable["LIA_PATH2SIGNINGKEY"]))
        # serve(drv_rst_app,host=self.ipaddressComdrv, port=self.portComdrv,threads= 10)
        self.pyAAS.service_logger.info("REST API namespaces are started")

    def start(self, pyAAS, uID):
        self.pyAAS = pyAAS
        self.uID = uID
        restServerThread = threading.Thread(target=self.run)
        restServerThread.start()

    def stop(self):
        self.pyAAS.service_logger.info("REST API namespaces are stopped.")

    def dispatchMessage(self, send_Message):
        try:
            targetHeader = {"content-type": "application/json", "User-Agent": "VWS Registry Agent " + str(
                datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]}
            targetID = send_Message["frame"]["receiver"]["id"]
            targetAAS_URI = self.pyAAS.httpEndPointsDict[targetID]
            # t1 = self.pyAAS.idDict[targetID]
            # self.pyAAS.idDict[targetID] = t1 + "," +str(datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]
            targetResponse = requests.post(targetAAS_URI, data=json.dumps(send_Message), headers=targetHeader)
            if (targetResponse.status_code == 200):
                # t2 = self.pyAAS.idDict[targetID]
                # self.pyAAS.idDict[targetID] = t2 + "," +str(datetime.utcnow().isoformat(sep=' ', timespec='microseconds'))[17:]
                return True
            else:
                return False
        except Exception as E:
            print(str(E))
            return True

    def sendBroadCatMessage(self, send_Message, key):
        try:
            requests.post(url=self.pyAAS.httpEndPointsDict[key], data=json.dumps(send_Message),
                          headers=self.targetHeader)
            print("A new broadcast message is sent to the AAS " + key)
        except Exception as E:
            print(str(E) + "Error HTTP Send Error")

    def dispatchBroadCastMessage(self, send_Message):
        keysList = list(self.pyAAS.httpEndPointsDict.keys())
        for key in keysList:
            (threading.Thread(target=self.sendBroadCatMessage, args=(send_Message, key))).start()

    def sendExceptionMessageBack(self, ErrorMessage):
        I40FrameData = {
            "semanticProtocol": "Register",
            "type": "registerAck",
            "messageId": "registerAck_1",
            "SenderAASID": self.pyAAS.AASID,
            "SenderRolename": "HTTP_ENDPoint",
            "conversationId": "AASNetworkedBidding",
            "ReceiverAASID": self.pyAAS.AASID,
            "ReceiverIdType": "idShort",
            "SenderIdType": "idShort",
            "ReceiverRolename": "Register"
        }
        self.gen = Generic()
        self.frame = self.gen.createFrame(I40FrameData)

        self.InElem = self.pyAAS.dba.getAAsSubmodelsbyId(self.pyAAS.AASID, "StatusResponse")["message"][0]

        self.InElem["submodelElements"][0]["value"] = "E"
        self.InElem["submodelElements"][1]["value"] = "E009. delivery-error"
        self.InElem["submodelElements"][2]["value"] = ErrorMessage

        registerAckMessage = {"frame": self.frame,
                              "interactionElements": [self.InElem]}

        self.pyAAS.msgHandler.putIbMessage(registerAckMessage)

    def retrieveMessage(self, testMesage):  # todo
        pass
