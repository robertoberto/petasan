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


function set_cancel_add_cluster(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });

}


//when submit form

$("#addcluster_form").submit(function (event) {

    //........................ validate cluster name......................

    var clusterName = $("#clusterName");
    var clusterNameValue = $("#clusterName").val();
    // check not empty
    if (!clusterNameValue) {
        $("#clusterName_lbl").text(messages.add_cluster_lbl_name_empty);
        clusterName.closest('.form-group').addClass('has-error');
        clusterName.focus();
        event.preventDefault();
    }

    else {
        clusterName.closest('.form-group').removeClass('has-error');
        $("#clusterName_lbl").html("Cluster Name:" + "<font color='red'>*</font>");
    }


    //........................ validate cluster IP ......................
    var dest_cluster_ip = $("#dest_cluster_ip");
    var dest_cluster_ip_value = $("#dest_cluster_ip").val();
    // check not empty
    if (!dest_cluster_ip_value) {
        $("#lblDestinationIP").text(messages.add_cluster_lbl_ip_empty);
        dest_cluster_ip.closest('.form-group').addClass('has-error');
        dest_cluster_ip.focus();
        event.preventDefault();
    }

    else {
        dest_cluster_ip.closest('.form-group').removeClass('has-error');
        $("#lblDestinationIP").html("Remote IP:" + "<font color='red'>*</font>");
    }

    //........................ validate User Name ......................

    var userName = $("#userName");
    var userNameValue = $("#userName").val();
    // check not empty
    if (!userNameValue) {
        $("#userName_lbl").text(messages.add_cluster_lbl_user_name_empty);
        userName.closest('.form-group').addClass('has-error');
        userName.focus();
        event.preventDefault();
    }

    else {
        userName.closest('.form-group').removeClass('has-error');
        $("#userName_lbl").html("user Name:" + "<font color='red'>*</font>");
    }

     //........................ validate User Private key ......................

    var userkey = $("#key");
    var userkeyValue = $("#key").val();
    // check not empty
    if (!userkeyValue) {
        $("#key_lbl").text(messages.add_cluster_lbl_user_name_empty);
        userkey.closest('.form-group').addClass('has-error');
        userkey.focus();
        event.preventDefault();
    }

    else {
        userkey.closest('.form-group').removeClass('has-error');
        $("#key_lbl").html("User's Private Key:" + "<font color='red'>*</font>");
    }

});

$('#test_succeed').hide();
$('#test_failed').hide();
$('#overlay').hide();

function test_connection(get_test_connection_url) {
    $('#test_succeed').hide();
    $('#test_failed').hide();
    var cluster_name = "";

    if ($("#clusterName").val().length > 0) {
        cluster_name = $("#clusterName").val();}
        if ($("#dest_cluster_ip").val().length > 0) {
        dest_cluster_ip = $("#dest_cluster_ip").val();}
            if ($("#userName").val().length > 0) {
        userName = $("#userName").val();}
                if ($("#key").val().length > 0) {
        key = $("#key").val();}
    $('#overlay').show();
    $.ajax({

        url: get_test_connection_url,
        type: "get",
        data: {
            cluster_name: cluster_name,
            dest_cluster_ip: dest_cluster_ip,
            userName: userName,
            key: key
        },
        success: function (data) {
             var test_success = $("#test_success").val();
             var test_fail = $("#test_fail").val();

            if (data == "true")
            {
                //alert(test_success);
                $('#overlay').hide();
                $('#test_succeed').show();
            }
            else
            {
                //alert(test_fail);
                $('#overlay').hide();
                $('#failed_sent').text(test_fail);
                $('#test_failed').show();
            }

        },
        error: function () {
             $('#overlay').hide();
            $('#failed_sent').text(data);
            $('#test_failed').show();

        }

    });

}
