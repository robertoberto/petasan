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
 * Created by root on 5/17/16.
 */

$("#cancelBtn").click(function () {

    window.location.href = "/";
});

$(document).ready(function () {
    $('#newPassword').val('');
    $('#confirmNewPassword').val('');
});


$("#change_password_form").submit(function (event) {
        // validate
        //  New password

        var newPassword = $("#newPassword");
        var newPasswordValue = $("#newPassword").val();
        // check not empty
        if (!newPasswordValue) {
            $("#lblNewPassword").text(messages.label_new_password);
            newPassword.closest('.form-group').addClass('has-error');
            newPassword.focus();
            event.preventDefault();
        }
        else {
            newPassword.closest('.form-group').removeClass('has-error');
            $("#lblNewPassword").html("New Password:" + "<font color='red'>*</font>");
        }
        // validate
        //  confirm new password

        var confirmNewPassword = $("#confirmNewPassword");
        var confirmNewPasswordValue = $("#confirmNewPassword").val();
        // check Matching
        if (newPasswordValue != confirmNewPasswordValue) {
            $("#lblConfirmNewPassword").text(messages.label_confirm_new_password);
            confirmNewPassword.closest('.form-group').addClass('has-error');
            confirmNewPassword.focus();
            event.preventDefault();

            event.preventDefault();
        }
        else {
            confirmNewPassword.closest('.form-group').removeClass('has-error');
            $("#lblConfirmNewPassword").html("Confirm Password:" + "<font color='red'>*</font>");
        }

    }
);
