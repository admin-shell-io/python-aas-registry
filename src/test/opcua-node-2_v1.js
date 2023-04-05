"use strict";
const {
    OPCUAServer,
    Variant,
    DataType,
    nodesets,
    StatusCodes,
    VariantArrayType,
    ServerEngine
} = require("node-opcua");
const os = require("os");

function constructPADIMAddressSpace(padimserver) {

    const addressSpace = padimserver.engine.addressSpace;
    const namespace = addressSpace.getOwnNamespace();

	const PADIMType = addressSpace.findObjectType("4:PADIMType");

    const TH400 = PADIMType.instantiate({
        browseName: "ABB_TTF_300",
		modellingRule:"Mandatory",
		optionals: ["SignalSet","DateOfLastChange","DeviceHealthAlarms","DisplayLanguage","FactoryReset","SubDevices",""],
		organizedBy: padimserver.engine.addressSpace.rootFolder.objects
    });

}

var uaNodeSetFile ="./Opc.Ua.NodeSet2.xml";
var diNodeSetFile ="./Opc.Ua.Di.NodeSet2.xml";
var irdiNodeSetFile ="./Opc.Ua.IRDI.NodeSet2.xml";
var padimNodeSetFile ="./Opc.Ua.PADIM.NodeSet2.xml";

var server_options = {
   hostname: "localhost",
   port: 4850,

   allowAnonymous: false,
   resourcePath: "/UA/PADIM",
   maxAllowedSessionNumber: 100,
   timeout: 1500000,
   maxConnectionsPerEndpoint: 100,
   nodeset_filename: [
     uaNodeSetFile,
     diNodeSetFile,
     irdiNodeSetFile,
	 padimNodeSetFile
   ],
	buildInfo : {
        productName: "PADIM Base Server",
        buildNumber: "2404",
		manufacturerName: "OVGU LIA",
		softwareVersion: "padim-opcua",
        buildDate: new Date(2021,4,24)
	},
	securityModes:[1],
	
};

(async () => {

    try {
		//Creating the server 
        const _padimserver = new OPCUAServer(server_options);
		//Initializing the server
        await _padimserver.initialize();
		//creating the address space
        constructPADIMAddressSpace(_padimserver);
		// starting the server
        await _padimserver.start();

        process.on("SIGINT", async () => {
            await _padimserver.shutdown();
            console.log("terminated");

        });
    } catch (err) {
        console.log(err);
        process.exit(-1);
    }
})();