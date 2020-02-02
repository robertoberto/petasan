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

$(document).ready(function () {

    // hide the divs as soon as the DOM is ready //
    // ======================================== //


    // shows the div on checking the box for iscsi_1
   $('#vlan1_check').click(function() {
    $("#vlan1").toggle(this.checked);
});


    // shows the div on checking the box for iscsi_2
   $('#vlan2_check').click(function() {
    $("#vlan2").toggle(this.checked);
});



    $(function () {
        $("[data-mask]").inputmask();
    });
});

$("#manage_network_config").submit(function (event) {



        var iqn = $("#iqnVal");
        var iqnValue = $("#iqnVal").val();
        // check not empty
        if (!iqnValue) {
            $("#lblIqn").text( messages.label_iqn);
            $("#lblIqn").closest('.form-group').addClass('has-error');
            iqn.closest('.form-group').addClass('has-error');
            iqn.focus();
            event.preventDefault();
        }
        else {
            $("#lblIqn").closest('.form-group').removeClass('has-error');
            iqn.closest('.form-group').removeClass('has-error');
            $("#lblIqn").html("Default base/prefix:" + "<font color='red'>*</font>");

        }


        // check length
        //
        if (!iqnValue.match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {


            $("#lblIqn").text( messages.label_iqn_not_valid_format);
            $("#lblIqn").closest('.form-group').addClass('has-error');
            iqn.closest('.form-group').addClass('has-error');
            iqn.focus();
            event.preventDefault();


        } else {
            $("#lblIqn").closest('.form-group').removeClass('has-error');
            iqn.closest('.form-group').removeClass('has-error');
            $("#lblIqn").html("IQN base/prefix:" + "<font color='red'>*</font>");
        }

        // validate for subnet 1

        var subnet1 = $("#subnet1Val");
        var subnet1Value = $("#subnet1Val").val();
        // check not empty
        if (!subnet1Value) {
            $("#lblSubnet1").text( messages.label_subnet_iscsi_1);
            subnet1.closest('.form-group').addClass('has-error');
            subnet1.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!subnet1Value.match(/^((128|192|224|240|248|252|254)\.0\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0)|255\.(0|128|192|224|240|248|252|254)))))$/)) {
            $("#lblSubnet1").text( messages.label_invalid_subnet_iscsi_1);
            subnet1.closest('.form-group').addClass('has-error');
            subnet1.focus();
            event.preventDefault();
        }
        else {
            subnet1.closest('.form-group').removeClass('has-error');
            $("#lblSubnet1").html("Subnet Mask:" + "<font color='red'>*</font>");
        }


        // validate for ip address


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

        var from_subnet1 = $("#fromSubnet1Val");
        var from_subnet1_value = from_subnet1.val();
        if (!from_subnet1_value) {

            $("#lblFromSubnet1").text(messages.label_from_ip_subnet_iscsi_1);
            from_subnet1.closest('.form-group').addClass('has-error');
            from_subnet1.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!ValidateIPaddress(from_subnet1_value)) {
            $("#lblFromSubnet1").text( messages.label_invalid_from_ip_subnet_iscsi_1);
            from_subnet1.closest('.form-group').addClass('has-error');
            from_subnet1.focus();
            event.preventDefault();
        }
        else {
            from_subnet1.closest('.form-group').removeClass('has-error');
            $("#lblFromSubnet1").html("Auto IP Range: From:" + "<font color='red'>*</font>");
        }
        // validate to for subnet mask 1

        var to_subnet1 = $("#toSubnet1Val");
        var to_subnet1_value = to_subnet1.val();
        if (!to_subnet1_value) {

            $("#lblToSubnet1").text(messages.label_to_ip_subnet_iscsi_1 );
            to_subnet1.closest('.form-group').addClass('has-error');
            to_subnet1.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!ValidateIPaddress(to_subnet1_value)) {
            $("#lblToSubnet1").text( messages.label_invalid_to_ip_subnet_iscsi_1);
            to_subnet1.closest('.form-group').addClass('has-error');
            to_subnet1.focus();
            event.preventDefault();
        }
        else {


            var res = IpSubnetCalculator.calculateCIDRPrefix(from_subnet1_value, subnet1Value);

            var ipTo = IPToNumber(to_subnet1_value);
            var ipFrom = IPToNumber(from_subnet1_value);
            var min1 = IPToNumber(res.ipLowStr);
            var max1 = IPToNumber(res.ipHighStr);
//                    set info for subnet mask path 1
            $("#Subnet1_Info").val(JSON.stringify(res));


            var isValid = (ipTo != 0 && (ipTo > min1 && ipTo < max1));

            if (!isValid) {
                $("#lblToSubnet1").text( messages.label_invalid_to_ip_not_in_range_subnet_iscsi_1);
                to_subnet1.closest('.form-group').addClass('has-error');
                to_subnet1.focus();
                event.preventDefault();

            } else if (ipTo <= ipFrom) {
                $("#lblToSubnet1").text( messages.label_invalid_to_ip_less_tahn_from_ip_subnet_iscsi_1 );
                to_subnet1.closest('.form-group').addClass('has-error');
                to_subnet1.focus();
                event.preventDefault();

            }
            else {
                to_subnet1.closest('.form-group').removeClass('has-error');
                $("#lblToSubnet1").html("To:" + "<font color='red'>*</font>");
            }
        }


        // validate for subnet 2

        var subnet2 = $("#subnet2Val");
        var subnet2Value = $("#subnet2Val").val();
        // check not empty
        if (!subnet2Value) {
            $("#lblSubnet2").text(messages.label_subnet_iscsi_2);
            subnet2.closest('.form-group').addClass('has-error');
            subnet2.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!subnet2Value.match(/^((128|192|224|240|248|252|254)\.0\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0\.0)|(255\.(((0|128|192|224|240|248|252|254)\.0)|255\.(0|128|192|224|240|248|252|254)))))$/)) {
            $("#lblSubnet2").text(messages.label_invalid_subnet_iscsi_2 );
            subnet2.closest('.form-group').addClass('has-error');
            subnet2.focus();
            event.preventDefault();
        }
        else {
            subnet2.closest('.form-group').removeClass('has-error');
            $("#lblSubnet2").html("Subnet Mask:" + "<font color='red'>*</font>");
        }
        //validate ip address from in subnet 2

        var from_subnet2 = $("#fromSubnet2Val");
        var from_subnet2_value = from_subnet2.val();


        if (!from_subnet2_value) {

            $("#lblFromSubnet2").text( messages.label_from_ip_subnet_iscsi_2 );
            from_subnet2.closest('.form-group').addClass('has-error');
            from_subnet2.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!ValidateIPaddress(from_subnet2_value)) {
            $("#lblFromSubnet2").text(messages.label_invalid_from_ip_subnet_iscsi_2);
            from_subnet2.closest('.form-group').addClass('has-error');
            from_subnet2.focus();
            event.preventDefault();
        }
        else {
            from_subnet2.closest('.form-group').removeClass('has-error');
            $("#lblFromSubnet2").html("Auto IP Range: From:" + "<font color='red'>*</font>");
        }
        // validate to for subnet mask 1

        var to_subnet2 = $("#toSubnet2Val");
        var to_subnet2_value = to_subnet2.val();
        if (!to_subnet2_value) {

            $("#lblToSubnet2").text(messages.label_to_ip_subnet_iscsi_2 );
            to_subnet2.closest('.form-group').addClass('has-error');
            to_subnet2.focus();
            event.preventDefault();
        }
        // check is valid

        else if (!ValidateIPaddress(to_subnet2_value)) {
            $("#lblToSubnet2").text( messages.label_invalid_to_ip_subnet_iscsi_2 );
            to_subnet2.closest('.form-group').addClass('has-error');
            to_subnet2.focus();
            event.preventDefault();
        }
        else {

            var res = IpSubnetCalculator.calculateCIDRPrefix(from_subnet2_value, subnet2Value);

            var ipTo = IPToNumber(to_subnet2_value);
            var ipFrom = IPToNumber(from_subnet2_value);
            var min1 = IPToNumber(res.ipLowStr);
            var max1 = IPToNumber(res.ipHighStr);

            $("#Subnet2_Info").val(JSON.stringify(res));


            var isValid = (ipTo != 0 && (ipTo > min1 && ipTo < max1));

            if (!isValid) {
                $("#lblToSubnet2").text(messages.label_invalid_to_ip_not_in_range_subnet_iscsi_2 );
                to_subnet2.closest('.form-group').addClass('has-error');
                to_subnet2.focus();
                event.preventDefault();

            } else if (ipTo <= ipFrom) {
                $("#lblToSubnet2").text( messages.label_invalid_to_ip_less_tahn_from_ip_subnet_iscsi_2);
                to_subnet2.closest('.form-group').addClass('has-error');
                to_subnet2.focus();
                event.preventDefault();

            }
            else {
                to_subnet2.closest('.form-group').removeClass('has-error');
                $("#lblToSubnet2").html("To:" + "<font color='red'>*</font>");
            }
        }




