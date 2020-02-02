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

$("#cancelBtn").click(function () {
    window.location = "/";
});

if ($('#disabled_mode').prop("checked") == true) {
    $('#compression_algorithm').hide();
} else {
    $('#compression_algorithm').show();
}

$("input").on("keydown", function (e) {

    return e.which !== 32;
});

function isEmail(EmailValue) {
    var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    return regex.test(EmailValue);
}


if ($('#authentication_value option:selected').val() == "4") {
    $("#userPassword").val("");
    $("#pass_hide").hide();
}


//onServerAuthentication function to hide the password if the server authentication value equal Anonymous

function onChangeServerAuthenticationValue() {
    if ($('#authentication_value option:selected').val() == "4") {
        $("#userPassword").val("");
        $("#pass_hide").hide();
    } else {
        $("#pass_hide").show();
    }
}

$('#email_sent_successfully').hide();
$('#email_sent_failed').hide();
$('#overlay').hide();


//Test Mail Configuration function to validate the mail inputs


function mail_settings_validation() {
    var status = 1
    var SMTPValue = $('#smtp_server').val();
    var PortNoValue = $('#port_no').val();
    var EmailValue = $('#email').val();
    var PasswdValue = $("#userPassword").val();
    var authentication_value = $('#authentication_value option:selected').val();
    var Email = $('#email');
    var PortNo = $('#port_no');
    var Smtp = $('#smtp_server');
    var Passwd = $("#userPassword");

    if (!SMTPValue) {
        $("#lblSMTPServer").text(messages.label_smtp_empty_smtp);
        Smtp.closest('.form-group').addClass('has-error');
        Smtp.focus();
        status = 0;
        //event.preventDefault();
    }
    else {
        Smtp.closest('.form-group').removeClass('has-error');
        $("#lblSMTPServer").text("SMTP:");
    }

    if (!PortNoValue) {
        $("#lblPortNum").text(messages.label_smtp_port_number);
        PortNo.closest('.form-group').addClass('has-error');
        PortNo.focus();
        status = 0;
        //event.preventDefault();
    } else if (isNaN(PortNoValue)) {
        $("#lblPortNum").text(messages.label_smtp_port_number_valid);
        PortNo.closest('.form-group').addClass('has-error');
        PortNo.focus();
        status = 0;
        //event.preventDefault();
    }
    else {
        PortNo.closest('.form-group').removeClass('has-error');
        $("#lblPortNum").text("Port Number:");
    }


    if (!EmailValue) {
        $("#lblEmail").text(messages.label_smtp_email);
        Email.closest('.form-group').addClass('has-error');
        Email.focus();
        status = 0;
        //event.preventDefault();
    } else {
        if (EmailValue.length > 0 && !isEmail(EmailValue)) {
            $("#lblEmail").text(messages.label_smtp_valid_email);
            Email.closest('.form-group').addClass('has-error');
            Email.focus();
            status = 0;
            //event.preventDefault();
        }
        else {
            Email.closest('.form-group').removeClass('has-error');
            $("#lblEmail").text("Sender Email:");
        }
    }


    if (authentication_value != "4") {
        if (!PasswdValue) {
            $("#lblPassword").text(messages.label_smtp_password);
            Passwd.closest('.form-group').addClass('has-error');
            Passwd.focus();
            status = 0;
            //event.preventDefault();
        }
        else {
            Passwd.closest('.form-group').removeClass('has-error');
            $("#lblPassword").text("Password:");
        }
    }


    return status;


}


//onClick testEmail button function

function test_email() {
    if (mail_settings_validation() == false) {
        return false
    }
    $('#email_sent_successfully').hide();
    $('#email_sent_failed').hide();


    var SMTP_value = $('#smtp_server').val();
    var port_no_value = $('#port_no').val();
    var password_value = $("#userPassword").val();
    var mail_value = $('#email').val();
    var authentication_value = $('#authentication_value option:selected').val();

    $('#overlay').show();
    $.ajax({
        type: "POST",
        url: test_email_url,
        data: {
            'email': mail_value,
            'password': password_value,
            'server': SMTP_value,
            'port': port_no_value,
            'security': authentication_value
        },
        success: function (data) {
            if (data.indexOf('Sign in') != -1) {
                window.location.href = loginUrl;
            }
            var status = JSON.parse(data)
            if (status.success == false) {
                if (status.err_msg == "") {
                    $('#overlay').hide();
                    $('#failed_sent').text(status.exception);
                    $('#email_sent_failed').show();


                } else {
                    $('#overlay').hide();
                    $('#failed_sent').text(status.err_msg);
                    $('#email_sent_failed').show();

                }

            } else {
                $('#overlay').hide();
                $('#email_sent_successfully').show();

            }
        },
        error: function (data) {
            $('#overlay').hide();
            $('#failed_sent').text(data);
            $('#email_sent_failed').show();
        }

    });
}


$("#cluster_setting").submit(function (event) {

        var SMTPValue = $('#smtp_server').val();

        if (SMTPValue != "") {
            if (mail_settings_validation() == false)
                event.preventDefault();
        }

    }
);