# Registry Infrastructure Component

The work's of platform industrie 4.0, the [AAS Detail Part 1](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part1_V3.html) firstly introduces the term Asset Administration Shell as digital representation of a real-world asset. Secondly it presents a meta model for structuring the information about an asset in terms of Submodels and submodel elements (submodel collections, properties, operations, events, reference elements, files, and capability’s). The entire data structure representing an AAS can be packaged in either AASx container format or plain JSON, XML formats and can be exchanged between the trading partners (Type 1 AAS).

An AAS being a digital representation of an aaset, the [AAS Detail Part 2](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part_2_V1.html) specifies standards for platform independent services that an AAS needs to support for making information about itself be accessible or available in the digital world (Type 2 AAS). [AAS Detail Part 2](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part_2_V1.html) also mentions about Type 3 AAS that are expected to communicate with each other, probably to solve a real-world problem or to perform a specific task. But it does not specify nor impose any restrictions on how messages between the Type3 AAS needs to be structured.

The VDI/VDE 2193 [Part 1](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-1-sprache-fuer-i40-komponenten-struktur-von-nachrichten) and [Part 2](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-2-sprache-fuer-i40-komponenten-interaktionsprotokoll-fuer-ausschreibungsverfahren) provides guidelines on how the messages exchanged between Type3 AAS needs to be structured and acconrdingly introduces a new language for I4.0 components. An I4.0 message consisits of two parts **frame** and **intercationElements**, the frame part represents the sender and receiver information, where as the intercationElements can have any element that is part of the AAS meta model as defined in the [AAS Detail Part 1](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part1_V3.html).

The standardization group from the platform industrie 4.0 and the group responsible for the 
VDI/VDE 2193 [Part 1](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-1-sprache-fuer-i40-komponenten-struktur-von-nachrichten) and [Part 2](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-2-sprache-fuer-i40-komponenten-interaktionsprotokoll-fuer-ausschreibungsverfahren) neither specifiy nor contemplate any restrictions on how the software component of the AAS needs to be structured and designed. The design decision of using the programming lanaguage, including the application protocols(ALPs) for the development is prerogative of the software developer. From the perspective of application layer protocols, with different alternatives (MQTT, HTTP, AMQP, COAP) available there could a heterogenous system of AAS that are expected to talk to each other.

