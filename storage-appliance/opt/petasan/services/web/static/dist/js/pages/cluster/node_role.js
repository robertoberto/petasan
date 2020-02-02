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
 * Created by root on 7/14/16.
 */
onChangeShowDiskTable();
function change_node_action(url) {
    $('#validate').val('false');
    $('#option_form').attr("action", url);
    $("#option_form").submit();
}

function dataTable() {
    $("#diskList").DataTable({
        "paging": false,
        "searching": false,
        "info": true,
        "order": [],
        "columnDefs": [{
            "targets": 'no-sort',
            "orderable": false, "targets": [8]
        },
            {targets: [5, 6, 7], class: "wrap_model_vendor_serial"},
            {targets: [0, 1, 2, 3, 4], class: "wrap_diskName_type_size"}
        ]
    });
}


function onChangeUsageDisk(disk_name) {
    if ($('#disk_check_box' + disk_name).prop("checked") == true) {
        $('#osd' + disk_name).prop('disabled', false);
        $('#journal' + disk_name).prop('disabled', false);
        console.log('usage' + disk_name)
        $('#usage' + disk_name).prop('disabled', false);
        console.log("3")
    } else {
        $('#osd' + disk_name).prop("checked", false);
        $('#journal' + disk_name).prop("checked", false);
        $('#osd' + disk_name).prop('disabled', true);
        $('#journal' + disk_name).prop('disabled', true);
         $('#usage' + disk_name).val("0");
         $('#usage' + disk_name).prop('disabled', true);

    }
}


function onChangeShowDiskTable() {
    if ($('#option_storage').prop("checked") == true) {
        $('#table_disk_list').show();
    } else {
        $('.disk_select').prop("checked", false);
        $('.disk_usage').prop('disabled', true);
        $('.disk_usage').prop("checked", false);
        $('.disk_usage').val("0")
        $('#table_disk_list').hide();
    }
}

var disk_name = [];

var alertMessageValue = $('#alert_message').text()
$('#option_form').submit(function (event) {
    if ($('#option_storage').prop("checked") == true) {

        $('.disk_select').each(function (index, element) {
            check_disk_name = $(this).attr('name');

            if ($(this).prop("checked") == true) {
                if($('#usage_' + check_disk_name).val() == '0'){
                    disk_name.push(check_disk_name);

                }

            }


        });
        if (disk_name != "" && $('#validate').val() != "false") {
            $('#alert_message').text(alertMessageValue + " " + disk_name.join(','));
            $('#usage_alert').show();
            event.preventDefault();
        }

    }
    disk_name = [];
    check_disk_name = "";

});


dataTable();