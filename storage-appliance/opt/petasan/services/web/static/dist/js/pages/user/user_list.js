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

function load_popup_info(get_user_info_url) {

    $('#userInfoArea').hide();
    $('#img').show();


    $.ajax({
        url: get_user_info_url,
        type: "get",
        success: function (data) {

            // get_pool_info_url  --> '/pool/<pool_name>'  --> after split -->  ['','pool','<pool_name>']  --> the second element ..
            var pool_name = get_user_info_url.split('/')[2];
            var user_data = JSON.parse(data);
            console.log(user_data);

            $('#userInfo_NameValue').html(user_data['name']);
            $('#userInfo_UserNameValue').html(user_data['user_name']);
            if (user_data['email']) {
                $('#userInfo_EmailValue').html(user_data['email']);
            }
            else {
                $('#userInfo_EmailValue').html("&nbsp;");
            }
            if (user_data['role_id'] == 1) {
                $('#userInfo_RoleValue').html("Administrator");
            }
            else {
                $('#userInfo_RoleValue').html("Viewer");
            }

            if (user_data['notfiy'] == false) {
                $('#userInfo_NotificationValue').html('No');
            }
            else if (user_data['notfiy'] == true) {
                $('#userInfo_NotificationValue').html('Yes');

            }


            $('#img').hide();
            $('#userInfoArea').show();

        },
        error: function () {

        }

    });

}
