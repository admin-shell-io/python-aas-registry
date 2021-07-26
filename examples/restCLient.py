'''
Copyright (c) 2021-2022 OVGU LIA
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import json
import requests

url = "http://localhost:9021/api/v1/registry/OVGU_LIA_Requester"
headers = {'content-type' : 'application/json'}
aasDescriptor = {}
with open("OVGU_LIA_Requester.json") as aasDAdaptor:
    aasDescriptor = json.load(aasDAdaptor)

# PUT Rest API 
_putRegistryResponse = requests.put(url,data=json.dumps(aasDescriptor),headers=headers)
print(_putRegistryResponse.text)
print(_putRegistryResponse)

# GET Rest API
_getRegistryResponse = requests.get(url)
print(_getRegistryResponse.text)
print(_getRegistryResponse)

'''
# DELETE Rest API
_deleteRegistryResponse = requests.get(url)
print(_deleteRegistryResponse.text)
print(_deleteRegistryResponse)
'''