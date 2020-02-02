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

function doDelete(name){
    confirm_deleting_name = messages.confirm_deleting_username;
    confirm_deleting_name = confirm_deleting_name.replace("$" , name);
    var result = confirm(confirm_deleting_name);
    if(!result){
        return false;
    }
}




function get_user_info(user_name){
    $('#username_val').html("");
    $('#private_key_val').html("");

    $('#userInfoArea').hide();
    $('#img').show();

    $.ajax({
        url: '/replication_users/get_user/'+user_name+'',
        type: "get",
        success: function (data) {

            var user_info = JSON.parse(data);
            var pools = "";
            for (i in user_info.auth_pools){
                pools += user_info.auth_pools[i];
                pools += " ,";
            }
            pools = pools.slice(0, -1);
            $('#username_val').html(user_info.user_name);
            $('#private_key_val').html(user_info.ssh_prv_key);

            $('#pools_list_val').html(pools);


            $('#img').hide();
            $('#userInfoArea').show();

        },
        error: function () {

        }

    });

}