//........................ validate VLAN 1 ID ......................
var x = $("#vlan1_check").prop('checked');
        console.log(x)
        if(x == false)
        {
            $("#IDVal1").val("");
        }
else if(x){
        var vlan1ID = $("#IDVal1");
    var Valn1Value = $("#IDVal1").val();
    // check not empty
    if (!Valn1Value) {
        $("#lblvlan1id").text(messages.vlan1_lbl_id_empty);
        vlan1ID.closest('.form-group').addClass('has-error');
        vlan1ID.focus();
        event.preventDefault();
    }
  // check if has space //
    // ------------------ //
    else if (Valn1Value.indexOf(" ") != -1) {
        $("#lblvlan1id").text(messages.vlan1_lbl_has_space_error);
        vlan1ID.closest('.form-group').addClass('has-error');
        vlan1ID.focus();
        event.preventDefault();
    }

    // check if not digit //
    // ------------------ //
    else if (!Valn1Value.match(/^\d+$/)) {
        $("#lblvlan1id").text(messages.vlan1_lbl_number_error);
        vlan1ID.closest('.form-group').addClass('has-error');
        vlan1ID.focus();
        event.preventDefault();
    }

    // check if digit is less than 1 or greater than 4094 //
    // ---------------------------------------------------- //
    else if (Valn1Value < 1 || Valn1Value > 4094) {
        $("#lblvlan1id").text(messages.vlan1_lbl_number_error);
        vlan1ID.closest('.form-group').addClass('has-error');
        vlan1ID.focus();
        event.preventDefault();
    }

    else {
        vlan1ID.closest('.form-group').removeClass('has-error');
        $("#lblvlan1id").html("VLAN ID:" + "<font color='red'>*</font>");
    }
    }


        //........................ validate VLAN 2 ID ......................

