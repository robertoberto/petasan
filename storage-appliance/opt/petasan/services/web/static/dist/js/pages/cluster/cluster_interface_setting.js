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
    $('#jf_interfaces').hide();
    $('#new_bond').hide();
    $('#bond_primary').hide();
    if ($('#option_normal').is(':checked')) {
        $('#jf_interfaces').hide();
    }
    else if ($('#option_jf').is(':checked')) {
        $('#jf_interfaces').show();
    }
    if ($('#option_normal_type').is(':checked')) {
        $('#new_bond').hide();
    }
    else if ($('#option_bond_type').is(':checked')) {
        $('#new_bond').show();
    }
});
var bond_counter = 0;

$('input:radio[name="frame_size"]').change(
    function () {
        if ($('#option_normal').is(':checked')) {
            $('#jf_interfaces').hide();
            $("#jf_interface option:selected").removeAttr("selected");
            $('#jf_interfaces').val("0");

        } else {
            $('#jf_interfaces').show();
        }
    });

$('input:radio[name="interface_type"]').change(
    function () {
        if ($('#option_normal_type').is(':checked')) {
            $('#new_bond').hide();
            $("#bond_interfaces option:selected").removeAttr("selected");
            $('#bond_interfaces').val("0");
            $('#bond_mode').val("0");
            $('#bond_primary').hide();
            $('#bond_primary_int').val("0");
            $('#bond_name').val("");
            //bond_counter = 0;
        } else {
            $('#new_bond').show();
            $("#bond_interfaces").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
            $("#bond_mode").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_mode").html("Bond Mode:" + "<font color='red'>*</font>");
            $("#bond_mode").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_mode").html("Bond Mode:" + "<font color='red'>*</font>");
            $("#bond_name").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_name").html("Bond Name:" + "<font color='red'>*</font>");
            set_bond_name();
        }
    });

