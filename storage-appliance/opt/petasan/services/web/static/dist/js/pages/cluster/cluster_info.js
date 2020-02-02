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

$("#cluster_info_form").submit(function (event) {
        if ($('#validate').val() != 'false') {
            // validate cluster name
            var name = $("#name");
            var nameValue = $("#name").val();
            // check not empty
            if (!nameValue) {
                $("#lblName").text(messages.label_cluster_name);
                name.closest('.form-group').addClass('has-error');
                name.focus();
                event.preventDefault();
            }
            // check has spaces
            else if (nameValue.indexOf(' ') > 0) {
                $("#lblName").text(messages.lbl_cluster_name_contain_spaces);
                name.closest('.form-group').addClass('has-error');
                name.focus();
                event.preventDefault();
            }
            else {
                name.closest('.form-group').removeClass('has-error');
                $("#lblName").html("Cluster Name:" + "<font color='red'>*</font>");
            }

            // validate cluster password
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
                $("#lblPassword").html("Password:" + "<font color='red'>*</font>");
            }
            // validate
            //  confirm password

            var confirmPassword = $("#confirmPassword");
            var confirmPasswordValue = $("#confirmPassword").val();
            // check Matching
            if (clusterPasswordValue != confirmPasswordValue) {
                $("#lblConfirmPassword").text(messages.label_cluster_confirm_password);
                confirmPassword.closest('.form-group').addClass('has-error');
                confirmPassword.focus();
                event.preventDefault();

            }
            else {
                confirmPassword.closest('.form-group').removeClass('has-error');
                $("#lblConfirmPassword").html("Confirm Password:" + "<font color='red'>*</font>");
            }

        }
    }
)
