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


$("#join_cluter_form").submit(function (event) {
        console.log($('#validate').val());
        if ($('#validate').val() != 'false') {
            // validate cluster ip
            var IP = $("#cluterIP");
            var ipValue = $("#cluterIP").val();
            // check not empty
            if (!ipValue) {
                $("#lblCluterIP").text(messages.label_management_node_ip);
                IP.closest('.form-group').addClass('has-error');
                IP.focus();
                event.preventDefault();
            }
            else if (!ValidateIPaddress($("#cluterIP").val())) {
                //lblCluterIP
                //alert("not valid");
                $("#lblCluterIP").text(messages.label_management_node_ip_not_valid);
                IP.closest('.form-group').addClass('has-error');
                IP.focus();
                event.preventDefault();

            }
            else {
                IP.closest('.form-group').removeClass('has-error');
                $("#lblCluterIP").html("Management node IP to join:" + "<font color='red'>*</font>");
            }

            // validate
            //  cluster password

            var clusterPassword = $("#clusterPassword");
            var clusterPasswordValue = $("#clusterPassword").val();
            // check not empty
            if (!clusterPasswordValue) {
                $("#lblPassword").text(messages.label_cluster_password);
                clusterPassword.closest('.form-group').addClass('has-error');
                clusterPassword.focus();
                event.preventDefault();
            }
            else {
                clusterPassword.closest('.form-group').removeClass('has-error');
                $("#lblPassword").html("Cluster Password:" + "<font color='red'>*</font>");
            }
            function ValidateIPaddress(ipaddress) {
                if (ipaddress.match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/)) {
                    return (true);
                }

                return (false);
            }

        }

    }
)
