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

function load_profile_info(profile_name){
    $('#profile_name_val').html("");
    $('#k_val').html("");
    $('#profileInfo_k').hide();
    $('#m_val').html("");
    $('#profileInfo_m').hide();
    $('#plugin_val').html("");
    $('#profileInfo_plugin').hide();
    $('#locality_val').html("");
    $('#profileInfo_locality').hide();
    $('#durability_estimator_val').html("");
    $('#profileInfo_durability_estimator').hide();
    $('#packet_size_val').html("");
    $('#profileInfo_packet_size').hide();
    $('#strip_unit_val').html("");
    $('#profileInfo_strip_unit').hide();
    $('#technique_val').html("");
    $('#profileInfo_technique').hide();


    $('#profileInfoArea').hide();
    $('#img').show();

    $.ajax({
        url: '/ec_profile/get/'+profile_name+'',
        type: "get",
        success: function (data) {

            var profile_info = JSON.parse(data);

            $('#profile_name_val').html(profile_info.name);
            if(profile_info.k > 0){
                $('#k_val').html(profile_info.k);
                $('#profileInfo_k').show();
            }
            if(profile_info.m > 0){
                $('#m_val').html(profile_info.m);
                $('#profileInfo_m').show();
            }
            if(profile_info['plugin'].length > 0){
                $('#plugin_val').html(profile_info['plugin']);
                $('#profileInfo_plugin').show();
            }
            if(profile_info.locality > 0){
                $('#locality_val').html(profile_info.locality);
                $('#profileInfo_locality').show();
            }
            if(profile_info.durability_estimator > 0){
                $('#durability_estimator_val').html(profile_info.durability_estimator);
                $('#profileInfo_durability_estimator').show();
            }
            if(profile_info.packet_size > 0){
                $('#packet_size_val').html(profile_info.packet_size);
                $('#profileInfo_packet_size').show();
            }
            if(profile_info.strip_unit.length > 0){
                $('#strip_unit_val').html(profile_info.strip_unit);
                $('#profileInfo_strip_unit').show();
            }
            if(profile_info.technique.length > 0){
                $('#technique_val').html(profile_info.technique);
                $('#profileInfo_technique').show();
            }
            console.log()


            $('#img').hide();
            $('#profileInfoArea').show();

        },
        error: function () {

        }

    });

}



function doDelete(profile_name){
    confirm_deleting_ecProfile = messages.confirm_deleting_ecProfile;
    confirm_deleting_ecProfile = confirm_deleting_ecProfile.replace("$" , profile_name);
    var result = confirm(confirm_deleting_ecProfile);
    if(!result){
        return false;
    }
}
















