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

$(document).ready(function () {

    //$("#Rep_CompressionAlg").hide();

    if ($('#pool_type').val() == 'replicated')
    {
        if ($("#compression_mode_hidden").val() != "none")
        {
            $("#Rep_CompressionAlg").show();
        }
    }


    else if ($('#pool_type').val() == 'erasure')
    {

    }

    //================================================================================================================//

    // shows the "CompressionAlg Div" in "Replicated Pool Div" on clicking the radiobutton "enabled" //
    // --------------------------------------------------------------------------------------------- //
    $("#rep_enabled").click(function () {
        $("#Rep_CompressionAlg").show();
    });

    // hides the "CompressionAlg Div" in "Replicated Pool Div" on clicking the radiobutton "disabled" //
    // ---------------------------------------------------------------------------------------------- //
    $("#rep_disabled").click(function () {
        $("#Rep_CompressionAlg").hide();
    });


    // shows the "CompressionAlg Div" in "EC Pool Div" on clicking the radiobutton "enabled" //
    // ------------------------------------------------------------------------------------- //
    $("#ec_enabled").click(function () {
        $("#EC_CompressionAlg").show();
    });

    // hides the "CompressionAlg Div" in "EC Pool Div" on clicking the radiobutton "disabled" //
    // -------------------------------------------------------------------------------------- //
    $("#ec_disabled").click(function () {
        $("#EC_CompressionAlg").hide();
    });


    //================================================================================================================//

});

//====================================================================================================================//

function set_cancel_add_rule(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });
}

//====================================================================================================================//

function get_Min_Max_rule_values(rule) {

    var rule_info = rule.split("##");

    selected_Rule_Min_value = parseInt(rule_info[1]) ;
    selected_Rule_Max_value = parseInt(rule_info[2]) ;

}

//====================================================================================================================//

// When Submitting Form : //

$("#editPool_form").submit(function (event) {

    // *****************************************************************************************************************
    // *****************************************************************************************************************
    //                                   First : "Replicated Pool Div" Validation :
    // *****************************************************************************************************************
    // *****************************************************************************************************************

    if (selected_pool == "replicated") {

        // ====================================
        // Validation of Replica Minimum Size :
        // ====================================
            var replicaMinSize = $("#replica_min_size");
            var replicaMinValue = $("#replica_min_size").val();
            var replicaSizeValue = $("#replica_size").val();

            if (replicaMinValue > replicaSizeValue) {
                $("#lblMinRep").text(messages.edit_pool_lbl_min_replica_size_error);
                replicaMinSize.closest('.form-group').addClass('has-error');
                replicaMinSize.focus();
                event.preventDefault();
            }

            else {
                replicaMinSize.closest('.form-group').removeClass('has-error');
                $("#lblMinRep").html("Min Size:" + "<font color='red'>*</font>");
            }
    }

    // *****************************************************************************************************************
    // *****************************************************************************************************************
    //                                          Second : "EC Pool Div" Validation :
    // *****************************************************************************************************************
    // *****************************************************************************************************************

    else if (selected_pool == "erasure") {

        // ==================================================
        // Validation of Min Size : ( >= K ) and ( <= K + M ) :
        // ==================================================

        var ec_MinNumber = $("#ec_min_size");
        var ec_MinNumberValue = $("#ec_min_size").val();
        ec_MinNumberValue = parseInt(ec_MinNumberValue);

        var ec_SizeValue = selected_K_value + selected_M_value ;

        // check if empty //
        // -------------- //

        if (!ec_MinNumberValue) {
            $("#lbl_EC_MinSize").text(messages.edit_ec_pool_lbl_MinSize_empty);
            ec_MinNumber.closest('.form-group').addClass('has-error');
            ec_MinNumber.focus();
            event.preventDefault();
        }

        // check if not digit //
        // ------------------ //
        else if (isNaN(ec_MinNumberValue)) {
            $("#lbl_EC_MinSize").text(messages.edit_ec_pool_lbl_MinSize_number_error);
            ec_MinNumber.closest('.form-group').addClass('has-error');
            ec_MinNumber.focus();
            event.preventDefault();
        }

        // check if digit is less than k or greater than k+m //
        // ------------------------------------------------- //
        else if (ec_MinNumberValue < selected_K_value || ec_MinNumberValue > ec_SizeValue) {

            $("#lbl_EC_MinSize").text(messages.edit_ec_pool_lbl_MinSize_number_error);
            ec_MinNumber.closest('.form-group').addClass('has-error');
            ec_MinNumber.focus();
            event.preventDefault();
        }

        else {
            ec_MinNumber.closest('.form-group').removeClass('has-error');
            $("#lbl_EC_MinSize").html("Min Size:" + "<font color='red'>*</font>");
        }

        // =========================
        // Validation of Rule Name :
        // =========================
        var ec_ruleName = $("#ec_rule_name");

        // Check if pool was ( Erasure ) : the selected "Rule" Max Size must be greater than or equal to (k+m) :
        // ----------------------------------------------------------------------------------------------------------
        if (selected_Rule_Max_value < ec_SizeValue) {
            $("#lbl_EC_RuleName").text(messages.edit_ec_pool_lbl_rule_max_size);
            ec_ruleName.closest('.form-group').addClass('has-error');
            ec_ruleName.focus();
            event.preventDefault();
        }

        // Check if pool was ( Erasure ) : the selected "Rule" Min Size must be less than or equal to (k+m) :
        // --------------------------------------------------------------------------------------------------

        else if (selected_Rule_Min_value > ec_SizeValue) {
            $("#lbl_EC_RuleName").text(messages.edit_ec_pool_lbl_rule_min_size);
            ec_ruleName.closest('.form-group').addClass('has-error');
            ec_ruleName.focus();
            event.preventDefault();
        }

        else {
            ec_ruleName.closest('.form-group').removeClass('has-error');
            $("#lbl_EC_RuleName").html("Rule Name:" + "<font color='red'>*</font>");
        }

    }


});
