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


var jerasure_techniques = ['reed_sol_van' , 'reed_sol_r6_op' , 'cauchy_orig' , 'cauchy_good' , 'liberation' , 'blaum_roth' , 'liber8tion'].sort();
var isa_techniques = ['reed_sol_van' , 'cauchy'].sort();
var techniques = ['reed_sol_van' , 'reed_sol_r6_op' , 'cauchy_orig' , 'cauchy_good' , 'liberation' , 'blaum_roth' , 'liber8tion' , 'cauchy'].sort();
var optional_tags = ['plugin' , 'technique' , 'stripe_unit' , 'packet_size' , 'locality' , 'durability_estimator'].sort();
var hidden_tags_ids = ['#technique_div' , '#packet_size_div' , '#locality_div' , '#durability_estimator_div'].sort();
var plugins_related_fields = ['technique' , 'packet_size' , 'durability_estimator' , 'locality'].sort();


function onChangeAdvancedCheckbox(element){
    if($( element ).find("i").hasClass("glyphicon glyphicon-plus")){
        $(element).find("i").attr("class", "glyphicon glyphicon-minus");
        showHideTags(".toggle_show_hide" , "show");
        showHideTagsArray(hidden_tags_ids , "hide");
        $('#advanced').val("checked");
    }else{
        $(element).find("i").attr("class", "glyphicon glyphicon-plus");
        showHideTags(".toggle_show_hide" , "hide");
        removeTagsValues(optional_tags);
        $('#advanced').val("unchecked");
        removeErrorClass();
    }

}


function onChangePlugins(element){
    removeErrorClass();
    removeTagsValues(plugins_related_fields);
    deleteTags(techniques);
    if($(element).val() == "jerasure"){
        appendOptionTag(jerasure_techniques);
        showHideTags("#packet_size_div" , "show");
        showHideTags("#technique_div" , "show");
        showHideTags("#locality_div" , "hide");
        showHideTags("#durability_estimator_div" , "hide");
    }else if($(element).val() == "lrc"){
        showHideTags("#packet_size_div" , "hide");
        showHideTags("#locality_div" , "show");
        showHideTags("#durability_estimator_div" , "hide");
        showHideTags("#technique_div" , "hide");
    }else if($(element).val() == "shec"){
        showHideTags("#packet_size_div" , "hide");
        showHideTags("#locality_div" , "hide");
        showHideTags("#durability_estimator_div" , "show");
        showHideTags("#technique_div" , "hide");
    }else if($(element).val() == "isa"){
        appendOptionTag(isa_techniques);
        showHideTags("#technique_div" , "show");
        showHideTags("#packet_size_div" , "hide");
        showHideTags("#locality_div" , "hide");
        showHideTags("#durability_estimator_div" , "hide");
    }else{
        showHideTags("#technique_div" , "hide");
        showHideTags("#packet_size_div" , "hide");
        showHideTags("#locality_div" , "hide");
        showHideTags("#durability_estimator_div" , "hide");

    }

}

function deleteTags(tags_ids){
    $.each(tags_ids , function(key , value){
       $('#'+value+'').remove();
    });
}


function appendOptionTag(techniques){
    $.each(techniques, function(key , value) {
     $('#technique').append($("<option></option>").attr("value",value).text(value).attr("id" , value));
});
}


function showHideTags(name , action_function){
    $(name).each(function(){
            if (action_function == "show"){
                $(name).show();
            }else{
                $(name).hide();
            }
        });
}


function removeTagsValues(Tags_ids){
    $.each(Tags_ids , function(key , value){
       $('#'+value+'').val("");
    });
}

function showHideTagsArray(tags_array , action){
    $.each(tags_array , function(key , value){
       if (action == "show"){
                $(value).show();
            }else{
                $(value).hide();
            }
    });
}

function removeErrorClass(){
        $('#packet_size').closest('.form-group').removeClass('has-error');
        $("#label_packet_size").text("Packet Size:");
        $('#locality').closest('.form-group').removeClass('has-error');
        $("#label_locality").text("Locality:").append("<font color='red'>*</font>");
        $('#durability_estimator').closest('.form-group').removeClass('has-error');
        $("#label_durability_estimator").text("Durability Estimator:").append("<font color='red'>*</font>");
    }





