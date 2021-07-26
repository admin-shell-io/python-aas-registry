	function _createtableRow(serverName,timestamp)
	{	
		var rowelement = document.createElement("tr");
		var serverCol = document.createElement("td");
		var timeStampCol = document.createElement("td");
		serverCol.innerHTML  = serverName;
		timeStampCol.innerHTML  = timestamp
		rowelement.appendChild(serverCol);
		rowelement.appendChild(timeStampCol);
		return rowelement
	}	
	function _createDataTable(statusDict)
	{
		var headerElement = document.getElementById("headerElem");
		headerElement.innerHTML  = "VWS Heart Beat Status Update " + new Date().toLocaleString().replace(',','');
		var entriesList = document.getElementById("entriesList");
		entriesList.innerHTML = "";
		for (var key in  statusDict)
			{
				childData = _createtableRow(key,statusDict[key]);
				entriesList.appendChild(childData);
			}
	}
	function documentLoad(connectstatusDict)
	{
		_createDataTable(connectstatusDict)
	}
	function statusRetrieval() {
		var httpGetRequest = new XMLHttpRequest();
		try {
			var httpGetRequest = new XMLHttpRequest();
			httpGetRequest.open('POST','/status');
			httpGetRequest.onload = () => {
				statusDict = JSON.parse(httpGetRequest.response);
				_createDataTable(statusDict)
			} 
			httpGetRequest.send();
			}catch (error) {
			  console.error(error);

			}
		  
		}
	var myVar = setInterval(statusRetrieval, 5000);
