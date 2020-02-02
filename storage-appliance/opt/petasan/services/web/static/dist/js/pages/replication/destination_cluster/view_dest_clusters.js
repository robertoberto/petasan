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

function load_dest_cluster_info(get_dest_cluster_info_url) {

    $('#destClusterInfoArea').hide();
    $('#img').show();

    $.ajax({
        url: get_dest_cluster_info_url,
        type: "get",
        success: function (data) {

            var cluster_data = JSON.parse(data);
            console.log(data);
            $('#dest_clusterInfo_NameValue').html(cluster_data['cluster_name']);
            $('#dest_clusterIPValue').html(cluster_data['remote_ip']);
            $('#dest_clusterUserNameValue').html(cluster_data['user_name']);
            $('#dest_clusterKeyValue').html(cluster_data['ssh_private_key']);
            $('#img').hide();
            $('#destClusterInfoArea').show();

        },
        error: function () {

        }

    });

}