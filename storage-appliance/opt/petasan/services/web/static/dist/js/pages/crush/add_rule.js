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

//********filling table from Puthon using jquery*******//

$(document).ready(function () {


    $("#name option").filter(function () {
        return $(this).val() == $("#ruleData").val();

    }).attr('selected', true);

    $("#name").on("change", function () {

        $("#ruleData").val($(this).find("option:selected").attr("value"));
        $("#ruleName").val($(this).find("option:selected").attr("name"));
    });


    var options = $("#name option");                    // Collect options
    options.detach().sort(function (a, b) {               // Detach from select, then Sort
        var at = $(a).text();
        var bt = $(b).text();
        return (at > bt) ? 1 : ((at < bt) ? -1 : 0);            // Tell the sort function how to order
    });
    options.appendTo("#name");

});




function set_cancel_add_rule(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });

}


//when submit form

$("#addRule_form").submit(function (event) {

    //........................ validate rule name......................

    var ruleName = $("#ruleName");
    var ruleNameValue = $("#ruleName").val();
    // check not empty
    if (!ruleNameValue) {
        $("#ruleName_lbl").text(messages.add_rule_lbl_name_empty);
        ruleName.closest('.form-group').addClass('has-error');
        ruleName.focus();
        event.preventDefault();
    }
    // check no whitespace
    else if (ruleNameValue.indexOf(" ")!=-1) {
        $("#ruleName_lbl").text(messages.add_rule_lbl_name_whitespace);
        ruleName.closest('.form-group').addClass('has-error');
        ruleName.focus();
        event.preventDefault();
    }
    else {
        ruleName.closest('.form-group').removeClass('has-error');
        $("#ruleName_lbl").html("Rule Name:" + "<font color='red'>*</font>");
    }


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


