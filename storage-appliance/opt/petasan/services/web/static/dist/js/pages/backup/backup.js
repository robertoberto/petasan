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


var disk_names ="";


function chooseDisks()
{
    var value = "";


    // remove last #
    if(disk_names.length > 0)
    {
        disk_names = disk_names.substring(0, disk_names.length - 1);

        var list = disk_names.split("#");

        for (var x = 0; x < list.length; x++)
        {
            var disk_name = list[x];

            if (document.getElementById(disk_name).checked)
                value += document.getElementById(disk_name).value + ",";
        }

        value = value.substring(0, value.length - 1);

        $('#disks').attr('value', value);
    }

}


////////////////////////////////////////////////////////
function load_disks(get_rule_info_url) {

    //alert(get_rule_info_url);

    $('#disksArea').hide();
    $('#img').show();

    $.ajax({
        url: get_rule_info_url,
        type: "get",
        success: function (data) {

            var disks_list = JSON.parse(data);

            // clear old data //
            $('#disksListBody').html("");
            disk_names = "";

            var body = "";

            for (var k in disks_list)
             {
                 disk_names = disk_names + disks_list[k]['disk_name'] + "#";


                 body =  body + '<tr class="disk">' ;

                 body = body + '<td><input type="checkbox" name="' + disks_list[k]['disk_name'] +
                     '" id="' + disks_list[k]['disk_name'] + '" value="' + disks_list[k]['disk_name'] + '"></td>';

                 body = body + '<td class="id">' + disks_list[k]['id'] + '</td>';

                 if (disks_list[k]['size'] >= 1024)
                    body = body + '<td>' + (disks_list[k]['size'] / 1024) +' TB</td>'
                 else
                    body = body + '<td>' + disks_list[k]['size'] + 'GB</td>'

                 body = body + '<td class="name">' + disks_list[k]['disk_name'] +'</td>';

                 body = body + '<td>' + disks_list[k]['create_date'] + '</td>';

                 body = body + '<td class="pool">' + disks_list[k]['pool'] + '</td>';

                 body = body + '<td class="pool">' + disks_list[k]['iqn'] + '</td>';

                 body = body + '</tr>';

                //$('#disksListBody').append(body);

             }
             $('#disksListBody').html(body);



            // data-table //
            $("#disksList").DataTable({
                "columnDefs": [
                    {"orderable": false, "targets": [0], "order":[1,2,3,4,5,6], "sortable": true, "searchable": true}
                ]
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
