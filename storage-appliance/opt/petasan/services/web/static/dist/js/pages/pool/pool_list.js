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

var is_finished = true;
var is_finished1 = true;
var delete_job_id = 0;

$(document).ready(function () {


    if ($("#delete_job_id").val() > 0) {
        delete_job_id = $("#delete_job_id").val().trim();
        pool_name = $("#pool_name").val().trim();
        setInterval("isDeleteFinished (delete_job_id)", 10000);  // call every 10 seconds
        loadPoolStatus(pool_name);
    }
    else {
        setInterval("loadPoolStatus('')", 15000);
    }

});

function isDeleteFinished(id) {

    if (is_finished == false)
            {
                console.log("wait")
                return
            }
    is_finished = false

    $.ajax({
        url: "/configuration/pools/get_delete_status/" + id,
        type: "get",
        success: function (data) {
            var deleted_status = JSON.parse(data);
            if (deleted_status) {

                base_url = $("#base_url").val().trim();

                indx = base_url.indexOf("pools");
                base_url = base_url.substring(0, indx + 6);
                $("#delete_job_id").attr("value", 0);

                window.location.href = base_url;

            }
            is_finished = true
        },
        error: function () {
        }
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function loadPoolStatus(deleted_pool) {

    if (is_finished1 == false)
    {
        console.log("wait")
        return
    }
    is_finished1 = false

    var d = new Date();
    console.log("start ajax >> " + d.toUTCString());
    $.ajax({
        url: "/configuration/pools/get_pool_status",
        type: "get",
        success: function (data) {
            //console.log("Ajax returns from server ...");

            var pools_list = JSON.parse(data);


            //console.log("pools list = " + pools_list["pools"][0]["name"]);
            //console.log("pools list = " + pools_list["actives"][0]);


            $("tr.pool").each(function () {

                $this = $(this);
                pool_name = $this.find('.name').text().trim();
                //console.log("pool_name = " + pool_name);


                if (pool_name !=  deleted_pool ) {

                    $('#status_' + pool_name).html("<span class='badge bg-stop'>Inactive</span>");

                    for (var index in pools_list["actives"]) {

                        if (pool_name == pools_list["actives"][index]) {

                            $('#status_' + pool_name).html("<span class='badge bg-started'>Active</span>");
                            break;
                        }
                    }

                }
                else {
                    $('#status_' + pool_name).html("<span class='badge bg-pending'>Deleting</span>");
                }


            });
            is_finished1 = true
        },
        error: function () {
        }
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function load_popup_info(get_pool_info_url) {

    $('#poolInfoArea').hide();
    $('#img').show();


    $.ajax({
        url: get_pool_info_url,
        type: "get",
        success: function (data) {

            // get_pool_info_url  --> '/pool/<pool_name>'  --> after split -->  ['','pool','<pool_name>']  --> the second element ..
            var pool_name = get_pool_info_url.split('/')[2];
            var pool_data = JSON.parse(data);
            console.log(pool_data);

            $('#poolInfo_NameValue').html(pool_data['name']);
            $('#poolInfo_TypeValue').html(pool_data['type']);
            $('#poolInfo_NumberOfPGsValue').html(pool_data['pg_num']);
            $('#poolInfo_NumberOfReplicasValue').html(pool_data['size']);
            $('#poolInfo_MinimumReplicasValue').html(pool_data['min_size']);

            if (pool_data['compression_mode'] != 'none')
            {
                $('#poolInfo_CompressionValue').html('Enabled');
                $('#poolInfo_CompressionAlg').show();
                $('#poolInfo_CompressionAlgValue').html(pool_data['compression_algorithm']);
            }
            else if  (pool_data['compression_mode'] == 'none')
            {
                $('#poolInfo_CompressionValue').html('Disabled');
                $('#poolInfo_CompressionAlg').hide();
            }

            $('#poolInfo_RuleNameValue').html(pool_data['rule_name']);


            $('#img').hide();
            $('#poolInfoArea').show();

        },
        error: function () {

        }

    });

}