The [LIA OVGU group](https://lia.ovgu.de/), as part of the [VWS Verntzt project](https://vwsvernetzt.de/) has proposed  a complex infrastructure component **RIC** .  As specified in the [AAS Detail Part 2](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part_2_V1.html), the RIC implements an AAS registry that maintains descriptor details. Additionally RIC platform is associated with multiple application layer plugins (COAP, MQTT and HTTP), where each plugin has a server and the related client component.

#### RIC as Message Broker
RIC platform exploits the descriptor information present in the registry to provide a medium or a channel for transport of messages between any two AAS that support different application layer protocols(ALPs). Any AAS that expects to utilize the services of RIC platform for transport of messages to any other AAS, firstly it should register itself with the RIC registry. Secondly, it needs to embed the endpoint information to which the messages are to be delivered. In case an AAS supports MQTT as the ALP, it is not required to provide any additional endpoint information but it is mandated to subscribe to the MQTT server provided by the RIC.
<pre><code>
      {
        "interface": "communication",
        "protocol_information": {
          "endpoint_address": "http://ip:port/i40commu",
          "endpoint_protocol": "http"
        }
      }
</code></pre>
                                 Addditional endpoint information with interface type as communication.

Every AAS is expected to post the I4.0 message over its preferred ALP to the RIC. RIC takes the responsibility of delivering the message to the appropriate AAS by looking into the descriptor registry.

#### Registration and HeartBeat

Based on the guidelines of VDI/VDE 2193 [Part 1](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-1-sprache-fuer-i40-komponenten-struktur-von-nachrichten) and [Part 2](https://www.vdi.de/richtlinien/details/vdivde-2193-blatt-2-sprache-fuer-i40-komponenten-interaktionsprotokoll-fuer-ausschreibungsverfahren), the RIC introduces two new semantic protocols, one for registration of an AAS and the other  heartbeat for maintaining active status of an AAS. The registration protocol consisits of two I4.0 message types **register** and **registerack**, the hearbeat protocol consists of **HeartBeat** and **HeartBeatAck** message types. The table 1 provides sample values for the 4 message types.

| I4.0 Element                   	| Register I4.0                                   	| RegisterAck I4.0                                	| HeartBeat I4.0                                  	| HeartBeatAck I4.0                               	|
|--------------------------------	|-------------------------------------------------	|-------------------------------------------------	|-------------------------------------------------	|-------------------------------------------------	|
| semanticProtocol/keys/type     	| GlobalReference                                 	| GlobalReference                                 	| GlobalReference                                 	| GlobalReference                                 	|
| semanticProtocol/keys/local    	| local                                           	| local                                           	| local                                           	| local                                           	|
| semanticProtocol/keys/value    	| www.admin-shell.io/<br>interaction/registration 	| www.admin-shell.io/<br>interaction/registration 	| www.admin-shell.io/<br>interaction/registration 	| www.admin-shell.io/<br>interaction/registration 	|
| semanticProtocol/keys/ idType  	| IRI                                             	| IRI                                             	| IRI                                             	| IRI                                             	|
| type                           	| register                                        	| registerack                                     	| HeartBeat                                       	| HeartBeatAck                                    	|
| messageId                      	| Set by the AAS                                  	| Set by the RIC                                  	| Set by the AAS                                  	| Set by the RIC                                  	|
| sender/identification/id       	| Global unique ID                                	| VWS_RIC                                         	| Global unique ID                                	| VWS_RIC                                         	|
| sender/identification/idType   	| Set by the AAS                                  	| idShort                                         	| Set by the AAS                                  	| idShort                                         	|
| sender/role/name               	| Register                                        	| RegistryHandler                                 	| AASHeartBeatHandler                             	| HeartBeatHandler                                	|
| receiver/identification/id     	| VWS_RIC                                         	| Global unique ID                                	| VWS_RIC                                         	| Global unique ID                                	|
| receiver/identification/idType 	| idShort                                         	| Set by the AAS                                  	| idShort                                         	| Set by the AAS                                  	|
| receiver/role/name             	| RegistryHandler                                 	| Register                                        	| HeartBeatHandler                                	| AASHeartBeatHandler                             	|
| conversationId                 	| Set by the AAS                                  	| Same as register packet                         	| Set by the AAS                                  	| Same as in the HeartBeat                        	|
| interactionElements            	| AASiD part 2   Descriptor                       	| Empty List                                      	| Empty List                                      	| Empty List / Status Submodel                    	|

                    Table 1 I4.0 message details for register, registerack, HeartBeat, HeartBeatAck 

The replyTo field in the frame part of an I4.0 message indicates ALP of the receiver AAS, RIC utilizes this information to deliver the I4.0 message to appropriate receiver AAS. The replyBy element indicates the ALP over which the appropriate reply should be delivered by the receiver AAS. 


## Dependencies

This repository hosts the source code for RIC architecture, 

:one: The  code is written in Python 3.7 <br />
:two: All the Python dependencies are specified in the [requirements.txt](https://github.com/harishpakala/VWS_AAS_Registry/blob/main/requirements.txt) <br />
:three: AAS descriptors are represented in JSON format as specified in [AAS Detail Part 2](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part_2_V1.html), a new Json schema definition is created in accordance with  the AAS meta  model as specified in [AAS Detail Part 1](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part1_V3.html). The registration and modification requests are validated using this json schema.  <br />
:four: An external MQTT server is needed as part of MQTT plugin of the RIC.  <br />
:five: The LIA OVGU development uses eclipse editor, accordingly eclipse related project files are provided in the repository.
 
## Configuration
The source code is associated with a .env file, all the configuration variables are specified in it.
<pre><code>
LIA_AAS_RESTAPI_HOST_EXTERN=localhost               Ip address of the host on which the RIC is running (it is defaulted to localhost)
LIA_AAS_RESTAPI_PORT_INTERN=9021                    Port of the host system over which HTTP rest services can be accssed.
LIA_AAS_RESTAPI_PORT_EXTERN=9021                    In case of docker different external port can be used.
LIA_AAS_COAP_PORT_INTERN=5643                       Port of the host system over which coap rest services can be accssed.	
LIA_AAS_MQTT_HOST=localhost                         IP address of the MQTT server (external to RIC)
LIA_AAS_MQTT_PORT=1883                              Port of the external MQTT server 
LIA_PREFEREDI40ENDPOINT=MQTT                        The prefereed communication endpoint over which the RIC prefers to communicate
LIA_preferredCommunicationFormat=JSON               The prefeered communication format  (fixed to JSON)
</code></pre>

## Running 
1) The base python program is organized inside the src/main subdirectory.  <br/>
<strong>python3 vws_ric.py</strong> <br/>
2) As a docker container <br/>
<pre><code>docker pull harishpakala/vws-ovgu:python_aas_registry</code></pre> <br/>
<pre><code>docker run -e LIA_AAS_MQTT_HOST='localhost' -e LIA_AAS_RESTAPI_PORT_INTERN='9021' -e LIA_AAS_RESTAPI_PORT_EXTERN='9021' -e LIA_AAS_COAP_PORT_INTERN='50683' -e LIA_AAS_MQTT_PORT='1883' -p 9021:9021 -p 50683:50683/udp --name python_aas_registry_cont harishpakala/vws-ovgu:python_aas_registry</code></pre> <br/>
3) [Reference Implementation](https://vwsvernetzt.de/wp-content/uploads/2021/07/Reference_Implementation_VWSvernetzt_RIC_V1.pdf) <br/>

## AAS Registry Rest API Services
The table 2 provides list of rest servises the RIC as a registry provides, it also lists down the allowed operations for each of the service. The services are as per the guidelines of [AAS Detail Part 2](https://www.plattform-i40.de/PI40/Redaktion/DE/Downloads/Publikation/Details_of_the_Asset_Administration_Shell_Part_2_V1.html). 

{aas-identifier} = idShort or global unique identifier of AAS or global unique identifier of the aaset that the AAS is representing <br />
{submodel-identifier} = idShort or global unique identifier of Submodel <br />

|                         HTTP URI                                               |        GET         |        PUT         |       DELETE       |
|----------------------------------------------------------------------------------| ------------------ | ------------------ | ------------------ |
|<http://localhost:9021/registry/shellDescriptors>                                 | :heavy_check_mark: |       :x:          |      :x:           |  
|<http://localhost:9021/registry/shellDescriptors/{aas-identifier}>                   | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |              
|<http://localhost:9021/registry/shellDescriptors/{aas-identifier}/submodelDescriptors/>     | :heavy_check_mark: | :x: | :x: |              
|<http://localhost:9021/registry/descriptor/shellDescriptor> | :heavy_check_mark: |       :x:          |      :x:           |                

                    Table 2 AAS Registry rest services provided by the RIC


## Submodel Registry Rest API Services

|                         HTTP URI                                                 |        GET         |        PUT         |       DELETE       |
|----------------------------------------------------------------------------------| ------------------ | ------------------ | ------------------ |
|<http://localhost:9021/registry/submodelDescriptors>                              | :heavy_check_mark: |       :x:          |      :x:           |  
|<http://localhost:9021/registry/submodelDescriptors//{submodel-identifier}>       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |  
|<http://localhost:9021/registry/descriptor/submodelDescriptor>                       | :heavy_check_mark: |       :x:          |      :x:           |  
    
                    Table 3 Submodel Registry rest services provided by the RIC

## RIC ALP Interface Access
The MQTT client component of the RIC subscibes to the topic *AASpillarbox**. The registration, heartbeat and all other I4.0 messages that are to transported to another AAS should be posted to this topic. Similarly the I4.0 messages should be posted to the appropriate endpoint listed in the table 4.

| HTTP URI                          	| Type 	| Description                                           	|
|-----------------------------------	|------	|-------------------------------------------------------	|
| <http://localhost:9021/i40commu>  	| POST 	| Post an I4.0 message packet to HTTP server of the RIC 	|
| <coap://localhost:50683/i40commu> 	| POST 	| Post an I4.0 message packet to COAP server of the RIC 	|
                
                Table 4 HTTP and COAP endpoints of RIC for I4.o message communication


## Logs
The python project maintains a logger, all the important aspects regarding its functionality  are captured with logger. The entire log information is stored into .LOG files under the src &gt; main &gt; logs folder, in case of docker under logs (the log files will also be mapped to the host system, related mapping information is provided in the docker-compose.yml file).

## Issues
If you want to request new features or report bug [submit a new issue](https://github.com/admin-shell-io/python-aas-registry/issues/new)

## License

Python AAS Registry is Licensed under Apache 2.0, the complete license text including the copy rights is included under [License.txt](https://github.com/admin-shell-io/python-aas-registry/blob/main/LICENSE.txt)

* APScheduler,python-snap7,jsonschema,aiocoap,hbmqtt MIT License <br />
* Flask,werkzeug, Flask-RESTful, python-dotenv BSD-3-Clause <br />
* requests Apache License, Version 2.0 <br />
* paho-mqtt Eclipse Public License 2.0 and the Eclipse Distribution License 1.0 <br />
