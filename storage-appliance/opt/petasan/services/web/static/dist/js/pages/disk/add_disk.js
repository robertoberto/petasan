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

function set_cancel_add(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });
}


function onChangePoolType(pool_type){
    if(pool_type == "replicated"){
        $('#erasure_pool_section').hide();
        $('#plus').hide();

    }else{
        $('#erasure_pool_section').show();
        $('#plus').show();
    }
}




function set_slider_add(size_list) {
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

            $("#diskSize").change(function () {
                var num = $("#diskSize").val();
                $("#diskSizeVal").val(num);
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

    $("#diskName").focus();

    if ($('#orpUseFirstRangeYes').is(':checked')) {
        $('#divPath2').hide();
        $('#divPath1').hide();
    }

    if ($('#orpAclAll').is(':checked')) {
        $('#IqnVal').hide();
    } else {
        $('#IqnVal').show();
    }

    if ($('#orpAuthNo').is(':checked')) {
        $('#divUserName').hide();
        $('#divPassword').hide();
        $('#divConfirmPassword').hide();
    } else {
        $('#divUserName').show();
        $('#divPassword').show();
        $('#divConfirmPassword').show();
    }

    if ($("#ActivePaths").val() > 2){
        $('#divPath2').hide();
        $('#divPath1').hide();
        $("#orpUseFirstRangeYes").prop('checked', true);
        $("#orpUseFirstRangeYes").attr('disabled', 'disabled');
        $("#orpUseFirstRangeNo").attr('disabled', 'disabled');
    } else if ($("#ActivePaths").val() == 2 && ($('#orpUseFirstRangeNo').is(':checked'))) {
        $('#divPath2').show();
        $('#divPath1').show();
    } else if ($("#ActivePaths").val() == 1 && ($('#orpUseFirstRangeNo').is(':checked'))) {
        $('#divPath2').hide();
        $('#divPath1').show();
    }

    //$('#UserNameVal').val('');
    //$('#PasswordVal').val('');
    //$('#ConfirmPasswordVal').val('');
    //select 'rbd' option by default
    $("#pool").each(function(){ $(this).find('option[value="'+ 'rbd' +'"]').prop('selected', true); });


        var pool_type = $('#form_pool_type').val();
        var replicated_pool = $('#form_replicated_pool').val();
        var erasure_pool = $('#form_erasure_pool').val();

    if(pool_type.length > 0 ){

        if(pool_type == 'replicated'){
            $('#replicated').attr('checked',true);
            $('#pool').val(replicated_pool);

        }else{
            $('#pool').val(replicated_pool);
            $('#erasure').attr('checked',true);
            $('#er_pool').val(erasure_pool);
        }
        onChangePoolType(pool_type);
    }


});

$('input:radio[name="orpUseFirstRange"]').change(
    function () {
        if ($('#orpUseFirstRangeYes').is(':checked')) {
            $('#divPath2').hide();
            $('#divPath1').hide();

        } else {
            $('#divPath1').show();
            var diskActivePaths = $("#ActivePaths").val();
            if (diskActivePaths == 2) {
                $('#divPath2').show();
            } else {
                $('#divPath2').hide();
            }
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

$("#ActivePaths").bind('keyup mouseup keydown mousedown', function () {
    var ActivePaths = $("#ActivePaths");
    var ActivePathsValue = $("#ActivePaths").val();

    if (ActivePathsValue >= 3) {
        $("#orpUseFirstRangeYes").prop("checked", true);
        $("#orpUseFirstRangeYes").attr('disabled', 'disabled');
        $("#orpUseFirstRangeNo").attr('disabled', 'disabled');
        $('#divPath2').hide();
        $('#divPath1').hide();
        $("#path1Val").removeAttr('value');
        $("#path2Val").removeAttr('value');
    }
    else {
        $("#orpUseFirstRangeYes").removeAttr('disabled');
        $("#orpUseFirstRangeNo").removeAttr('disabled');

        if ($("#orpUseFirstRangeNo").is(':checked')) {
            $('#divPath1').show();
            if (ActivePathsValue == 2) {
                $('#divPath2').show();
            } else if (ActivePathsValue == 1) {
                $('#divPath2').hide();
            }
        }
    }
});

//when submit form

$("#add_task_form").submit(function (event) {

    // validate for size

    var diskSize = $("#diskSizeVal");
    var diskSizeValue = $("#diskSizeVal").val();
    // check not empty
    if (!diskSizeValue) {
        $("#lblDiskSize").text(messages.add_disk_lbl_size_empty);
        diskSize.closest('.form-group').addClass('has-error');
        diskSize.focus();
        event.preventDefault();
    }
    // check is digit
    else if (!diskSizeValue.match(/^\d+$/)) {
        $("#lblDiskSize").text(messages.add_disk_lbl_size_invalid);
        diskSize.closest('.form-group').addClass('has-error');
        diskSize.focus();
        event.preventDefault();
    }
    // check equal zero
    else if (diskSizeValue == 0) {
        $("#lblDiskSize").text(messages.add_disk_lbl_size_invalid);
        diskSize.closest('.form-group').addClass('has-error');
        diskSize.focus();
        event.preventDefault();
    }
    else {
        diskSize.closest('.form-group').removeClass('has-error');
        $("#lblDiskSize").text("Size :");
    }


    // validate disk name

    var diskName = $("#diskName");
    var diskNameValue = $("#diskName").val();
    // check not empty
    if (!diskNameValue) {
        $("#lblDiskName").text(messages.add_disk_lbl_name_empty);
        diskName.closest('.form-group').addClass('has-error');
        diskName.focus();
        event.preventDefault();
    }
    // check length
    else if (!diskNameValue.length > 50) {
        $("#lblDiskName").text(messages.add_disk_lbl_name_length);
        diskName.closest('.form-group').addClass('has-error');
        diskName.focus();
        event.preventDefault();
    }
    else {
        diskName.closest('.form-group').removeClass('has-error');
        $("#lblDiskName").html("Disk Name:" + "<font color='red'>*</font>");
    }

    // validate for ISCSI Subnet

    var ISCSIsubnet = $("#ISCSISubnet");
    var ISCSIsubnetValue = $("#ISCSISubnet").val();
    // check not empty
    if (ISCSIsubnetValue == 0) {
        $("#lblISCSISubnet").text(messages.add_disk_lbl_subnet_empty);
        ISCSIsubnet.closest('.form-group').addClass('has-error');
        ISCSIsubnet.focus();
        event.preventDefault();
    }
    else {
        ISCSIsubnet.closest('.form-group').removeClass('has-error');
        $("#lblISCSISubnet").html("iSCSI Subnet:" + "<font color='red'>*</font>");
    }

    // validate for path1

    function IPToNumber(s) {

        var arr = s.split('.');
        var n = 0;
        for (var i = 0; i < 4; i++) {

            n = n * 256;
            n += parseInt(arr[i], 10);

        }

        return n;
    }

    function ValidateIPaddress(ipaddress) {
        if (ipaddress.match(/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/)) {
            return (true);
        }

        return (false);
    }

    if (!$('#orpUseFirstRangeYes').is(':checked')) {

        // check is valid ip address
        if (!ValidateIPaddress($("#path1Val").val())) {
            $("#lblPath1").text(messages.add_disk_lbl_path1_invalid);
            $("#path1Val").closest('.form-group').addClass('has-error');
            $("#path1Val").focus();
            event.preventDefault();

        } else {
            $("#path1Val").closest('.form-group').removeClass('has-error');
            $("#lblPath1").html("Path1:" + "<font color='red'>*</font>");
        }

        if ($("#ActivePaths").val() == 2) {

            // check is valid ip address
            if (!ValidateIPaddress($("#path2Val").val())) {
                $("#lblPath2").text(messages.add_disk_lbl_path2_invalid);
                $("#path2Val").closest('.form-group').addClass('has-error');
                $("#path2Val").focus();
                event.preventDefault();

            } else {
                $("#path2Val").closest('.form-group').removeClass('has-error');
                $("#lblPath2").html("Path2:" + "<font color='red'>*</font>");
            }

        }
    }

    if (!$('#orpAclAll').is(':checked')) {

        var iqn = $("#IqnVal");
        var iqnValue = $("#IqnVal").val();
        // check not empty
        if (!iqnValue) {
            $("#lblACL").text(messages.add_disk_lbl_iqn_empty);
            $("#lblACL").closest('.form-group').addClass('has-error');
            iqn.closest('.form-group').addClass('has-error');
            iqn.focus();
            event.preventDefault();
        }
        else {
            $("#lblACL").closest('.form-group').removeClass('has-error');
            iqn.closest('.form-group').removeClass('has-error');
            $("#lblACL").text("Client ACL :");
            $("#lblIqnVal").html("IQN(s):" + "<font color='red'>*</font>");
        }


        // check length
        if (iqnValue.toLowerCase().indexOf(",") >= 0) {
            var values = iqnValue.split(',');
            for (i = 0; i < values.length; i++) {
                if (!values[i].match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {
                    $("#lblACL").text(messages.add_disk_lbl_iqn_invalid);
                    $("#lblACL").closest('.form-group').addClass('has-error');
                    iqn.closest('.form-group').addClass('has-error');
                    iqn.focus();
                    event.preventDefault();
                } else {
                    $("#lblACL").closest('.form-group').removeClass('has-error');
                    iqn.closest('.form-group').removeClass('has-error');
                    $("#lblACL").text("Client ACL : ");
                    $("#lblIqnVal").html("IQN(s):" + "<font color='red'>*</font>");
                }
            }
        } else {
            if (!iqnValue.match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {
                $("#lblACL").text(messages.add_disk_lbl_iqn_invalid);
                $("#lblACL").closest('.form-group').addClass('has-error');
                iqn.closest('.form-group').addClass('has-error');
                iqn.focus();
                event.preventDefault();
            } else {
                $("#lblACL").closest('.form-group').removeClass('has-error');
                iqn.closest('.form-group').removeClass('has-error');
                $("#lblACL").text("Client ACL : ");
                $("#lblIqnVal").html("IQN(s):" + "<font color='red'>*</font>");
            }
        }
    }
// validare for user name and password if matched
    if (!$('#orpAuthNo').is(':checked')) {

        // validate
        // user name

        var userName = $("#UserNameVal");
        var userNameValue = $("#UserNameVal").val();
        // check not empty
        if (!userNameValue) {
            $("#lblUserName").text(messages.add_disk_lbl_username_empty);
            userName.closest('.form-group').addClass('has-error');
            userName.focus();
            event.preventDefault();
        }
        // check length
        else if (!userNameValue.length > 50) {
            $("#lblUserName").text(messages.add_disk_lbl_username_length);
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
            $("#lblPass").text(messages.add_disk_lbl_password_empty);
            password.closest('.form-group').addClass('has-error');
            password.focus();
            event.preventDefault();
        }
        // check length
        else if (passwordValue.length > 16 || passwordValue.length < 12) {
            $("#lblPass").text(messages.add_disk_lbl_password_length);
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
            $("#lblConfirmPass").text(messages.add_disk_lbl_confirm_password_empty);
            confirmPassword.closest('.form-group').addClass('has-error');
            confirmPassword.focus();
            event.preventDefault();
        }
        // check length
        else if (confirmPasswordValue != passwordValue) {
            $("#lblConfirmPass").text(messages.add_disk_lbl_confirm_password_mismatch);
            confirmPassword.closest('.form-group').addClass('has-error');
            confirmPassword.focus();
            event.preventDefault();
        } else {
            confirmPassword.closest('.form-group').removeClass('has-error');
            $("#lblConfirmPass").html("Confirm Password:" + "<font color='red'>*</font>");

        }

    }

    var data_pool = $('#er_pool');
    var data_pool_val = $('#er_pool').val();

    if($('#erasure').is(':checked')){
        if(data_pool_val == null){
            $('#er_lblPools').text(messages.add_disk_lbl_data_pool);
            data_pool.closest('.form-group').addClass('has-error');
            data_pool.focus();
            event.preventDefault();
        }else {
            data_pool.closest('.form-group').removeClass('has-error');
            $("#er_lblPools").html("Data Pool:" + "<font color='red'>*</font>");

        }
    }



});