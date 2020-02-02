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

function ajaxd() {

    $.ajax({
        url: "/build",
        type: "get",
        success: function (data) {


            var statusData = JSON.parse(data);
            var status_report = statusData["report_status"];
            var management_urls = statusData["management_url"]
            var node_number = statusData["node_num"]
            console.log(status_report);
            console.log("node number = "+node_number+" ");

            var status_data = status_report.join("<br />");
            //for (i = 0; i < status_report.length; i++) {
            //   status_report += status_report[i] + "<br>";
            //}
//                var reportText =""
//                for( i=0; i<status_report.length; i++ )
//{
//        reportText   =  status_report[i] + '<br />';
//}

            var status = statusData["status"];
            console.log(status);
            if (status == 1) {

                $('#sucessDone').show();
                $('#warning').hide();
                $('#img').hide();
                $('#urlMsg').show();
                 $('#managementUrls').show();
                $('#managementUrl2').show();
                $('#managementUrl3').show();
                $('#urls1').text(management_urls[0])
                $('#urls2').text(management_urls[1])
                $('#urls3').text(management_urls[2])
                $('#urls1').attr("href",management_urls[0]);
                $('#urls2').attr("href",management_urls[1]);
                $('#urls3').attr("href",management_urls[2]);


                    //urls.href += management_urls[i];


                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);

                }
            }


            else if (status == 2) {
                $('#sucessOneManagement').show();
                $('#warning').hide();
                $('#img').hide();
                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);

                }
            }
            else if (status == 3) {
                $('#sucessTwoManagement').show();
                $('#warning').hide();
                $('#img').hide();
                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);

                }

            }

            else if (status == 5) {
                $('#sucessDoneJoined').show();
                $('#warning').hide();
                $('#img').hide();
                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);

                }

            }
            else if(status == 6)
            {

                $('#sucessDoneReplaced').show();
                $('#warning').hide();
                $('#img').hide();
                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);

                }

            }
            else if (status < 0) {
                if (node_number == 3)
                {
                    $('#error').show();
                    $('#StateAll').show();
                }
                else
                {
                    $('#error_deploy').show();
                }
                $('#warning').hide();
                $('#img').hide();

                console.log(status_report);
                if (status_report.length != 0) {
                    $('#report_status').show();
                    $('#errorList').show();
                    $("#reportStatus").html(status_data);


                }
            }


        },
        error: function () {

        }
    });
}
$(document).ready(function () {
    $('#warning').show();
    $('#img').show();
    ajaxd();

});

