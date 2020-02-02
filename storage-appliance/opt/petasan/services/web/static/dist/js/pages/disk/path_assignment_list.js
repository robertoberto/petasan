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

/**
 * Created by root on 29/11/17.
 */

$('#status_assign').hide();

var no_of_paths = 0;

function loadPaths() {


    var count = 0;
    var moving = 0;
    var binding = 0;
    var succeeded = 0;
    var failed = 0;
    var all_data = {};
    var isAjaxDone = true;

    if (isAjaxDone != true) {
        return
    }
    isAjaxDone = false;

    $.get(get_disks_paths, function (data, status) {
        all_data = JSON.parse(data);
        no_of_paths = all_data.paths.length;

        var showStatus = true
        if (all_data['is_reassign_busy'] == true ) {
            $('#reassign_button').attr("disabled", "disabled");
            showStatus = true
            $('#status_assign').show();

        } else {

            $('#reassign_button').removeAttr("disabled");
            showStatus = false
            $('#status_assign').hide();

        }
        $.fn.clean();

        var data_ = {
            pathsData: all_data.paths,
            nodeList: all_data.nodes,
            showSelectCol: false,
            ShowStatusCol: showStatus
        };

        $.fn.paths(data_);

        if (status == "success") {
            isAjaxDone = true;
        } else {
            isAjaxDone = true;
        }

        for(i in all_data['paths']){
            paths_status = all_data['paths'][i]['status'];
            if (paths_status >= 0){
                count++;
                switch (paths_status) {
                    case 0:
                        moving++;
                        break;
                    case 1:
                        binding++;
                        break;
                    case 2:
                        succeeded++;
                        break;
                    case 3:
                        failed++;
                        break;

                }
            }
        }
        $('#total').html("");
        $('#moved').html("");
        $('#failed').html("");
        $('#moving').html("");
        $('#pending').html("");

        $('#total').append("Total: "+count);
        $('#moved').append("Moved: "+succeeded);
        $('#failed').append("Failed: "+failed);
        $('#moving').append("Moving: "+moving);
        $('#pending').append("Pending: "+binding);

        if(no_of_paths == 0){
            $('#reassign_button').attr("disabled", "disabled");
        }



    });



}


$(document).ready(function () {
    loadPaths();
    setInterval(loadPaths, 10000);

});