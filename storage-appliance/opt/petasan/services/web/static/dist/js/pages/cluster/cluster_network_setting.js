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

//    $("#iscsi_1_eth_name").html($("#iscsi_1_eth_name option").sort(function (a, b) {
//    return a.text == b.text ? 0 : a.text < b.text ? -1 : 1
//}));
//
//    $("#iscsi_2_eth_name").html($("#iscsi_2_eth_name option").sort(function (a, b) {
//    return a.text == b.text ? 0 : a.text < b.text ? -1 : 1
//}));
//
//    $("#backend_1_eth_name").html($("#backend_1_eth_name option").sort(function (a, b) {
//    return a.text == b.text ? 0 : a.text < b.text ? -1 : 1
//}));
//
//    $("#backend_2_eth_name").html($("#backend_2_eth_name option").sort(function (a, b) {
//    return a.text == b.text ? 0 : a.text < b.text ? -1 : 1
//}));
//    var iscsi_1_eth_options = $("#iscsi_1_eth_name option");
//    iscsi_1_eth_options.sort(function (a, b) {
//        if (a.text > b.text) return 1;
//        if (a.text < b.text) return -1;
//        return 0
//    })
//    $("#iscsi_1_eth_name").empty();
//   // $('#iscsi_1_eth_name').append($("<option></option>").attr("value",0).text("-----"));
//    $("#iscsi_1_eth_name").append(iscsi_1_eth_options);
//   // $("#iscsi_1_eth_name").val('0');
//
//    var iscsi_2_eth_options = $("#iscsi_2_eth_name option");
//    iscsi_2_eth_options.sort(function (a, b) {
//        if (a.text > b.text) return 1;
//        if (a.text < b.text) return -1;
//        return 0
//    })
//    $("#iscsi_2_eth_name").empty();
//    //$('#iscsi_2_eth_name').append($("<option></option>").attr("value",0).text("-----"));
//    $("#iscsi_2_eth_name").append(iscsi_2_eth_options);
//    //$("#iscsi_2_eth_name").val('0');
//
//    var backend_1_eth_options = $("#backend_1_eth_name option");
//    backend_1_eth_options.sort(function (a, b) {
//        if (a.text > b.text) return 1;
//        if (a.text < b.text) return -1;
//        return 0
//    })
//    $("#backend_1_eth_name").empty();
//   // $('#backend_1_eth_name').append($("<option></option>").attr("value",0).text("-----"));
//    $("#backend_1_eth_name").append(backend_1_eth_options);
//    //$("#backend_1_eth_name").val('0');
//
//    var backend_2_eth_options = $("#backend_2_eth_name option");
//    backend_2_eth_options.sort(function (a, b) {
//        if (a.text > b.text) return 1;
//        if (a.text < b.text) return -1;
//        return 0
//    })
//    $("#backend_2_eth_name").empty();
//    //$('#backend_2_eth_name').append($("<option></option>").attr("value",0).text("---"));
//    $("#backend_2_eth_name").append(backend_2_eth_options);
//    //$("#backend_2_eth_name").val('0');
});


function toggleCheckbox(element, id) {
    if (element.checked) {
        $('#' + id).show();
    } else {
        $('#' + id).hide();
    }

}


