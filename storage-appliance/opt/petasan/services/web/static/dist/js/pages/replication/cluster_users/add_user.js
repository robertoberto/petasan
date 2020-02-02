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


function user_add_cancel(path) {
    $("#cancelBtn").click(function () {

        window.location = path;
    });
}



$("#add_user_form").submit(function (event) {
    var user_name = $("#userName");
    var user_name_val = $("#userName").val();
    if (!user_name_val) {
        $("#lblUserName").text(messages.user_name_required);
        user_name.closest('.form-group').addClass('has-error');
        user_name.focus();
        event.preventDefault();
    }
    else if(!isNaN(user_name_val) || user_name_val.indexOf(" ") != -1){
        $("#lblUserName").text(messages.user_name_valid);
        user_name.closest('.form-group').addClass('has-error');
        user_name.focus();
        event.preventDefault();
    }
    else{
        user_name.closest('.form-group').removeClass('has-error');
        $("#lblUserName").text("User Name:");
    }
    var pools = $('#pools');
    var pools_val = $('#pools').val();
    if(pools_val == null){
        $("#lblPools").text(messages.pools_required);
        pools.closest('.form-group').addClass('has-error');
        pools.focus();
        event.preventDefault();

    }else{
        pools.closest('.form-group').removeClass('has-error');
        $("#lblPools").text("Authorized Pools:");
    }
});