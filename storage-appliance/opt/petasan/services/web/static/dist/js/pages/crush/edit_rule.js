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

function set_cancel_edit_rule(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });

}

//when submit form

$("#edit_rule_form").submit(function (event) {



    //........................ validate rule info ......................
    var ruleInfo = $("#ruleData");
    var ruleInfoValue = $("#ruleData").val();
    // check not empty
    if (!ruleInfoValue) {
        $("#ruleData_lbl").text(messages.add_rule_lbl_info_empty);
        ruleInfo.closest('.form-group').addClass('has-error');
        ruleInfo.focus();
        event.preventDefault();
    }

    else {
        ruleInfo.closest('.form-group').removeClass('has-error');
        $("#ruleData_lbl").html("Rule:" + "<font color='red'>*</font>");
    }

});


