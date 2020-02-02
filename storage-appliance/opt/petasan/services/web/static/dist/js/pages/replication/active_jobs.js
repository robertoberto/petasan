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
    load_active_jobs_list();
    setInterval(load_active_jobs_list, 10000);

});

var isAjaxDone = true;

function load_active_jobs_list(){

    if (isAjaxDone != true) {
        return false;
    }

    isAjaxDone = false;

    $.ajax({
        url:'/replication/active_jobs_list',
        type:"get",
        success:function(data){
            $('#active_jobs_area').html("");
            var body = '<table id="activeJobsList" class="table table-bordered table-striped table-align-mid nowrap" style="table-layout: fixed">'+
                        '<thead>'+
                            '<tr>'+
                                '<th style="vertical-align:middle">Id</th>'+
                                '<th style="vertical-align:middle">Name</th>'+
                                '<th style="vertical-align:middle">Start Time</th>'+
                                '<th style="vertical-align:middle">Elapsed Time</th>'+
                                '<th style="vertical-align:middle">Transfer Rate</th>'+
                                '<th style="vertical-align:middle">Transferred</th>'+
                                '<th style="vertical-align:middle">Compression</th>'+
                                '<th style="vertical-align:middle">Progress</th>'+
                                '<th style="vertical-align:middle">Actions</th>'+
                            '</tr>'+
                        '</thead>'+'<tbody id="activeJobsListBody">';

            if(data.length > 0){
                jobs = JSON.parse(data);
                for(job in jobs){
                    body = body + '<tr>';
                    body = body + '<td>' + jobs[job].job_id.split('-')[0] + '</td>';
                    body = body + '<td>' + jobs[job].job_name + '</td>';
                    body = body + '<td>' + jobs[job].start_time + '</td>';
                    body = body + '<td>' + jobs[job].elapsed_time + ' hh:mm' + '</td>';
                    body = body + '<td>' + jobs[job].uncompressed_transferred_rate + '</td>';
                    body = body + '<td>' + jobs[job].uncompressed_transferred_bytes + '</td>';
                    body = body + '<td>' + jobs[job].compression_ratio + '</td>';
                    body = body + '<td>' + jobs[job].progress + '</td>';
                    body = body + '<td>'+
                        '<div title="Cancel Job" class="btn-group ">'+
                        '<form action="" id='+jobs[job].job_id+' method="post">'+
                        '<button type="submit" class="btn btn-default" id='+jobs[job].job_id+'#'+jobs[job].job_name+' onclick="return doDeleteActiveJob(id);" >'+
                        '<i class="fa fa-remove"></i></button></form></div></td>';
                }

            }

                body = body + '</tbody> </table>';
                $('#active_jobs_area').html(body);
                $('#active_jobs_area').show();
                $('#img').hide();
            $(function () {
                    $("#activeJobsList").DataTable({
                        "columnDefs": [
                            {"orderable": false, "targets": [8]}
                        ]
                    });
                });

            isAjaxDone = true;
        },
        error:function(data){
            $('#active_jobs_area').html("");
            var body = '<table id="activeJobsList" class="table table-bordered table-striped table-align-mid nowrap" style="table-layout: fixed">'+
                        '<thead>'+
                            '<tr>'+
                                '<th style="vertical-align:middle">Id</th>'+
                                '<th style="vertical-align:middle">Name</th>'+
                                '<th style="vertical-align:middle">Start Time</th>'+
                                '<th style="vertical-align:middle">Elapsed Time</th>'+
                                '<th style="vertical-align:middle">Transfer Rate</th>'+
                                '<th style="vertical-align:middle">Transferred</th>'+
                                '<th style="vertical-align:middle">Compression</th>'+
                                '<th style="vertical-align:middle">Progress</th>'+
                                '<th style="vertical-align:middle">Actions</th>'+
                            '</tr>'+
                        '</thead>'+'<tbody id="activeJobsListBody">';
            isAjaxDone = true;
            body = body + '</tbody> </table>';
                $('#active_jobs_area').html(body);
                $('#active_jobs_area').show();
                $('#img').hide();
            $(function () {
                    $("#activeJobsList").DataTable({
                        "columnDefs": [
                            {"orderable": false, "targets": [8]}
                        ]
                    });
                });
        }
    });
}

function doDeleteActiveJob(job_info){
            var job = job_info.split("#");
            var id = job[0];
            var name =  job[1];
            var url_action = url_cancel_job + id;
            $('#' + id).attr('action' , url_action);
            delete_message = confirm_delete_msg.replace('$', name);
            var confirm_deleting = confirm(delete_message);
            if(!confirm_deleting){
                return false;
            }
}