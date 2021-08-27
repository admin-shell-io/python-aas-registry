'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universität Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''


class Generic(object):
    def __init__(self):
        pass
    
    def toString(self,message32):
        message32 = message32.hex().rstrip("0")
        if len(message32) % 2 != 0:
            message32 = message32 + '0'
        message = bytes.fromhex(message32).decode('utf8')
        return message
    
    def getRestAPIFrame(self,aasId):
        I40Frame = {
                    "type":"RestRequest",
                    "messageId":"RestRequest",
                    "SenderAASID":aasId,
                    "SenderRolename":"restAPI",
                    "ReceiverAASID":"",
                    "rolename":"",
                    "replyBy":"NA",
                    "conversationId":"AASNetworkedBidding",
                    "semanticProtocol":"www.admin-shell.io/interaction/restapi"
                }
        return I40Frame
    
    def createFrame(self,I40Frame):
        frame = {
                    "semanticProtocol": {
                    "keys": [
                        {
                            "type": "GlobalReference",
                            "local": "local", 
                            "value": I40Frame["semanticProtocol"], 
                            "idType": "IRI"
                        }
                        ]
                    }, 
                    "type": I40Frame["type"],
                    "messageId": I40Frame["messageId"], 
                    "sender": {
                        "identification": {
                            "id": I40Frame["SenderAASID"],
                            "idType": I40Frame["SenderIdType"]
                        }, 
                        "role": {
                            "name": I40Frame["SenderRolename"]
                            }
                        },
                    "replyBy": I40Frame["replyBy"],
                    "replyTo": I40Frame["replyTo"],
                    "conversationId": I40Frame["conversationId"]
                }
        
        if (I40Frame["ReceiverAASID"] != ""):
            frame["receiver"] = {
                                    "identification": {
                                        "id": I40Frame["ReceiverAASID"],
                                        "idType": I40Frame["ReceiverIdType"]
                                    }, 
                                    "role": {
                                        "name": I40Frame["ReceiverRolename"],
                                        
                                    }
                                }
     
        return frame