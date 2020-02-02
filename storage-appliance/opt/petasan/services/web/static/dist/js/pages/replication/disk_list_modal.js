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

var source_disk_name = "";
var dest_disk_id = "";
var src_disk_size = 0;
var dest_disk_size = 0;
var disk_list = [];
var timeStamp = new Date().getTime();

$(document).ready(function () {

    $.ajaxSetup({cache: false});
     $("#choose").click(function(){
            var radioValue = $("input[name='selected_disk']:checked").val();
            if(radioValue){
                $('#source_disk').attr('value', radioValue);

            }
        });

     $("#choose_dest").click(function(){
            var radioValue = $("input[name='selected_dest_disk']:checked").val();
            if(radioValue){
                $('#destination_disk').attr('value', radioValue);

            }
        });
});


//function load_disks_2(get_disk_list_info_url)
//{
//    alert(get_disk_list_info_url);
//    var url = get_disk_list_info_url;
//    setInterval("load_disks (url)", 5000);  // call every 10 seconds
//}

////////////////////////////////////////////////////////
function load_disks_2(get_disk_list_info_url) {
    $('#disksArea').hide();
    $('#img').show();
    $('#disksList').empty();

    $.ajax({
        cache: false,
        url: get_disk_list_info_url,
        type: "get",
        success: function (data) {


            var disks_list = JSON.parse(data);
            disk_list = disks_list;
            // clear old data //
            $('#disksListBody').html("");
            $('#disksList').append('<thead><tr><th></th><th>Disk Id</th><th>Size</th><th>Name</th><th>Created</th><th>Pool</th><th>IQN</th></tr></thead><tbody id="disksListBody">');
            source_disk_name = "";

            var body = "";
            for (var k in disks_list) {
                source_disk_name = source_disk_name + disks_list[k]['id'] + "#";

                body = body + '<tr class="disk">';

                body = body + '<td><input type="radio" name="selected_disk" id="' + disks_list[k]['id'] + '" value="' + disks_list[k]['id'] + '"></td>';

                body = body + '<td class="id">' + disks_list[k]['id'] + '</td>';

                if (disks_list[k]['size'] >= 1024)
                    body = body + '<td>' + (disks_list[k]['size'] / 1024) + ' TB</td>'
                else
                    body = body + '<td>' + disks_list[k]['size'] + 'GB</td>'

                body = body + '<td class="name">' + disks_list[k]['disk_name'] + '</td>';

                body = body + '<td>' + disks_list[k]['create_date'] + '</td>';

                var pool;
                pool = disks_list[k]['pool'];
                if (disks_list[k]['data_pool'].length > 0) {
                    pool = disks_list[k]['pool'] + '+' + disks_list[k]['data_pool']
                }

                body = body + '<td class="pool">' + pool + '</td>';

                body = body + '<td class="pool">' + disks_list[k]['iqn'] + '</td>';

                body = body + '</tr>';


            }
            body = body + '</tbody>';
            $('#disksList').append(body);

            //data-table //
            $("#disksList").DataTable({
                "order": [[1, "asc" ]],
                "columnDefs": [
                    {
                        "orderable": false, "targets": [0],
                        "targets": [0],
                        "sortable": true,
                        "searchable": true
                    }
                ],
                destroy: true
            });

            $('#img').hide();

            $('#disksArea').show();
            $('#disksList').show();
            $('#disksListBody').show();


        },
        error: function () {

        }

    });

}

function load_dest_disks(get_disk_list_info_url) {
    validDestCluster();
    $('#test_failed').hide();
    $('#dest_disksArea').hide();
    $('#dest_img').show();
    $('#dest_disksList').empty();

    var cluster_name = "";
    var cluster_ip = "";
    var cluster_password = "";

    if ($("#dest_cluster_name").val().length > 0) {
        cluster_name = $("#dest_cluster_name").val();
    }

    $.ajax({
        cache: false,
        url: get_disk_list_info_url + '?dt=' + new Date().getTime(),
        type: "get",
        data: {
            cluster_name: cluster_name,
        },
        success: function (data) {

            var disks_list = JSON.parse(data);
            if ('err' in disks_list)
            {
                $('#dest_img').hide();
                $('#failed_sent').text(disks_list['err']);
                $('#test_failed').show();
            }
            else{

            // clear old data //
            $('#dest_disksListBody').html("");
            $('#dest_disksList').append('<thead><tr><th></th><th>Disk Id</th><th>Size</th><th>Name</th><th>Created</th><th>Pool</th><th>IQN</th></tr></thead><tbody id="dest_disksListBody">');
            dest_disk_id = "";

            var body = "";

            for (var k in disks_list) {
                dest_disk_id = dest_disk_id + disks_list[k]['id'] + "#";

                body = body + '<tr>';

                body = body + '<td><input type="radio" name="selected_dest_disk" id="' + disks_list[k]['id'] + '" value="' + disks_list[k]['id'] + '"></td>';

                body = body + '<td>' + disks_list[k]['id'] + '</td>';

                if (disks_list[k]['size'] >= 1024)
                    body = body + '<td>' + (disks_list[k]['size'] / 1024) + ' TB</td>'
                else
                    body = body + '<td>' + disks_list[k]['size'] + 'GB</td>'

                body = body + '<td>' + disks_list[k]['disk_name'] + '</td>';

                body = body + '<td>' + disks_list[k]['create_date'] + '</td>';

                var pool;
                pool = disks_list[k]['pool'];
                if (disks_list[k]['data_pool'].length > 0) {
                    pool = disks_list[k]['pool'] + '+' + disks_list[k]['data_pool']
                }

                body = body + '<td class="pool">' + pool + '</td>';

                body = body + '<td>' + disks_list[k]['iqn'] + '</td>';

                body = body + '</tr>';
                //$('#disksListBody').append(body);


            }
            body = body + '</tbody>';
            $('#dest_disksList').append(body);


            // data-table //
            $("#dest_disksList").DataTable({
                "order": [[1, "asc" ]],
                "columnDefs": [
                    {
                        "orderable": false, "targets": [0],
                        "sortable": true,
                        "searchable": true
                    }
                ],
                destroy: true
            });

            $('#dest_img').hide();
            $('#dest_disksArea').show();
            $('#dest_disksList').show();
            $('#dest_disksListBody').show();
                }


        },
        error: function () {
        }

    });

}




