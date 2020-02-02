/*
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
 */


var Validatation = {
	firstlevel : 0,
	secondlevel : 1,
	thirdlevel : 2,
	fourthlevel : 3,
///
// test ip address in subnet mask and parent ip address 
//
///	
	checkip : function (mainIP, subnetMask, ipAddress) {
		//var ipaddress = document.getElementById("ip").value;
		if (this.validateIP(ipAddress)) {

			var pattForZeroTo255 = "(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5])";
			var mainPattern = "";
			subnetMaskArr = subnetMask.split(".");
			ipAddressArr = mainIP.split(".");
			var subnetMaskRange = this.getRangeSubnetMask(subnetMask);
			//alert(subnetMaskRange);
			switch (subnetMaskRange) {
			case this.firstlevel:
				for (var c = 0; c <= 3; c++) {
					if (c == 0) {
						mainPattern += "\^" + pattForZeroTo255;
					} else {
						mainPattern += "\\." + pattForZeroTo255;
					}
				}
				//alert(mainPattern);
				break;
			case this.secondlevel:
				mainPattern += ipAddressArr[0];
				//alert(ipAddressArr[0]);
				for (c = 1; c <= 3; c++) {

					mainPattern += "\\." + pattForZeroTo255;
				}
				break;
			case this.thirdlevel:
				//alert(ipAddressArr[0]);
				mainPattern += "^" + ipAddressArr[0] + "\\." + ipAddressArr[1];
				for (c = 2; c <= 3; c++) {
					mainPattern += "\\." + pattForZeroTo255;
				}
				break;
			case this.fourthlevel:
				//alert(ipAddressArr[0]);
				mainPattern += "^" + ipAddressArr[0] + "\\." + ipAddressArr[1] + "\\." + ipAddressArr[2];
				for (c = 3; c <= 3; c++) {
					mainPattern += "\\." + pattForZeroTo255;
				}
				break;

			}
			mainPattern = mainPattern + "$"
				var match2 = ipAddress.match(mainPattern);

			if (match2 == null) {
				alert("Please review your Subnet Mask!");
				//return false;
			} else {
				alert("success");
				//return false;
			}
		}
	},
	getRangeSubnetMask : function (subnetMask) {
		var result = 0;
		//Check Format
		subnetMaskArray = subnetMask.split(".");

		//Check Numbers
		for (var c = 0; c <= 3; c++) {
			//Perform Test
			if (subnetMaskArray[c] == 0) {
				result = c;
				//result=subnetMasklevel.
				break;
			}
		}
		return result;
	},
	validateIP : function (ip) {
		//Check Format
		var ip = ip.split(".");

		if (ip.length != 4) {
			return false;
		}

		//Check Numbers
		for (var c = 0; c < 4; c++) {
			//Perform Test
			if (ip[c] <= -1 || ip[c] > 255 ||
				isNaN(parseFloat(ip[c])) ||
				!isFinite(ip[c]) ||
				ip[c].indexOf(" ") !== -1) {

				return false;
			}
		}
		return true;
	}

};
Validatation.checkip("192.168.0.0", "255.0.0.0", "68.20.20.123");
Validatation.checkip("192.168.0.0", "255.255.255.0", "192.23.20.123");
Validatation.checkip("192.168.0.0", "255.255.0.0", "192.23.20.123");
Validatation.checkip("192.168.0.0", "255.0.0.0", "192.20.20.123");
Validatation.checkip("192.168.0.0", "0.0.0.0", "192.20.20.123");

Validatation.checkip("192.168.0.0", "255.0.0.0", "68.20.20.123");



// validate with range min and max 

