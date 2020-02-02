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


function set_cancel_edit(path) {

    $("#cancelBtn").click(function () {
        window.location = path;
    });
}

function set_slider_edit(size_list) {
    $(document).ready(function () {
        $(function () {

            $("[data-mask]").inputmask();

            var loaded_value = $("#diskSizeExactValue").val();

            //ion range slider
            var my_values_num_str = size_list;
            var my_values_num = my_values_num_str.slice(1, -1).split(',');


            $("#diskSize").ionRangeSlider({
                type: "single",
                values: my_values_num,
                grid: true,

                prettify: function (n) {

                    if (n >= 1024) {
                        return Math.floor(n / 1024) + " TB";
                    } else {
                        return n + " GB"
                    }
                },
                onChange: function (obj) {
                    value = obj["from_value"];
                    setText(value);
                }
            });
            function setText(num) {

                $("#diskSizeVal").val(num);
                if (num >= 1024) {
                    $("#diskSizeVal").val((num / 1024));
                    $("#lblDiskValUnit").text(" TB");

                } else {
                    $("#diskSizeVal").val(num);
                    $("#lblDiskValUnit").text(" GB");
                }

            }


            $("#diskSizeVal").keypress(function () {
                $("#lblDiskValUnit").text(" GB");
                var slider = $("#diskSize").data("ionRangeSlider");
                var value = $("#diskSizeVal").val();
                if (value.match(/^\d+$/)) {

                    if (value > my_values_num[my_values_num.length - 1]) {
                        value = my_values_num[my_values_num.length - 1];


                    } else {
                        for (var i = 0; i < my_values_num.length - 1; i++) {

                            if (value >= my_values_num[i] && value < my_values_num[i + 1]) {
                                value = i;

                                break;
                            }
                        }
                    }
                    slider.update({
                        from: value
                    });
                } else {

                    slider.update({
                        from: value
                    });
                }

            });

            $("#diskSizeVal").on('keyup', function (e) {

                var slider = $("#diskSize").data("ionRangeSlider");
                var value = $("#diskSizeVal").val();
                if (value.match(/^\d+$/)) {

                    if (value > my_values_num[my_values_num.length - 1]) {

                        value = my_values_num[my_values_num.length - 1];

                        setText(value);

                    } else {
                        for (var i = 0; i < my_values_num.length - 1; i++) {

                            if (value >= my_values_num[i] && value < my_values_num[i + 1]) {
                                value = i;
                                setText($("#diskSizeVal").val());
                                break;
                            }
                        }
                    }
                    slider.update({
                        from: value
                    });
                } else {
                    setText(1);
                    slider.update({
                        from: value
                    });
                }

            });

            setSliderValue();
            function setSliderValue() {

                var slider = $("#diskSize").data("ionRangeSlider");

//                var value = "{{disk.diskSize}}";
                var value = loaded_value;

                for (var i = 0; i < my_values_num.length - 1; i++) {

                    if (value >= my_values_num[i] && value < my_values_num[i + 1]) {
                        setText(value);
                        value = i;

                        break;
                    }
                }

                slider.update({
                    from: value
                });

            }
        });
    });
}

