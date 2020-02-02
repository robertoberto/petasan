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

$(document).ready(function () {
    var do_ajax = $("#do_ajax").val();
    if (do_ajax.length == 0) {
        getTemplate($('#tuning_template').val());
    }
    else if (do_ajax.length > 0) {
        get_template_details();
    }

});

function get_template_details() {
    console.log($('#tuning_template').val());
    if ($('#tuning_template').val().length > 0) {
        $(".collapse").collapse('show');
        $("#mark").removeClass("fa-plus");
        $("#mark").addClass("fa-minus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Hide Details");
    }
}

$("#tuning_template").change(function () {
    getTemplate($('#tuning_template').val());
    console.log($('#tuning_template').val());
    if ($('#tuning_template').val() == 'custom') {
        $(".collapse").collapse('show');
        $("#mark").removeClass("fa-plus");
        $("#mark").addClass("fa-minus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Hide Details");
    }
});

$(".btn_collapse").click(function () {
    $(".collapse").collapse('toggle');
    if ($("#mark").hasClass("fa-plus")) {
        $("#mark").removeClass("fa-plus");
        $("#mark").addClass("fa-minus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Hide Details");
    } else if ($("#mark").hasClass("fa-minus")) {
        $("#mark").removeClass("fa-minus");
        $("#mark").addClass("fa-plus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Show Details");
    }
});

function getTemplate(template_name) {
    $.ajax({
        url: "/get_tuning_template/" + template_name,
        type: "get",
        success: function (data) {
            var template_data = JSON.parse(data);
            $('#ceph_script').val(template_data['ceph_tunings']);
            $('#lio_script').val(template_data['lio_tunings']);
            $('#post_deploy_script').val(template_data['post_deploy_script']);
        },
        error: function () {
        }
    });
}

$("#tuning_config").submit(function (event) {
    if ($('#validate').val() != 'false') {
        //check cluster size
        var cluster_size_lbl = $("#cluster_size");
        var cluster_size = $("#cluster_size").val();
        if (cluster_size == undefined || cluster_size == null || cluster_size == 0) {
            $("#lblClusterSize").text(messages.save_tuning_setting_lbl_cluster_size_empty);
            cluster_size_lbl.closest('.form-group').addClass('has-error');
            cluster_size_lbl.focus();
            event.preventDefault();
        }
        else {
            cluster_size_lbl.closest('.form-group').removeClass('has-error');
            $("#lblClusterSize").html("Cluster Size:" + "<font color='red'>*</font>");
        }
    }
});