$("#ec_profile_form").submit(function (event){
    var profile_name = $("#name");
    var profile_name_val = $("#name").val();
    if (!profile_name_val) {
        $("#label_name").text(messages.profile_name_required);
        profile_name.closest('.form-group').addClass('has-error');
        profile_name.focus();
        event.preventDefault();
    }
    else if (profile_name_val.indexOf(" ") != -1) {
            $("#label_name").text(messages.profile_name_shouldnot_have_space);
            profile_name.closest('.form-group').addClass('has-error');
            profile_name.focus();
            event.preventDefault();
    }
    else if (!isNaN(profile_name_val)) {
        $("#label_name").text(messages.profile_name_should_be_string);
        profile_name.closest('.form-group').addClass('has-error');
        profile_name.focus();
        event.preventDefault();
    }else{
        profile_name.closest('.form-group').removeClass('has-error');
        $("#label_name").text("Name:");
    }


    var profile_k = $("#k");
    var profile_k_val = $("#k").val();
    if (!profile_k_val) {
        $("#label_k").text(messages.profile_k_required);
        profile_k.closest('.form-group').addClass('has-error');
        profile_k.focus();
        event.preventDefault();
    }
    else if (isNaN(profile_k_val)) {
        $("#label_k").text(messages.profile_k_should_be_a_number);
        profile_k.closest('.form-group').addClass('has-error');
        profile_k.focus();
        event.preventDefault();
    }else{
        profile_k.closest('.form-group').removeClass('has-error');
        $("#label_k").text("K:");
    }


    var profile_m = $("#m");
    var profile_m_val = $("#m").val();
    if (!profile_m_val) {
        $("#label_m").text(messages.profile_m_required);
        profile_m.closest('.form-group').addClass('has-error');
        profile_m.focus();
        event.preventDefault();
    }
    else if (isNaN(profile_m_val)) {
        $("#label_m").text(messages.profile_m_should_be_a_number);
        profile_m.closest('.form-group').addClass('has-error');
        profile_m.focus();
        event.preventDefault();
    }else{
        profile_m.closest('.form-group').removeClass('has-error');
        $("#label_m").text("M:");
    }






    if ($('#advanced').val() == 'checked'){

        var packet_size_val = $('#packet_size').val();
        var packet_size_input = $('#packet_size');

        if (packet_size_val != "" && isNaN(packet_size_val)) {
        $("#label_packet_size").text(messages.profile_packet_size_should_be_a_number);
        packet_size_input.closest('.form-group').addClass('has-error');
        packet_size_input.focus();
        event.preventDefault();
    }else{
        packet_size_input.closest('.form-group').removeClass('has-error');
        $("#label_packet_size").text("Packet Size:");
    }

        var locality_val = $('#locality').val();
        var locality_input = $('#locality');

        if($('#plugin').val() == 'lrc' && locality_val == ""){
            $("#label_locality").text(messages.profile_locality_should_be_entered);
            locality_input.closest('.form-group').addClass('has-error');
            locality_input.focus();
            event.preventDefault();
        }else if (locality_val != "" && isNaN(locality_val)) {
            $("#label_locality").text(messages.profile_locality_should_be_a_number);
            locality_input.closest('.form-group').addClass('has-error');
            locality_input.focus();
            event.preventDefault();
        }else{
            locality_input.closest('.form-group').removeClass('has-error');
            $("#label_locality").text("Locality:");
        }


        var durability_estimator_val = $('#durability_estimator').val();
        var durability_estimator_input = $('#durability_estimator');

        if($('#plugin').val() == 'shec' && durability_estimator_val == ""){
            $("#label_durability_estimator").text(messages.profile_durability_estimator_should_be_entered);
            durability_estimator_input.closest('.form-group').addClass('has-error');
            durability_estimator_input.focus();
            event.preventDefault();
        }else if (durability_estimator_val != "" && isNaN(durability_estimator_val)) {
            $("#label_durability_estimator").text(messages.profile_durability_estimator_should_be_a_number);
            durability_estimator_input.closest('.form-group').addClass('has-error');
            durability_estimator_input.focus();
            event.preventDefault();
        }else{
            durability_estimator_input.closest('.form-group').removeClass('has-error');
            $("#label_durability_estimator").text("Durability Estimator:");
        }


    }

});


function set_cancel_add_ec_profile(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });
}
