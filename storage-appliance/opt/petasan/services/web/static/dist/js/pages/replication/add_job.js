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


    $(function () {

        $("[data-mask]").inputmask();
    });


    // shows the "CompressionAlg Div" in "Replicated Pool Div" on clicking the radiobutton "enabled" //
    // --------------------------------------------------------------------------------------------- //
    $("#rep_enabled").click(function () {
        $("#Rep_CompressionAlg").show();
    });

    // hides the "CompressionAlg Div" in "Replicated Pool Div" on clicking the radiobutton "disabled" //
    // ---------------------------------------------------------------------------------------------- //
    $("#rep_disabled").click(function () {
        $("#Rep_CompressionAlg").hide();
    });
    var dest_cluster_name_value = $("#dest_cluster_name").val();
    if (!dest_cluster_name_value) {
        $('#v').bind('click', false);
    }

});

function validDestCluster() {
    var dest_cluster_name = $("#dest_cluster_name");
    var dest_cluster_name_value = $("#dest_cluster_name").val();
    if (!dest_cluster_name_value) {
        $('#v').bind('click', false);
        $("#lblDestinationName").text(messages.add_job_lbl_dest_cluster_name_empty);
        dest_cluster_name.closest('.form-group').addClass('has-error');
        dest_cluster_name.focus();
    }
    else {
        $('#v').unbind('click', false);
        dest_cluster_name.closest('.form-group').removeClass('has-error');
        $("#lblDestinationName").html("Destination Cluster Name:" + "<font color='red'>*</font>");
    }

}


$(".btn_collapse").click(function () {
    $(".collapse").collapse('toggle');
    if ($("#mark").hasClass("fa-plus")) {
        $("#mark").removeClass("fa-plus");
        $("#mark").addClass("fa-minus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Advanced");
    } else if ($("#mark").hasClass("fa-minus")) {
        $("#mark").removeClass("fa-minus");
        $("#mark").addClass("fa-plus");
        $("#box_details_title").empty();
        $("#box_details_title").text("Advanced");
    }
});

//####################################################################################################################//
// When Submitting Form : //
//####################################################################################################################//

$("#addJob_form").submit(function (event) {

    // Validation of Job Name :
    // =========================
    var jobName = $("#job_name");
    var jobNameValue = $("#job_name").val();

    // check if empty //
    // -------------- //

    if (!jobNameValue) {
        $("#lblJobName").text(messages.add_job_lbl_name_empty);
        jobName.closest('.form-group').addClass('has-error');
        jobName.focus();
        event.preventDefault();
    }

    else if ((/^[a-zA-Z0-9- ,_]*$/.test(jobNameValue) == false)) {
        $("#lblJobName").text(messages.add_job_lbl_name_no_special_char);
        jobName.closest('.form-group').addClass('has-error');
        jobName.focus();
        event.preventDefault();
    }


    else {
        jobName.closest('.form-group').removeClass('has-error');
        $("#lblJobName").html("Name:" + "<font color='red'>*</font>");
    }

    // Validation of Service Node :
    // =========================
    var backup_node = $('#backup_node');
    var backup_node_value = $('#backup_node').val();

    // check if empty //
    // -------------- //

    if (backup_node_value == "") {
        $('#lblUseNode').text(messages.add_job_lbl_Use_node_null);
        backup_node.closest('.form-group').addClass('has-error');
        backup_node.focus();
        event.preventDefault();
    } else {
        backup_node.closest('.form-group').removeClass('has-error');
        $("#lblUseNode").html("Use Node:" + "<font color='red'>*</font>");

    }


    // Validation of Source Cluster iSCSI :
    // =========================
    var source_disk = $("#source_disk");
    var source_disk_value = $("#source_disk").val();

    // check if empty //
    // -------------- //

    if (!source_disk_value) {
        $("#lblSourceDisk").text(messages.add_job_lbl_src_iscsi_empty);
        source_disk.closest('.form-group').addClass('has-error');
        source_disk.focus();
        event.preventDefault();
    }


    else {
        source_disk.closest('.form-group').removeClass('has-error');
        $("#lblSourceDisk").html("Source Disk:" + "<font color='red'>*</font>");
    }


    // Validation of Destination cluster name :
    // =========================
    var dest_cluster_name = $("#dest_cluster_name");
    var dest_cluster_name_value = $("#dest_cluster_name").val();

    // check if empty //
    // -------------- //

    if (!dest_cluster_name_value) {
        $("#lblDestinationName").text(messages.add_job_lbl_dest_cluster_name_empty);
        dest_cluster_name.closest('.form-group').addClass('has-error');
        dest_cluster_name.focus();
        event.preventDefault();
    }


    else {
        dest_cluster_name.closest('.form-group').removeClass('has-error');
        $("#lblDestinationName").html("Destination Cluster Name:" + "<font color='red'>*</font>");
    }


    // Validation of Destination Cluster iSCSI :
    // =========================
    var destination_disk = $("#destination_disk");
    var destination_disk_value = $("#destination_disk").val();

    // check if empty //
    // -------------- //

    if (!destination_disk_value) {
        $("#lblIDestinationDisk").text(messages.add_job_lbl_dest_iscsi_empty);
        destination_disk.closest('.form-group').addClass('has-error');
        destination_disk.focus();
        event.preventDefault();
    }


    else {
        destination_disk.closest('.form-group').removeClass('has-error');
        $("#lblIDestinationDisk").html("Destination Disk:" + "<font color='red'>*</font>");
    }

    // Validation of Schedule :
    // =========================
    var selected_schedule = $("#selected_schedule");
    var selected_schedule_value = $("#selected_schedule").val();

    // check if empty //
    // -------------- //

    if (!selected_schedule_value) {
        $("#lblSchedule").text(messages.add_job_lbl_schedule_required);
        selected_schedule.closest('.form-group').addClass('has-error');
        selected_schedule.focus();
        event.preventDefault();
    }


    else {
        selected_schedule.closest('.form-group').removeClass('has-error');
        $("#lblSchedule").html("Schedule:" + "<font color='red'>*</font>");
    }

});

function set_cancel_add_job(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });
}