var x2 = $("#vlan2_check").prop('checked');
        if(x2 == false)
        {
            $("#IDVal2").val("");
        }
        else if(x2){

        var vlan2ID = $("#IDVal2");
    var Valn2Value = $("#IDVal2").val();
    // check not empty
    if (!Valn2Value) {
        $("#lblvlan2id").text(messages.vlan1_lbl_id_empty);
        vlan2ID.closest('.form-group').addClass('has-error');
        vlan2ID.focus();
        event.preventDefault();
    }
  // check if has space //
    // ------------------ //
    else if (Valn2Value.indexOf(" ") != -1) {
        $("#lblvlan2id").text(messages.vlan1_lbl_has_space_error);
        vlan2ID.closest('.form-group').addClass('has-error');
        vlan2ID.focus();
        event.preventDefault();
    }

    // check if not digit //
    // ------------------ //
    else if (!Valn2Value.match(/^\d+$/)) {
        $("#lblvlan2id").text(messages.vlan1_lbl_number_error);
        vlan2ID.closest('.form-group').addClass('has-error');
        vlan2ID.focus();
        event.preventDefault();
    }

    // check if digit is less than 1 or greater than 4094 //
    // ---------------------------------------------------- //
    else if (Valn2Value < 1 || Valn2Value > 4094) {
        $("#lblvlan2id").text(messages.vlan1_lbl_number_error);
        vlan2ID.closest('.form-group').addClass('has-error');
        vlan2ID.focus();
        event.preventDefault();
    }

    else {
        vlan2ID.closest('.form-group').removeClass('has-error');
        $("#lblvlan2id").html("VLAN ID:" + "<font color='red'>*</font>");
    }

}

    }
);