var ValidatationInRange  = {
	firstlevel : 0,
	secondlevel : 1,
	thirdlevel : 2,
	fourthlevel : 3,

	checkip : function (mainIP, maxIP, minIP, subnetMask) {
		//var ipaddress = document.getElementById("ip").value;
		if (this.validateIP(mainIP)) {
			var pattForZeroTo255 = "(?:[0-9]{1,2}|1[0-9]{2}|2[0-4][0-9]|25[0-5])";
			var mainPattern = "";
			mainIPSplitted = mainIP.split(".");
			maxIpSplitted = maxIP.split(".");
			minIpSplitted = minIp.split(".");
			var subnetMaskRange = this.getRangeSubnetMask(subnetMask);
			switch (subnetMaskRange) {
			case this.firstlevel:
				for (var c = 0; c <= 3; c++) {
					if (c == 0) {
						mainPattern += "\^" + pattForZeroTo255;
					} else {
						mainPattern += "\\." + pattForZeroTo255;
					}
				}

				break;
			case this.secondlevel:
				mainPattern += maxIpSplitted[0];
				for (c = 1; c <= 3; c++) {
					mainPattern += "\\." + pattForZeroTo255;
				}
				break;
			case this.thirdlevel:

				mainPattern += "^" + maxIpSplitted[0] + "\\." + maxIpSplitted[1];
				for (c = 2; c <= 3; c++) {
					mainPattern += "\\." + pattForZeroTo255;
				}
				break;
			case this.fourthlevel:
				mainPattern += "^" + maxIpSplitted[0] + "\\." + maxIpSplitted[1] + "\\." + mainIPSplitted[2];
				for (c = 3; c <= 3; c++) {
					mainPattern += "\\." + pattForZeroTo255;
				}
				break;

			}
			mainPattern = mainPattern + "$";
			var match = mainIP.match(mainPattern);

			if (match == null) {
				alert("Please review your Subnet Mask!");
			} else {

				switch (subnetMaskRange) {
				case this.firstlevel:
					for (var c = this.firstlevel; c <= 3; c++) {
						if (!(mainIPSplitted[c] > minIpSplitted[c] && mainIPSplitted[c] < maxIpSplitted[c])) {
							alert("failed");
							return false;
						}
					}
					break;
				case this.secondlevel:
					for (var c = this.secondlevel; c <= 3; c++) {
						alert("ip is" + mainIPSplitted[c] + " min is " + minIpSplitted[c] + " max is " + maxIpSplitted[c]);
						if (!(mainIPSplitted[c] > minIpSplitted[c] && mainIPSplitted[c] < maxIpSplitted[c])) {

							alert("failed");
							return false;
						}
					}
					break;
				case this.thirdlevel:
					for (var c = this.thirdlevel; c <= 3; c++) {
						alert("ip is" + mainIPSplitted[c] + " min is " + minIpSplitted[c] + " max is " + maxIpSplitted[c]);
						if (!(mainIPSplitted[c] > minIpSplitted[c] && mainIPSplitted[c] < maxIpSplitted[c])) {
							alert("failed");
							return false;
						}
					}
					break;
				case this.fourthlevel:
					for (var c = this.fourthlevel; c <= 3; c++) {
						if (!(mainIPSplitted[c] > minIpSplitted[c] && mainIPSplitted[c] < maxIpSplitted[c])) {
							alert("failed");
							return false;
						}
					}
					break;

				}
				alert("success");

			}
		}
	},
	getRangeSubnetMask : function (subnetMask) {
		var result = 0;

		subnetMaskSplitted = subnetMask.split(".");

		//Check Numbers
		for (var c = 0; c <= 3; c++) {
			//Perform Test
			if (subnetMaskSplitted[c] == 0) {
				result = c;
				//result=subnetMasklevel.
				break;
			}
		}
		return result;
	},
	validateIP : function (ip) {

		var ip = ip.split(".");

		if (ip.length != 4) {
			return false;
		}

		//Check Numbers
		for (var c = 0; c < 4; c++) {
			//Perform Test
			if (ip[c] <= -1 || ip[c] > 255 ||
				isNaN(parseFloat(ip[c])) ||
				!isFinite(ip[c]) ||
				ip[c].indexOf(" ") !== -1) {

				return false;
			}
		}
		return true;
	}

};
//Validatation.checkip("192.168.0.0","192.168.255.255", "255.0.0.0", "68.20.20.123");
//Validatation.checkip("192.168.0.0","192.168.255.255", "255.255.255.0", "192.23.20.123");
ValidatationInRange.checkip("192.168.10.10", "192.168.255.255", "192.168.0.0", "255.255.0.0");
//Validatation.checkip("192.168.0.0","192.168.255.255", "255.0.0.0", "192.20.20.123");
//Validatation.checkip("192.168.0.0","192.168.255.255", "0.0.0.0", "192.20.20.123");
//Validatation.checkip("192.168.0.0","192.168.255.255", "255.0.0.0", "68.20.20.123");
