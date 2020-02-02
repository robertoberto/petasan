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

function load_job_info(get_job_info_url) {

    $('#jobInfoArea').hide();
    $('#img_loading').show();


    $.ajax({
        url: get_job_info_url,
        type: "get",
        success: function (data) {

            var job_data = JSON.parse(data);
            $('#job_name').html(job_data['job_name']);
            $('#node_name').html(job_data['node_name']);
            $('#source_cluster_name').html(job_data['source_cluster_name']);
            $('#source_disk_id').html(job_data['source_disk_id']);
            if (job_data['compression_algorithm'].length > 0) {
                $('#compression').html('Enabled');
                $('#compression_algorithm_info').show();
                $('#compression_algorithm').html(job_data['compression_algorithm']);
            }
            else {
                $('#compression').html('Disabled');
                $('#compression_algorithm_info').hide();
            }

            selected_schedule = get_text(job_data['schedule']);
            $('#pre_snap_url').html(job_data['pre_snap_url']);
            $('#post_snap_url').html(job_data['post_snap_url']);
            $('#post_job_complete').html(job_data['post_job_complete']);
            $('#schedule').html(selected_schedule);
            $('#destination_cluster_name').html(job_data['destination_cluster_name']);
            $('#destination_disk_id').html(job_data['destination_disk_id']);

            $('#img_loading').hide();
            $('#jobInfoArea').show();
            if (job_data['pre_snap_url'] || job_data['post_snap_url'] || job_data['post_job_complete']) {
                $(".collapse").collapse('show');
                $("#mark").hasClass("fa-plus");
                $("#mark").removeClass("fa-plus");
                $("#mark").addClass("fa-minus");
                $("#box_details_title").empty();
                $("#box_details_title").text("Advanced");

            }

        },
        error: function () {

        }

    });

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


$(document).ready(function () {


});