$(document).ready(function () {

    if ($('#orpAuthNo').is(':checked')) {
        $('#divUserName').hide();
        $('#divPassword').hide();
        $('#divConfirmPassword').hide();
    } else {
        $('#divUserName').show();
        $('#divPassword').show();
        $('#divConfirmPassword').show();
    }

    if ($('#orpAclAll').is(':checked')) {
        $('#IqnVal').hide();
    } else {
        $('#IqnVal').show();
    }


$('input:radio[name="orpACL"]').change(
    function () {
        if ($('#orpAclAll').is(':checked')) {
            $("#lblIqnVal").html("IQN(s)");
            $('#IqnVal').hide();

        } else {
            $("#lblIqnVal").html("IQN(s):" + "<font color='red'>*</font>");
            $('#IqnVal').show();
        }
    });


$('input:radio[name="orpAuth"]').change(
    function () {
        if ($('#orpAuthNo').is(':checked')) {
            $('#divUserName').hide();
            $('#divPassword').hide();
            $('#divConfirmPassword').hide();


        } else {
            $('#UserNameVal').val('');
            $('#PasswordVal').val('');
            $('#ConfirmPasswordVal').val('');
            $('#divUserName').show();
            $('#divPassword').show();
            $('#divConfirmPassword').show();

        }

    });

    $('input:radio[name="orpACL"]').change(
    function () {
        if ($('#orpAclAll').is(':checked')) {
            $("#lblIqnVal").html("IQN(s)");
            $('#IqnVal').hide();

        } else {
            $("#lblIqnVal").html("IQN(s):" + "<font color='red'>*</font>");
            $('#IqnVal').show();
        }
    });




    $("#diskName").focus();

    $("#edit_task_form").submit(function (event) {


        // validate disk name
        var diskName = $("#diskName");
        var diskNameValue = $("#diskName").val();
        // check not empty
        if (!diskNameValue) {
            $("#lblDiskName").text(messages.edit_disk_lbl_name_empty);
            diskName.closest('.form-group').addClass('has-error');
            diskName.focus();
            event.preventDefault();
        }
        // check length
        else if (!diskNameValue.length > 50) {
            $("#lblDiskName").text(messages.edit_disk_lbl_name_length);
            diskName.closest('.form-group').addClass('has-error');
            diskName.focus();
            event.preventDefault();
        }
        else {
            diskName.closest('.form-group').removeClass('has-error');
            $("#lblDiskName").html("Disk Name:" + "<font color='red'>*</font>");
        }

        // validate for size
        var lblDiskValUnit = $("#lblDiskValUnit").text();
        var diskSize = $("#diskSizeVal");
        var diskSizeValue = $("#diskSizeVal").val();
        var diskSizeExactValue = $("#diskSizeExactValue").val();

        // check not empty
        if (!diskSizeValue) {
            $("#lblDiskSize").text(messages.edit_disk_lbl_size_empty);
            diskSize.closest('.form-group').addClass('has-error');
            diskSize.focus();
            event.preventDefault();
        }
        // check is digit
        else if (!diskSizeValue.match(/^\d+$/)) {
            $("#lblDiskSize").text(messages.edit_disk_lbl_size_invalid);
            diskSize.closest('.form-group').addClass('has-error');
            diskSize.focus();
            event.preventDefault();
        }
        // check if TB
        else if (lblDiskValUnit.trim() == "TB") {
            if (parseInt(diskSizeValue * 1024) < parseInt(diskSizeExactValue)) {
                $("#lblDiskSize").text(messages.edit_disk_lbl_size_small);
                diskSize.closest('.form-group').addClass('has-error');
                diskSize.focus();
                event.preventDefault();
            } else {
                diskSize.closest('.form-group').removeClass('has-error');
                $("#lblDiskSize").text("Size :");
            }
        }
        // check if GB
        else if (lblDiskValUnit.trim() == "GB") {
            if (parseInt(diskSizeValue) < parseInt(diskSizeExactValue)) {
                $("#lblDiskSize").text(messages.edit_disk_lbl_size_small);
                diskSize.closest('.form-group').addClass('has-error');
                diskSize.focus();
                event.preventDefault();
            } else {
                diskSize.closest('.form-group').removeClass('has-error');
                $("#lblDiskSize").text("Size :");
            }
        }
        else {
            diskSize.closest('.form-group').removeClass('has-error');
            $("#lblDiskSize").text("Size :");
        }

        if (!$('#orpAclAll').is(':checked')) {
            // validare for client acl
            var iqn = $("#IqnVal");
            var iqnValue = $("#IqnVal").val();
            // check not empty
            if (!iqnValue) {
                $("#lblACL").text(messages.edit_disk_lbl_iqn_empty);
                $("#lblACL").closest('.form-group').addClass('has-error');
                iqn.closest('.form-group').addClass('has-error');
                iqn.focus();
                event.preventDefault();
            }
            else {
                $("#lblACL").closest('.form-group').removeClass('has-error');
                iqn.closest('.form-group').removeClass('has-error');
                $("#lblACL").html("Client ACL:"+ "<font color='red'>*</font>");
                $("#lblIqnVal").html("Iqn(s):" + "<font color='red'>*</font>");
            }

            // check length
            if (iqnValue.toLowerCase().indexOf(",") >= 0) {
                var values = iqnValue.split(',');
                for (i = 0; i < values.length; i++) {
                    if (!values[i].match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {
                        $("#lblACL").text(messages.edit_disk_lbl_iqn_invalid);
                        $("#lblACL").closest('.form-group').addClass('has-error');
                        iqn.closest('.form-group').addClass('has-error');
                        iqn.focus();
                        event.preventDefault();
                    } else {
                        $("#lblACL").closest('.form-group').removeClass('has-error');
                        iqn.closest('.form-group').removeClass('has-error');
                        $("#lblACL").html("Client ACL:"+ "<font color='red'>*</font>");
                        $("#lblIqnVal").html("Iqn(s):" + "<font color='red'>*</font>");
                    }
                }
            } else {
                if (!iqnValue.match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {
                    $("#lblACL").text(messages.edit_disk_lbl_iqn_invalid);
                    $("#lblACL").closest('.form-group').addClass('has-error');
                    iqn.closest('.form-group').addClass('has-error');
                    iqn.focus();
                    event.preventDefault();
                } else {
                    $("#lblACL").closest('.form-group').removeClass('has-error');
                    iqn.closest('.form-group').removeClass('has-error');
                    $("#lblACL").html("Client ACL:"+ "<font color='red'>*</font>");
                    $("#lblIqnVal").html("Iqn(s):" + "<font color='red'>*</font>");
                }
            }
        }

        // validare for user name and password if matched
        if ($('#orpAuthYes').is(':checked')) {

            // validate user name
            var userName = $("#UserNameVal");
            var userNameValue = $("#UserNameVal").val();
            // check not empty
            if (!userNameValue) {
                $("#lblUserName").text(messages.edit_disk_lbl_username_empty);
                userName.closest('.form-group').addClass('has-error');
                userName.focus();
                event.preventDefault();
            }
            // check length
            else if (!userNameValue.length > 50) {
                $("#lblUserName").text(messages.edit_disk_lbl_username_length);
                userName.closest('.form-group').addClass('has-error');
                userName.focus();
                event.preventDefault();
            }
            else {
                userName.closest('.form-group').removeClass('has-error');
                $("#lblUserName").html("User name:" + "<font color='red'>*</font>");
            }

            // validate passowrd

            var password = $("#PasswordVal");
            var passwordValue = $("#PasswordVal").val();
            // check not empty
            if (!passwordValue) {
                $("#lblPass").text(messages.edit_disk_lbl_password_empty);
                password.closest('.form-group').addClass('has-error');
                password.focus();
                event.preventDefault();
            }
            // check length
            else if (passwordValue.length > 16 || passwordValue.length < 12) {
                $("#lblPass").text(messages.edit_disk_lbl_password_length);
                password.closest('.form-group').addClass('has-error');
                password.focus();
                event.preventDefault();
            }
            else {
                password.closest('.form-group').removeClass('has-error');
                $("#lblPass").html("Password:" + "<font color='red'>*</font>");
            }

            //validate confirm password

            var confirmPassword = $("#ConfirmPasswordVal");
            var confirmPasswordValue = $("#ConfirmPasswordVal").val();
            // check not empty
            if (!confirmPasswordValue) {
                $("#lblConfirmPass").text(messages.edit_disk_lbl_confirm_password_empty);
                confirmPassword.closest('.form-group').addClass('has-error');
                confirmPassword.focus();
                event.preventDefault();
            }
            // check length
            else if (confirmPasswordValue != passwordValue) {
                $("#lblConfirmPass").text(messages.edit_disk_lbl_confirm_password_mismatch);
                confirmPassword.closest('.form-group').addClass('has-error');
                confirmPassword.focus();
                event.preventDefault();
            } else {
                confirmPassword.closest('.form-group').removeClass('has-error');
                $("#lblConfirmPass").html("Confirm Password:" + "<font color='red'>*</font>");
            }
        }
    });
});