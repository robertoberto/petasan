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
 * Created by root on 03/12/17.
 */

var no_of_paths = 0;
var isAjaxDone = true;
function loadPaths() {

    if (isAjaxDone != true) {
        return;
    }
    isAjaxDone = false;

    $.get(get_disks_paths, function (data, status) {

        all_data = JSON.parse(data);


        for (var i = 0; i < all_data['nodes'].length; i++) {
            $('#nodes').append("<option value=" + all_data.nodes[i]  + ">" + all_data.nodes[i] + "</option>");

        }

        no_of_paths = all_data.paths.length;

        var data_ = {
            pathsData: all_data.paths,
            nodeList: all_data.nodes,
            showSelectCol: true,
            ShowStatusCol: false
        };


        $.fn.paths(data_);

        //$.fn.getSelectedPaths();

        if (status == "success") {
            isAjaxDone = true;
        } else {
            isAjaxDone = true;
        }
        $('#assign_Validation_false').hide();
        $('#search_path_fail').hide();

    });


}


function onChangeSearchOptions(){
    if($('#search_by_name_radio').prop("checked") == true ){
        $("#ip").prop('disabled', true);
        $("#name").prop('disabled', false);
    }else if($('#search_by_ip_radio').prop("checked") == true ){
        $("#name").prop('disabled', true);
        $("#ip").prop('disabled', false);
    }
}


$(document).ready(function () {
    $(window).keydown(function(event){
        if (event.keyCode == 13) {
            event.preventDefault();
            return false;
        }
    });

    loadPaths();
    $(function () {
        $("[data-mask]").inputmask();
    });

});


function onSearchPaths(event) {
    $('#search_path_fail').hide();
    $('#assign_Validation_false').hide();
    var URL = "";
    if ($('#search_by_name_radio').prop("checked") == true && $('#name').val() != "") {
        $('#ip').val("");
        var disk_name = $('#name').val();
        URL = get_disks_paths_by_name + disk_name;

    }
    else if ($('#search_by_ip_radio').prop("checked") == true && $('#ip').val() != "") {
        $('#name').val("");
        var ip = $('#ip').val();
        URL = get_disks_paths_by_ip + ip;

    } else {
        //$('#search_path_fail').show();
        event.preventDefault();
    }

    $.get(URL , function (data, status) {
        if (data.indexOf('Sign in') != -1) {
                window.location.href = loginUrl;
            }
            all_data_by_name = JSON.parse(data);
            if (all_data_by_name.is_reassign_busy == true){
                window.location.href = paths_redirect_search_button;
            }
            var data_name = {
                pathsData: all_data_by_name.paths,
                nodeList: all_data_by_name.nodes,
                showSelectCol: true,
                ShowStatusCol: false
            };
            $.fn.clean();

            $.fn.paths(data_name);
            console.log(data_name);
        });
    



}
$('#assign_manual').prop("checked", true);

function onChangeSearchSection() {
    if ($('#assign_manual').prop("checked") == true) {
        $('#paths_table').show();
        $('#search_section').show();
        $('#assign_to').show();
        $('#expand_and_collapse_buttons').show();
        $('#paths_table').show();
        $('#count_distribution').prop("checked", false);
        $('#path_count_distribution').hide();
        $('#search_by_name_radio').prop("checked" , true);
        $("#name").prop('disabled', false);
        $("#ip").prop('disabled', true);
    } else {
        $('#expand_and_collapse_buttons').hide();
        $('#paths_table').hide();
        $('#ip').val("");
        $('#name').val("");
        $('#search_by_ip_radio').prop("checked", false);
        $('#search_by_name_radio').prop("checked", false);
        $('#search_section').hide();
        $('#assign_to').hide();
        $('#count_distribution').prop("checked", true);
        $('#path_count_distribution').show();
    }
}


$("#assign_form").click(function (event) {
    $('#search_path_fail').hide();
    if ($('#assign_manual').prop("checked") == true) {
        var count = $.fn.getSelectedPaths();
        var node_name = $('#nodes').val();

        if(count.length > 0){
            for(var i in count){
                if(count[i].includes(node_name+"#")){
                    $('#error_message').text(" "+messages_node_validation);//message
                    $('#assign_Validation_false').show();
                    event.preventDefault();
                }
        }
            $("#form_submit").attr("action", send_manual_paths);
        }else
        {
            $('#error_message').text(" "+messages_select_paths_validation);//message
            $('#assign_Validation_false').show();
            event.preventDefault();
        }


    } else if ($('#assign_automatic').prop("checked") == true) {
            if (no_of_paths == 0){
               event.preventDefault();
         }
        console.log(no_of_paths)
        var type = 1;
        $("#form_submit").attr("action", send_auto_paths + type);
    } else {
        $('#error_message').text(" "+messages_select_paths_type_validation);//message
        $('#assign_Validation_false').show();
        event.preventDefault();
    }
});