$("#cluster_network_config").submit(function (event) {

    if ($('#validate').val() != 'false') {

        function ValidateIPaddress(ipaddress) {
            if (ipaddress.match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/)) {
                return (true);
            }

            return (false);
        }


        //validate vlan

        if ($('#vlan_tagging_backend1').prop('checked')) {
            var vlan_backend1_id = $('#vlan_id_backend1').val();
            if (vlan_backend1_id) {
                if (vlan_backend1_id < 1 || vlan_backend1_id > 4094) {

                    $("#vlan_id_backend1_label").text(messages.save_cluster_network_setting_lbl_validate_vlan_id);
                    $('#vlan_id_backend1').closest('.form-group').addClass('has-error');
                    $('#vlan_id_backend1').focus();
                    event.preventDefault();
                } else {
                    $('#vlan_id_backend1').closest('.form-group').removeClass('has-error');
                    $("#vlan_id_backend1_label").html("VLAN Id:" + "<font color='red'>*</font>");
                }

            } else {
                $("#vlan_id_backend1_label").text(messages.save_cluster_network_setting_lbl_backend1_vlan_id_empty);
                $('#vlan_id_backend1').closest('.form-group').addClass('has-error');
                $('#vlan_id_backend1').focus();
                event.preventDefault();
            }
        }


        if ($('#vlan_tagging_backend2').prop('checked')) {
            var vlan_backend2_id = $('#vlan_id_backend2').val();
            if (vlan_backend2_id) {
                if (vlan_backend2_id < 1 || vlan_backend2_id > 4094) {
                    $("#vlan_id_backend2_label").text(messages.save_cluster_network_setting_lbl_validate_vlan_id);
                    $('#vlan_id_backend2').closest('.form-group').addClass('has-error');
                    $('#vlan_id_backend2').focus();
                    event.preventDefault();
                } else {
                    $('#vlan_id_backend2').closest('.form-group').removeClass('has-error');
                    $("#vlan_id_backend2_label").html("VLAN Id:" + "<font color='red'>*</font>");
                }

            } else {
                $("#vlan_id_backend2_label").text(messages.save_cluster_network_setting_lbl_backend2_vlan_id_empty);
                $('#vlan_id_backend2').closest('.form-group').addClass('has-error');
                $('#vlan_id_backend2').focus();
                event.preventDefault();
            }
        }

        // validate for ISCSI Path 1
        var iscsi_1 = $("#iscsi_1_eth_name");
        var iscsi_1_value = $("#iscsi_1_eth_name").val();
        // check not empty
        if (iscsi_1_value == 0) {
            $("#lblIscsi1").text(messages.save_cluster_network_setting_lbl_iscsi1_empty);
            iscsi_1.closest('.form-group').addClass('has-error');
            iscsi_1.focus();
            event.preventDefault();
        } else {
            iscsi_1.closest('.form-group').removeClass('has-error');
            $("#lblIscsi1").html("iSCSI 1 Interface:" + "<font color='red'>*</font>");
        }

        // validate for ISCSI Path 2
        var iscsi_2 = $("#iscsi_2_eth_name");
        var iscsi_2_value = $("#iscsi_2_eth_name").val();
        // check not empty
        if (iscsi_2_value == 0) {
            $("#lblIscsi2").text(messages.save_cluster_network_setting_lbl_iscsi2_empty);
            iscsi_2.closest('.form-group').addClass('has-error');
            iscsi_2.focus();
            event.preventDefault();
        } else {
            iscsi_2.closest('.form-group').removeClass('has-error');
            $("#lblIscsi2").html("iSCSI 2 Interface:" + "<font color='red'>*</font>");
        }

        // validate for Backend 1
        var backend_1 = $("#backend_1_eth_name");
        var backend_1_value = $("#backend_1_eth_name").val();
        // check not empty
        if (backend_1_value == 0) {
            $("#lblBackend1").text(messages.save_cluster_network_setting_lbl_backend1_empty);
            backend_1.closest('.form-group').addClass('has-error');
            backend_1.focus();
            event.preventDefault();
        } else {
            backend_1.closest('.form-group').removeClass('has-error');
            $("#lblBackend1").html("Backend 1 Interface:" + "<font color='red'>*</font>");
        }

        // validate for Backend 2
        var backend_2 = $("#backend_2_eth_name");
        var backend_2_value = $("#backend_2_eth_name").val();
        // check not empty
        if (backend_2_value == 0) {
            $("#lblBackend2").text(messages.save_cluster_network_setting_lbl_backend2_empty);
            backend_2.closest('.form-group').addClass('has-error');
            backend_2.focus();
            event.preventDefault();
        } else {
            backend_2.closest('.form-group').removeClass('has-error');
            $("#lblBackend2").html("Backend 2 Interface:" + "<font color='red'>*</font>");
        }

        //validate for Base IP 1
        var base_ip_1 = $("#backend_1_base_ip");
        var base_ip_1_value = base_ip_1.val();
        //check if empty
        if (!base_ip_1_value) {
            $("#lblBaseIP1").text(messages.save_cluster_network_setting_lbl_ip_empty);
            base_ip_1.closest('.form-group').addClass('has-error');
            base_ip_1.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!ValidateIPaddress(base_ip_1_value)) {
            $("#lblBaseIP1").text(messages.save_cluster_network_setting_lbl_ip_invalid);
            base_ip_1.closest('.form-group').addClass('has-error');
            base_ip_1.focus();
            event.preventDefault();
        }
        else {
            base_ip_1.closest('.form-group').removeClass('has-error');
            $("#lblBaseIP1").html("Subnet Base IP:" + "<font color='red'>*</font>");
        }

        //validate for Base IP 2
        var base_ip_2 = $("#backend_2_base_ip");
        var base_ip_2_value = base_ip_2.val();
        //check if empty
        if (!base_ip_2_value) {
            $("#lblBaseIP2").text(messages.save_cluster_network_setting_lbl_ip_empty);
            base_ip_2.closest('.form-group').addClass('has-error');
            base_ip_2.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!ValidateIPaddress(base_ip_2_value)) {
            $("#lblBaseIP2").text(messages.save_cluster_network_setting_lbl_ip_invalid);
            base_ip_2.closest('.form-group').addClass('has-error');
            base_ip_2.focus();
            event.preventDefault();
        }
        else {
            base_ip_2.closest('.form-group').removeClass('has-error');
            $("#lblBaseIP2").html("Subnet Base IP:" + "<font color='red'>*</font>");
        }

        //validate for Subnet Mask 1
        var subnet_1 = $("#backend_1_mask");
        var subnet_1_value = subnet_1.val();
        //check if empty
        if (!subnet_1_value) {
            $("#lblSubnet1").text(messages.save_cluster_network_setting_lbl_subnet_empty);
            subnet_1.closest('.form-group').addClass('has-error');
            subnet_1.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!subnet_1_value.match(/^((128|192|224|240|248|252|254)\.0\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0)|255\.(0|128|192|224|240|248|252|254)))))$/)) {
            $("#lblSubnet1").text(messages.save_cluster_network_setting_lbl_subnet_invalid);
            subnet_1.closest('.form-group').addClass('has-error');
            subnet_1.focus();
            event.preventDefault();
        }
        else {
            subnet_1.closest('.form-group').removeClass('has-error');
            $("#lblSubnet1").html("Subnet Mask:" + "<font color='red'>*</font>");
        }

        //validate for Subnet Mask 2
        var subnet_2 = $("#backend_2_mask");
        var subnet_2_value = subnet_2.val();
        //check if empty
        if (!subnet_2_value) {
            $("#lblSubnet2").text(messages.save_cluster_network_setting_lbl_subnet_empty);
            subnet_2.closest('.form-group').addClass('has-error');
            subnet_2.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!subnet_2_value.match(/^((128|192|224|240|248|252|254)\.0\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0)|255\.(0|128|192|224|240|248|252|254)))))$/)) {
            $("#lblSubnet2").text(messages.save_cluster_network_setting_lbl_subnet_invalid);
            subnet_2.closest('.form-group').addClass('has-error');
            subnet_2.focus();
            event.preventDefault();
        }
        else {
            subnet_2.closest('.form-group').removeClass('has-error');
            $("#lblSubnet2").html("Subnet Mask:" + "<font color='red'>*</font>");
        }
    }
});