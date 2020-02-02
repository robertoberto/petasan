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
function user_edit_cancel(path) {
    $("#cancelBtn").click(function () {

        window.location = path;
    });
}

function isEmail(EmailValue) {
    var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    return regex.test(EmailValue);
}

$("#edit_user_form").submit(function (event) {
        // validate
        //  name
        var EmailValue = $('#email').val();
        var Email = $('#email');
        var name = $("#name");
        var nameValue = $("#name").val();
        // check not empty
        if (!nameValue) {
            $("#lblName").text(messages.label_name);
            name.closest('.form-group').addClass('has-error');
            name.focus();
            event.preventDefault();
        }
        else {
            name.closest('.form-group').removeClass('has-error');
            $("#lblName").html("Name:" + "<font color='red'>*</font>");
        }
        // validate
        //  user name

        var userName = $("#userName");
        var userNameValue = $("#userName").val();
        // check not empty
        if (!userNameValue) {
            $("#lblUserName").text(messages.label_user_name);
            userName.closest('.form-group').addClass('has-error');
            userName.focus();
            event.preventDefault();
        }
        else {
            userName.closest('.form-group').removeClass('has-error');
            $("#lblUserName").html("User Name:" + "<font color='red'>*</font>");
        }
        // validate
        //  user password

        var userPassword = $("#userPassword");
        var userPasswordValue = $("#userPassword").val();
        // check not empty
        if (!userPasswordValue) {
            $("#lblPassword").text(messages.label_user_password);
            userPassword.closest('.form-group').addClass('has-error');
            userPassword.focus();
            event.preventDefault();
        }
        else {
            userPassword.closest('.form-group').removeClass('has-error');
            $("#lblPassword").html("User Password:" + "<font color='red'>*</font>");
        }
        // validate
        //  confirm password

        var confirmPassword = $("#confirmPassword");
        var confirmPasswordValue = $("#confirmPassword").val();
        // check Matching
        if (userPasswordValue != confirmPasswordValue) {
            $("#lblConfirmPassword").text(messages.confirm_password);
            confirmPassword.closest('.form-group').addClass('has-error');
            confirmPassword.focus();
            event.preventDefault();

        }
        else {
            confirmPassword.closest('.form-group').removeClass('has-error');
            $("#lblConfirmPassword").html("Confirm Password:" + "<font color='red'>*</font>");
        }

        if ($('#notify_mail').is(':checked')) {
            if ($("#email").val() == "") {
                $("#lblEmail").text(messages.confirm_email);
                $("#email").closest('.form-group').addClass('has-error');
                $("#email").focus();
                event.preventDefault();
            }
            else {
                if (EmailValue.length > 0 && !isEmail(EmailValue)) {
                    $("#lblEmail").text(messages.valid_email);
                    Email.closest('.form-group').addClass('has-error');
                    Email.focus();
                    event.preventDefault();
                }
                else {
                    Email.closest('.form-group').removeClass('has-error');
                    $("#lblEmail").text("Email:");
                }
            }
        }
        else {
            if ($("#email").val() == "") {
                Email.closest('.form-group').removeClass('has-error');
                $("#lblEmail").text("Email:");
            }
            else {
                if (EmailValue.length > 0 && !isEmail(EmailValue)) {
                    $("#lblEmail").text(messages.valid_email);
                    Email.closest('.form-group').addClass('has-error');
                    Email.focus();
                    event.preventDefault();
                }
                else {
                    Email.closest('.form-group').removeClass('has-error');
                    $("#lblEmail").text("Email:");
                }
            }

        }

    }
);
