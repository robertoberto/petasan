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


$("#manage_disk_config").submit(function (event) {

        var iqn = $("#iqnVal");
        var iqnValue = $("#iqnVal").val();
        // check not empty
        if (!iqnValue) {
            $("#lblIqn").text("Default base/prefix |" + " please enter Iqn ");
            $("#lblIqn").closest('.form-group').addClass('has-error');
            iqn.closest('.form-group').addClass('has-error');
            iqn.focus();
            event.preventDefault();
        }
        else {
            $("#lblIqn").closest('.form-group').removeClass('has-error');
            iqn.closest('.form-group').removeClass('has-error');
            $("#lblIqn").html("Default base/prefix :"+" <font color='red'>*</font>");

        }


        // check length
        //
        if (!iqnValue.match(/^(?:iqn\.[0-9]{4}-[0-9]{2}(?:\.[a-z](?:[a-z0-9\-]*[a-z0-9])?)+(?::.*)?)$/)) {


            $("#lblIqn").text("Iqn base/prefix " + " |  please enter Iqn in a valid format ");
            $("#lblIqn").closest('.form-group').addClass('has-error');
            iqn.closest('.form-group').addClass('has-error');
            iqn.focus();
            event.preventDefault();


        } else {
            $("#lblIqn").closest('.form-group').removeClass('has-error');
            iqn.closest('.form-group').removeClass('has-error');
            $("#lblIqn").html("Iqn base/prefix  :"+" <font color='red'>*</font>");
        }
    }
);

