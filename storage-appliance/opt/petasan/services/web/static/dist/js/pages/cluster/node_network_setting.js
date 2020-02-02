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
});

$("#node_network_config").submit(function (event) {
    if ($('#validate').val() != 'false') {

        function ValidateIPaddress(ipaddress) {
            if (ipaddress.match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/)) {
                return (true);
            }

            return (false);
        }

        //validate for Base IP 1
        var backend_ip_1 = $("#backend_ip_1");
        var backend_ip_1_value = backend_ip_1.val();
        //check if empty
        if (!backend_ip_1_value) {
            $("#lblBackend1").text(messages.save_node_network_setting_lbl_ip1_empty);
            backend_ip_1.closest('.form-group').addClass('has-error');
            backend_ip_1.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!ValidateIPaddress(backend_ip_1_value)) {
            $("#lblBackend1").text(messages.save_node_network_setting_lbl_ip1_invalid);
            backend_ip_1.closest('.form-group').addClass('has-error');
            backend_ip_1.focus();
            event.preventDefault();
        }
        else {
            backend_ip_1.closest('.form-group').removeClass('has-error');
            $("#lblBackend1").html("Node Backend 1 IP:" + "<font color='red'>*</font>");
        }

        //validate for Base IP 2
        var backend_ip_2 = $("#backend_ip_2");
        var backend_ip_2_value = backend_ip_2.val();
        //check if empty
        if (!backend_ip_2_value) {
            $("#lblBackend2").text(messages.save_node_network_setting_lbl_ip2_empty);
            backend_ip_2.closest('.form-group').addClass('has-error');
            backend_ip_2.focus();
            event.preventDefault();
        }
        // check is valid
        else if (!ValidateIPaddress(backend_ip_2_value)) {
            $("#lblBackend2").text(messages.save_node_network_setting_lbl_ip2_invalid);
            backend_ip_2.closest('.form-group').addClass('has-error');
            backend_ip_2.focus();
            event.preventDefault();
        }
        else {
            backend_ip_2.closest('.form-group').removeClass('has-error');
            $("#lblBackend2").html("Node Backend 2 IP:" + "<font color='red'>*</font>");
        }
    }
});
