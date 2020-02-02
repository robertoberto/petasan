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


function resetKey(user_name){
    $.ajax({
        url: '/replication_users/update_user_private_key/' + user_name,
        type: "get",
        async:false,
        success: function (data) {
            if(data.length > 0){
                var privateKey = JSON.parse(data);
                $('#key').html(privateKey);
            }
        },
        error: function () {
        }

    });
}