$("#bond_mode").change(function () {
    var bond_interfaces_lbl = $("#bond_interfaces");
    var bond_interfaces = $("#bond_interfaces").val();
    if (bond_interfaces == undefined || bond_interfaces == null) {
        $('#bond_primary').hide();
        $("#bond_mode").val("0");
        $("#lbl_bond_interfaces").text(messages.save_cluster_interface_setting_lbl_bond_interfaces_empty);
        bond_interfaces_lbl.closest('.form-group').addClass('has-error');
        bond_interfaces_lbl.focus();
    } else {
        bond_interfaces_lbl.closest('.form-group').removeClass('has-error');
        $("#lbl_bond_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
        if (($("#bond_mode").val() == "active-backup") || ($("#bond_mode").val() == "balance-alb") || ($("#bond_mode").val() == "balance-tlb")) {
            $("#bond_primary_int").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_primary").html("Primary NIC:" + "<font color='red'>*</font>");
            $('#bond_primary').show();
            append_selected_eths_for_bond_to_primary();
        } else {
            $('#bond_primary').hide();
            $('#bond_primary_int').val("0");
        }
    }
});

$("#bond_interfaces").change(function () {
    if ($('#bond_primary').is(":hidden")) {
        $("#bond_mode").val("0");
    } else {
        if (($("#bond_mode").val() == "active-backup") || ($("#bond_mode").val() == "balance-alb") || ($("#bond_mode").val() == "balance-tlb")) {
            append_selected_eths_for_bond_to_primary();
        } else {
            $('#bond_primary').hide();
            $('#bond_primary_int').val("0");
        }
    }
});

function append_selected_eths_for_bond_to_primary() {
    $('#bond_primary_int').find('option').remove().end().append('<option value="0">---</option>');
    var bond_interfaces_lbl = $("#bond_interfaces");
    var bond_interfaces = $("#bond_interfaces").val();
    if (bond_interfaces == undefined || bond_interfaces == null) {
        $('#bond_primary').hide();
        $("#bond_mode").val("0");
        $("#lbl_bond_interfaces").text(messages.save_cluster_interface_setting_lbl_bond_interfaces_empty);
        bond_interfaces_lbl.closest('.form-group').addClass('has-error');
        bond_interfaces_lbl.focus();
    } else {
        bond_interfaces_lbl.closest('.form-group').removeClass('has-error');
        $("#lbl_bond_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
        for (i = 0; i < bond_interfaces.length; i++) {
            $('#bond_primary_int').append($("<option></option>").attr("value", bond_interfaces[i]).text(bond_interfaces[i]));
        }
    }
}

function set_bond_name() {
    $("#bond_name").val("bond" + bond_counter);
    //bond_counter ++;
}

function check_bond_name(name) {
    if ($('#bond_list tr').length > 1) {
        var bond_names = [];
        $("#bond_list tr").each(function () {
            bond_names.push($(this).find("td:first").text());
        });
        if (jQuery.inArray(name, bond_names) != -1) {
            return true;
        } else {
            return false;
        }
    } else {
        return false;
    }
}

function check_frame_size(interface) {
    if ($("#jf_interfaces").is(":visible")) {
        var jumbo_frames_interfaces_lbl = $("#jf_interface");
        var jumbo_frames_interfaces = $("#jf_interface").val();
        if (jumbo_frames_interfaces == undefined || jumbo_frames_interfaces == null) {
            $("#lbl_jf_interfaces").text(messages.save_cluster_interface_setting_lbl_jf_interfaces_empty);
            jumbo_frames_interfaces_lbl.closest('.form-group').addClass('has-error');
            jumbo_frames_interfaces_lbl.focus();
        } else {
            jumbo_frames_interfaces_lbl.closest('.form-group').removeClass('has-error');
            $("#lbl_jf_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
            var interfaces = []
            for (var i = 0; i < interface.length; i++) {
                var interface_name = interface[i]
                if (jQuery.inArray(interface[i], jumbo_frames_interfaces) != -1) {
                    interfaces.push({"interface_name": interface_name, "type": "jf"});
                } else {
                    interfaces.push({"interface_name": interface_name, "type": "normal"});
                }
            }
            return interfaces;
        }
    } else {
        return "-1";
    }
}

function check_array_all_values_equal(check_interfaces) {
    for (var i = 0; i < check_interfaces.length; i++) {
        if (check_interfaces[i]["type"] != check_interfaces[0]["type"]) {
            return false;
           // break;
        }
    }
    return true;
}

$("#add_bond").click(function () {
    //debugger;
    $("#lbl_added_bond").closest('.form-group').removeClass('has-error');
    $("#lbl_added_bond").html("Added Bonds:");
    var bond_interfaces_lbl = $("#bond_interfaces");
    var bond_interfaces = $("#bond_interfaces").val();
    var bond_mode_lbl = $("#bond_mode");
    var bond_mode = $("#bond_mode").val();
    var bond_name_lbl = $("#bond_name");
    var bond_name = $("#bond_name").val();
    var bond_primary = "";
    var primary_visible = false;
    if (bond_interfaces == undefined || bond_interfaces == null || bond_interfaces.length < 2) {
        $("#lbl_bond_interfaces").text(messages.save_cluster_interface_setting_lbl_bond_interfaces_empty);
        bond_interfaces_lbl.closest('.form-group').addClass('has-error');
        bond_interfaces_lbl.focus();
        return;
    }
    bond_interfaces_lbl.closest('.form-group').removeClass('has-error');
    $("#lbl_bond_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
    if (bond_mode == 0) {
        $("#lbl_bond_mode").text(messages.save_cluster_interface_setting_lbl_bond_mode_empty);
        bond_mode_lbl.closest('.form-group').addClass('has-error');
        bond_mode_lbl.focus();
        return;
    }
    bond_mode_lbl.closest('.form-group').removeClass('has-error');
    $("#lbl_bond_mode").html("Bond Mode:" + "<font color='red'>*</font>");
    if (bond_name == "") {
        $("#lbl_bond_name").text(messages.save_cluster_interface_setting_lbl_bond_name_empty);
        bond_name_lbl.closest('.form-group').addClass('has-error');
        bond_name_lbl.focus();
        return;
    }
    if (check_bond_name(bond_name)) {
        $("#lbl_bond_name").text(messages.save_cluster_interface_setting_lbl_bond_name_used);
        bond_name_lbl.closest('.form-group').addClass('has-error');
        bond_name_lbl.focus();
        return;
    }

    bond_name_lbl.closest('.form-group').removeClass('has-error');
    $("#lbl_bond_name").html("Bond Name:" + "<font color='red'>*</font>");
    bond_primary = $("#bond_primary_int").val();
    if (($("#bond_primary").is(":visible")) && bond_primary == 0) {
        $("#lbl_bond_primary").text(messages.save_cluster_interface_setting_lbl_bond_primary_empty);
        $("#bond_primary_int").closest('.form-group').addClass('has-error');
        $("#bond_primary_int").focus();
        primary_visible = true;
        return;
    } else {
        if (primary_visible) {
            $("#bond_primary_int").closest('.form-group').removeClass('has-error');
            $("#lbl_bond_primary").html("Primary NIC:" + "<font color='red'>*</font>");
        }
        if (bond_primary == 0) {
            bond_primary = ""
        }
        var check_interfaces = check_frame_size(bond_interfaces);
        var interfaces_frame_size = "Normal";
        if (check_interfaces != "-1") {
            if (check_array_all_values_equal(check_interfaces)) {

                if (check_interfaces[0]["type"] == "jf") {
                    interfaces_frame_size = "Jumbo";
                }
                $('#bond_list tr:last').after('<tr>' +
                    '<td>' + bond_name + '</td>' +
                    '<td>' + bond_mode + '</td>' +
                    '<td>' + bond_interfaces + '</td>' +
                    '<td>' + bond_primary + '</td>' +
                    '<td>' + interfaces_frame_size + '</td>' +
                    '<td>' + "<div title='Remove' class='btn-group'>" +
                    "<button id='delete_btn' onclick='remove_bond($(this))' class='btn btn-default'>" +
                    "<i class='fa fa-remove'></i> </button></div> " + '</td>' +
                    '</tr>'
                );
                for (var i = 0; i < bond_interfaces.length; i++) {
                    $('#bond_interfaces option').each(function () {
                        if ($(this).val() == bond_interfaces[i]) {
                            $(this).remove();
                        }
                    });
                }
                $('#bond_interfaces').val("0");
                $('#bond_mode').val("0");
                $('#bond_primary').hide();
                $('#bond_primary_int').val("0");
                bond_counter++;
                set_bond_name();
            } else {
                $("#lbl_bond_interfaces").text(messages.save_cluster_interface_setting_lbl_bond_interfaces_invalid);
                bond_interfaces_lbl.closest('.form-group').addClass('has-error');
                bond_interfaces_lbl.focus();
                return;
            }
        } else {
            $('#bond_list tr:last').after('<tr>' +
                '<td>' + bond_name + '</td>' +
                '<td>' + bond_mode + '</td>' +
                '<td>' + bond_interfaces + '</td>' +
                '<td>' + bond_primary + '</td>' +
                '<td>' + interfaces_frame_size + '</td>' +
                '<td>' + "<div title='Remove' class='btn-group'>" +
                "<button id='delete_btn' onclick='remove_bond($(this))' class='btn btn-default'>" +
                "<i class='fa fa-remove'></i> </button></div> " + '</td>' +
                '</tr>'
            );
            for (var i = 0; i < bond_interfaces.length; i++) {
                $('#bond_interfaces option').each(function () {
                    if ($(this).val() == bond_interfaces[i]) {
                        $(this).remove();
                    }
                });
            }
            $('#bond_interfaces').val("0");
            $('#bond_mode').val("0");
            $('#bond_primary').hide();
            $('#bond_primary_int').val("0");
            bond_counter++;
            set_bond_name();
        }
    }
});

function remove_bond(row) {
    var bond_deleted_other_interfaces = row.closest('tr').find('td').eq(2).html();
    row.closest('tr').remove();
    var interfaces = bond_deleted_other_interfaces.split(',');
    for (var i = 0; i < interfaces.length; i++) {
        $('#bond_interfaces').append($("<option></option>").attr("value", interfaces[i]).text(interfaces[i]));
    }

    var bond_interfaces_options = $("#bond_interfaces option");
    bond_interfaces_options.sort(function (a, b) {
        if (a.text > b.text) return 1;
        if (a.text < b.text) return -1;
        return 0
    })
    $("#bond_interfaces").empty().append(bond_interfaces_options);
}

$("#cluster_interface_setting").submit(function (event) {
    if ($('#validate').val() != 'false') {
        //debugger;
        $("#lbl_added_bond").closest('.form-group').removeClass('has-error');
        $("#lbl_added_bond").html("Added Bonds:");
        if ($("#jf_interfaces").is(":visible")) {
            var jumbo_frames_interfaces_lbl = $("#jf_interface");
            var jumbo_frames_interfaces = $("#jf_interface").val();
            if (jumbo_frames_interfaces == undefined || jumbo_frames_interfaces == null) {
                $("#lbl_jf_interfaces").text(messages.save_cluster_interface_setting_lbl_jf_interfaces_empty);
                jumbo_frames_interfaces_lbl.closest('.form-group').addClass('has-error');
                jumbo_frames_interfaces_lbl.focus();
                event.preventDefault();
            }
            else {
                jumbo_frames_interfaces_lbl.closest('.form-group').removeClass('has-error');
                $("#lbl_jf_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
            }
        }
        if (($("#new_bond").is(":visible"))) {
            if ($('#bond_list tr').length == 1) {
                $("#lbl_bond_interfaces").text(messages.save_cluster_interface_setting_lbl_bond_empty);
                $("#bond_interfaces").closest('.form-group').addClass('has-error');
                $("#bond_interfaces").focus();
                event.preventDefault();
            } else {
                $("#bond_interfaces").closest('.form-group').removeClass('has-error');
                $("#lbl_bond_interfaces").html("NIC Interfaces:" + "<font color='red'>*</font>");
                var jumbo_frames_interfaces = $("#jf_interface").val();
                if (jumbo_frames_interfaces != undefined || jumbo_frames_interfaces != null) {
                    $('#bond_list tr').not(":first").each(function () {
                        var bond_interfaces = $(this).find('td').eq(2).html();
                        bonded = bond_interfaces.split(',');
                        var bonded_frame_size = []
                        for (var i = 0; i < bonded.length; i++) {
                            if (jQuery.inArray(bonded[i], jumbo_frames_interfaces) != -1) {
                                bonded_frame_size.push({"type": "jf"});
                            } else {
                                bonded_frame_size.push({"type": "normal"});
                            }
                        }
                        if (!check_array_all_values_equal(bonded_frame_size)) {
                            //debugger;

                            $("#lbl_added_bond").text(messages.save_cluster_interface_setting_lbl_added_bonds_invalid);
                            $("#lbl_added_bond").closest('.form-group').addClass('has-error');
                            $("#lbl_added_bond").focus();
                            event.preventDefault();
                        }
                    });
                }
                var table_data = new Array();

                $('#bond_list tr:not(:has(th))').each(function (row, tr) {
                    var frame_size_flag = false;
                    if ($(tr).find('td:eq(4)').text() == "Jumbo") {
                        frame_size_flag = true;
                    }
                    if ($(tr).find('td:eq(3)').text() == "0") {
                        primary = "";
                    } else {
                        primary = $(tr).find('td:eq(3)').text();
                    }
                    table_data[row] = {
                        "name": $(tr).find('td:eq(0)').text()
                        , "mode": $(tr).find('td:eq(1)').text()
                        , "primary_interface": primary
                        , "interfaces": $(tr).find('td:eq(2)').text()
                        , "is_jumbo_frames": frame_size_flag
                    }
                });

                    $("#bonded_NIC").val(JSON.stringify(table_data));
                    console.log(table_data);
                //$('<input type="hidden" name="data" id="data" />').attr('value', JSON.stringify(table_data)).appendTo(this);
            }
        }
    }
});


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function load_interfaces_info() {
    /* Delete all rows in "interfacesTableBody" */
    $("#interfacesTableBody tr").remove();

    /* Getting the Json of "interfaces_info" dictionary --> "interfaces_json" */
    var interfaces = $('#network_interfaces').val();

    /* Convert json into object */
    var interfacesObj = JSON.parse(interfaces);

    /* Getting the string of "interfaces_info" dictionary keys --> interfaces names only */
    var keys_ls = $('#keys_ls').val();           // String --> 'eth3-eth2-eth1-eth0' //
    var keys_array = keys_ls.split("-");         // Array --> ["eth3","eth2","eth1","eth0"] //

    keys_array.sort();                           // Sorts the elements of keys_array //

    var i;
    for (i = 0; i < keys_array.length; i++) {
        var interface_name = keys_array[i];
        $('#interfacesTableBody').append('<tr><td>' + interfacesObj[interface_name]["device"] + '</td><td>' + interfacesObj[interface_name]["mac"] + '</td><td>' + interfacesObj[interface_name]["pci"] + '</td><td>' + interfacesObj[interface_name]["model"] + '</td></tr>');
    }

    $('#img').hide();
    $('#interfacesInfoArea').show();

}

function hide_used_NIC(bond_interfaces) {
    for (var i = 0; i < bond_interfaces.length; i++) {
        $('#bond_interfaces option').each(function () {
            if ($(this).val() == bond_interfaces[i]) {
                $(this).remove();
            }
        });
    }
}


