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

var is_finished = true

$(document).ready(function () {
    var ceph_summary_list;
    getClusterStatus();
    setInterval(getClusterStatus, 15000);

    $("[data-toggle='tooltip']").click(function () {
        if ($(this).attr('data-original-title') == 'Collapse') {
            $(this).attr('data-original-title', 'Expand');
        } else {
            $(this).attr('data-original-title', 'Collapse');
        }
    });


});




function fmtBytes(bytes) {
    if (bytes == 0) {
        return "0 bytes";
    }
    var s = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'];
    var e = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, e)).toFixed(2) + " " + s[e];

}


function getClusterStatus() {
    if (is_finished == false)
            {
                console.log("wait")
                return
            }
    is_finished = false

    $.ajax({
        url: "/dashboard",
        type: "get",
        success: function (data) {
            is_finished = true

            if (data.indexOf('Sign in') != -1) {
                window.location.href = loginUrl;
            }
            // *First data part is storage capacity*
            var storageData = JSON.parse(data.split("##")[0]);



            // *Second data part is maintenance mode ON/OFF*
            if (data.split("##")[1] == 1) { //maintenance_mode = 'ON'

                maintenance_mode = '<span class="text-red cluster-status">On</span>';

            } else { //maintenance_mode = 'OFF'

                maintenance_mode = '<span  class="text-green cluster-status" >Off</span>' +
                    '';
            }
            $('#maintenance_status').empty()
            $('#maintenance_status').append(maintenance_mode)
            writeSpeed = fmtBytes(storageData['pgmap']['write_bytes_sec'] || 0);
            writeSpeedSplit = writeSpeed.split(" ")
            $("#WritePerSecond").text(writeSpeedSplit[0]);
            $('#perSecond').html(writeSpeedSplit[1] + "/PerSecond");
            opsPerSecond = storageData['pgmap']['op_per_sec'] || 0;
            $("#WriteOpsPerSecond").text(opsPerSecond);
            var totalDisks = storageData["osdmap"]["osdmap"]["num_osds"];
            var upDisks = storageData["osdmap"]["osdmap"]["num_up_osds"];
            var downDisks = totalDisks - upDisks;
            bytesTotal = storageData["pgmap"]["bytes_total"];
            bytesUsed = storageData["pgmap"]["bytes_used"];
            if (bytesTotal == 0) {
                bytesUsed = 0;
                percentUsed = 0;
                availableStorage = 0;
            } else {
                percentUsed = ((bytesUsed / bytesTotal) * 100).toFixed(2);
                availableStorage = 100 - percentUsed;

            }
            var ceph_status_overall;
            if (storageData['health'].hasOwnProperty('overall_status')){
                ceph_status_overall = storageData['health']['overall_status'];
            } else{
                ceph_status_overall = storageData['health']['status'];
            }

            var ceph_status = storageData['health']['status'];
            ceph_summary_list = storageData['health']['summary'];

            ceph_health_obj = storageData['health'];
            console.log(ceph_health_obj);
            console.log(ceph_status)

            $("#availableStorage").val(availableStorage);
            $("#utilization_info").html(fmtBytes(bytesUsed) + " / " + fmtBytes(bytesTotal) + " (" + percentUsed + "%)");
            $("#total").html(totalDisks);
            $("#up").html(upDisks);
            $("#down").html(downDisks);
            $(".knob").knob({
                change: function (value) {
                    console.log("change : " + value);
                },
                release: function (value) {
                    console.log("release : " + value);
                },
                cancel: function () {
                    console.log("cancel : " + this.value);
                }
            });
            if (ceph_status_overall == 'HEALTH_OK') {
                $("#ceph_health").empty();
                $("#ceph_health").append('<span class="text-green cluster-status">OK <i class="fa fa-check text-green"></i></span>');
            } else if (ceph_status_overall == 'HEALTH_ERR') {
                $("#ceph_health").empty();

                $("#ceph_health").append("<a href='#' data-toggle='modal' data-target='#modal-default' onclick='return get_details();'> " +
                    '<span class="text-red cluster-status" style="">Error <i  class="fa text-red fa-ban"></i></span>' +
                    "</a>");
            } else if (ceph_status_overall == 'HEALTH_WARN' && ceph_status == 'HEALTH_WARN') {
                $("#ceph_health").empty();
                $("#ceph_health").append("<a href='#' data-toggle='modal' data-target='#modal-default' onclick='return get_details();'> " +
                    '<span class="text-yellow cluster-status" >Warning <i class="fa text-yellow fa-warning"></i></span>' +
                    "</a>");


            } else if (ceph_status_overall == 'HEALTH_WARN' && ceph_status == 'HEALTH_OK') {
                $("#ceph_health").empty();
                $("#ceph_health").append('<span class="text-green cluster-status">OK <i class="fa fa-check text-green"></i></span>');


            }
        },
        error: function () {
            is_finished = true
        }
    });
}


function get_details() {
    $("#modal_body").empty();
    if ('checks' in ceph_health_obj) {

        for(var key in ceph_health_obj['checks']){
            if(ceph_health_obj['checks'].hasOwnProperty(key)){
                 $("#modal_body").append("<label>" + ceph_health_obj['checks'][key]['summary']['message'] + "</label><br>");
            }

        }

    } else {
        for (var i = 0; i < ceph_summary_list.length; i++) {
            $("#modal_body").append("<label>" + ceph_summary_list[i]['summary'] + "</label>");
            if (i != ceph_summary_list.length - 1) {
                $("#modal_body").append("<br>");
            }
        }
    }

}