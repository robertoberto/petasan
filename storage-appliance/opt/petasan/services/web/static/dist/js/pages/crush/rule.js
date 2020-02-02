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

function load_rule_info(get_rule_info_url) {

    $('#ruleInfoArea').hide();
    $('#img').show();

    $.ajax({
        url: get_rule_info_url,
        type: "get",
        success: function (data) {

            var rule_name = get_rule_info_url.split('/');
            // get_rule_info_url = '/rule/<rule_name>'  ,  so the list : rule_name = ['','rule', '<rule_name>'] ...

            var rule_body = JSON.parse(data);

            $('#ruleInfo_NameValue').html(rule_name[2]);  // the third element in the list : rule_name  // we got the rule name from the url
            $('#ruleInfo_BodyValue').html(rule_body);     // we got the rule body from the data comes from the ajax call

            $('#img').hide();
            $('#ruleInfoArea').show();

        },
        error: function () {

        }

    });

}