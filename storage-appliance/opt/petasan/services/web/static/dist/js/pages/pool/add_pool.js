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

    // Adjust ComboBoxes in "Replicated Pool Div" //
    // ------------------------------------------ //

    // select '3' option by default
    $("#rep_replica_size").each(function () {
        $(this).find('option[value="' + '3' + '"]').prop('selected', true);
    });

    // select '2' option by default
    $("#rep_replica_min_size").each(function () {
        $(this).find('option[value="' + '2' + '"]').prop('selected', true);
    });

    // select 'snappy' option by default in both "Replicated Pool Div" and "EC Pool Div"
    $("#rep_compression_algorithm").each(function () {
        $(this).find('option[value="' + 'snappy' + '"]').prop('selected', true);
    });

    $("#ec_compression_algorithm").each(function () {
        $(this).find('option[value="' + 'snappy' + '"]').prop('selected', true);
    });

    //================================================================================================================//

    // shows the "EC Pool Div" on clicking the radiobutton "erasure" //
    // --------------------------------------------------------------- //
    $("#erasure").click(function () {
        selected_pool = "erasure";
        $("#replicated_pool_div").hide();
        $("#ec_pool_div").show();
    });

    // shows the "Replicated Pool Div" on clicking the radiobutton "replicated" //
    // ------------------------------------------------------------------------------- //
    $("#replicated").click(function () {
        selected_pool = "replicated";
        $("#ec_pool_div").hide();
        $("#replicated_pool_div").show();
    });

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

    // Sorting rule names in the combobox "rep_rule_name" //
    // -------------------------------------------------- //

    var options = $("#rep_rule_name option");                    // Collect options
    options.detach().sort(function (a, b) {               // Detach from select, then Sort
        var at = $(a).text();
        var bt = $(b).text();
        return (at > bt) ? 1 : ((at < bt) ? -1 : 0);            // Tell the sort function how to order
    });
    options.appendTo("#rep_rule_name");


    // Sorting rule names in the combobox "ec_rule_name" //
    // -------------------------------------------------- //

    var options = $("#ec_rule_name option");
    options.detach().sort(function (a, b) {
        var at = $(a).text();
        var bt = $(b).text();
        return (at > bt) ? 1 : ((at < bt) ? -1 : 0);
    });
    options.appendTo("#ec_rule_name");


    // Sorting profile names in the combobox "ec_profile" //
    // -------------------------------------------------- //

    var options = $("#ec_profile option");
    options.detach().sort(function (a, b) {
        var at = $(a).text();
        var bt = $(b).text();
        return (at > bt) ? 1 : ((at < bt) ? -1 : 0);
    });
    options.appendTo("#ec_profile");


});

//####################################################################################################################//

function set_cancel_add_rule(path) {
    $("#cancelBtn").click(function () {
        window.location = path;
    });
}

//####################################################################################################################//

function change_K_M_values(profile) {

    var profile_info = profile.split("##");
    //console.log(profile_info[0] + " - " + profile_info[1] + " - " + profile_info[2]);

    selected_K_value = parseInt(profile_info[1]) ;
    selected_M_value = parseInt(profile_info[2]) ;

    $('#ec_K').val(profile_info[1]);
    $('#ec_M').val(profile_info[2]);
    $('#ec_min_size').val(parseInt(profile_info[1])+1);
}


function get_Min_Max_rule_values(rule) {

    var rule_info = rule.split("##");

    selected_Rule_Min_value = parseInt(rule_info[1]) ;
    selected_Rule_Max_value = parseInt(rule_info[2]) ;

}

//####################################################################################################################//
// When Submitting Form : //
//####################################################################################################################//

$("#addPool_form").submit(function (event) {

    // =========================
        // Validation of Pool Name :
        // =========================
        var poolName = $("#name");
        var poolNameValue = $("#name").val();

        // check if empty //
        // -------------- //

        if (!poolNameValue) {
            $("#lblName").text(messages.add_pool_lbl_name_empty);
            poolName.closest('.form-group').addClass('has-error');
            poolName.focus();
            event.preventDefault();
        }

        // check if has space //
        // ------------------ //
        else if (poolNameValue.indexOf(" ") != -1) {
            $("#lblName").text(messages.add_pool_lbl_name_has_space_error);
            poolName.closest('.form-group').addClass('has-error');
            poolName.focus();
            event.preventDefault();
        }

        // check if pool name equals "all" + case insensitive --> "all" , "ALL" , "aLL" , "All" ... //
        // ---------------------------------------------------------------------------------------- //

        else if (poolNameValue.toLowerCase() == "all") {
            $("#lblName").text(messages.add_pool_lbl_name_equals_all);
            poolName.closest('.form-group').addClass('has-error');
            poolName.focus();
            event.preventDefault();
        }

        else {
            poolName.closest('.form-group').removeClass('has-error');
            $("#lblName").html("Pool Name:" + "<font color='red'>*</font>");
        }

    // *****************************************************************************************************************
    // *****************************************************************************************************************
    //                                   First : "Replicated Pool Div" Validation :
    // *****************************************************************************************************************
    // *****************************************************************************************************************

    if (selected_pool == "replicated") {

        // =========================
        // Validation of No of PGs :
        // =========================
        var pgNumber = $("#rep_pg_num");
        var pgNumberValue = $("#rep_pg_num").val();

        // check if empty //
        // -------------- //

        if (!pgNumberValue) {
            $("#lbl_Rep_PG").text(messages.add_pool_lbl_pg_empty);
            pgNumber.closest('.form-group').addClass('has-error');
            pgNumber.focus();
            event.preventDefault();
        }

        // check if has space //
        // ------------------ //
        else if (pgNumberValue.indexOf(" ") != -1) {
            $("#lbl_Rep_PG").text(messages.add_pool_lbl_pg_has_space_error);
            pgNumber.closest('.form-group').addClass('has-error');
            pgNumber.focus();
            event.preventDefault();
        }

        // check if not digit //
        // ------------------ //
        else if (!pgNumberValue.match(/^\d+$/)) {
            $("#lbl_Rep_PG").text(messages.add_pool_lbl_pg_number_error);
            pgNumber.closest('.form-group').addClass('has-error');
            pgNumber.focus();
            event.preventDefault();
        }

        // check if digit is less than 0 or greater than 65,536 //
        // ---------------------------------------------------- //
        else if (pgNumberValue > 65536) {
            $("#lbl_Rep_PG").text(messages.add_pool_lbl_pg_number_error);
            pgNumber.closest('.form-group').addClass('has-error');
            pgNumber.focus();
            event.preventDefault();
        }

        else {
            pgNumber.closest('.form-group').removeClass('has-error');
            $("#lbl_Rep_PG").html("Number of PGs:" + "<font color='red'>*</font>");
        }


        // ====================================
        // Validation of Replica Minimum Size :
        // ====================================
        var replicaMinSize = $("#rep_replica_min_size");
        var replicaMinValue = $("#rep_replica_min_size").val();
        var replicaSizeValue = $("#rep_replica_size").val();

        if (replicaMinValue > replicaSizeValue) {
            $("#lbl_Rep_MinRep").text(messages.add_pool_lbl_min_replica_size_error);
            replicaMinSize.closest('.form-group').addClass('has-error');
            replicaMinSize.focus();
            event.preventDefault();
        }

        else {
            replicaMinSize.closest('.form-group').removeClass('has-error');
            $("#lbl_Rep_MinRep").html("Min Size:" + "<font color='red'>*</font>");
        }


        // =========================
        // Validation of Rule Name :
        // =========================
        var ruleName = $("#rep_rule_name");
        var ruleNameValue = $("#rep_rule_name").val();

        if (ruleNameValue == " ") {
            $("#lbl_Rep_RuleName").text(messages.add_pool_lbl_rule_name_empty);
            ruleName.closest('.form-group').addClass('has-error');
            ruleName.focus();
            event.preventDefault();
        }

        else {
            ruleName.closest('.form-group').removeClass('has-error');
            $("#lbl_Rep_RuleName").html("Rule Name:" + "<font color='red'>*</font>");
        }
    }

    // *****************************************************************************************************************
    // *****************************************************************************************************************
    //                                          Second : "EC Pool Div" Validation :
    // *****************************************************************************************************************
    // *****************************************************************************************************************

    else if (selected_pool == "erasure") {

        // ===============================
        // Validation of EC Profile Name :
        // ===============================
        var ec_profileName = $("#ec_profile");
        var ec_profileNameValue = $("#ec_profile").val();

        if (ec_profileNameValue == " ") {
            $("#lbl_EC_Profile").text(messages.add_ec_pool_lbl_profile_name_empty);
            ec_profileName.closest('.form-group').addClass('has-error');
            ec_profileName.focus();
            event.preventDefault();
        }

        else {
            ec_profileName.closest('.form-group').removeClass('has-error');
            $("#lbl_EC_Profile").html("EC Profile:" + "<font color='red'>*</font>");
        }

        // =========================
        // Validation of No of PGs :
        // =========================
        var ec_pgNumber = $("#ec_pg_num");
        var ec_pgNumberValue = $("#ec_pg_num").val();

        // check if empty //
        // -------------- //

        if (!ec_pgNumberValue) {
            $("#lbl_EC_PG").text(messages.add_pool_lbl_pg_empty);
            ec_pgNumber.closest('.form-group').addClass('has-error');
            ec_pgNumber.focus();
            event.preventDefault();
        }

        // check if has space //
        // ------------------ //
        else if (ec_pgNumberValue.indexOf(" ") != -1) {
            $("#lbl_EC_PG").text(messages.add_pool_lbl_pg_has_space_error);
            ec_pgNumber.closest('.form-group').addClass('has-error');
            ec_pgNumber.focus();
            event.preventDefault();
        }

        // check if not digit //
        // ------------------ //
        else if (!ec_pgNumberValue.match(/^\d+$/)) {
            $("#lbl_EC_PG").text(messages.add_pool_lbl_pg_number_error);
            ec_pgNumber.closest('.form-group').addClass('has-error');
            ec_pgNumber.focus();
            event.preventDefault();
        }

        // check if digit is less than 0 or greater than 65,536 //
        // ---------------------------------------------------- //
        else if (ec_pgNumberValue > 65536) {
            $("#lbl_EC_PG").text(messages.add_pool_lbl_pg_number_error);
            ec_pgNumber.closest('.form-group').addClass('has-error');
            ec_pgNumber.focus();
            event.preventDefault();
        }

        else {
            ec_pgNumber.closest('.form-group').removeClass('has-error');
            $("#lbl_EC_PG").html("Number of PGs:" + "<font color='red'>*</font>");
        }

        // ============================================================
        // Validation of Min Size : must be ( >= K ) and ( <= K + M ) :
        // ============================================================

        var ec_KNumberValue = $("#ec_K").val();
        ec_KNumberValue = parseInt(ec_KNumberValue);              // numeric value of : k

        var ec_MNumberValue = $("#ec_M").val();
        ec_MNumberValue = parseInt(ec_MNumberValue);              // numeric value of : m

        var ec_MinNumber = $("#ec_min_size");

        var ec_MinNumberValue = $("#ec_min_size").val();
        ec_MinNumberValue = parseInt(ec_MinNumberValue);          // numeric value of : Min Size

        var ec_SizeValue = ec_KNumberValue + ec_MNumberValue ;    // numeric value of : k+m

        // check if empty //
        // -------------- //

        if (!ec_MinNumberValue) {
            $("#lbl_EC_MinSize").text(messages.add_ec_pool_lbl_MinSize_empty);
            ec_MinNumber.closest('.form-group').addClass('has-error');
            ec_MinNumber.focus();
            event.preventDefault();
        }

        // check if not digit //
        // ------------------ //
        else if (isNaN(ec_MinNumberValue)) {
            $("#lbl_EC_MinSize").text(messages.add_ec_pool_lbl_MinSize_number_error);
            ec_MinNumber.closest('.form-group').addClass('has-error');
            ec_MinNumber.focus();
            event.preventDefault();
        }

        // check if digit is less than k or greater than k+m //
        // ------------------------------------------------- //
        else if (ec_MinNumberValue < ec_KNumberValue || ec_MinNumberValue > ec_SizeValue) {

            $("#lbl_EC_MinSize").text(messages.add_ec_pool_lbl_MinSize_number_error);
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
        var ec_ruleNameValue = $("#ec_rule_name").val();

        var sum = selected_K_value + selected_M_value;

        if (ec_ruleNameValue == " ") {
            $("#lbl_EC_RuleName").text(messages.add_ec_pool_lbl_rule_name_empty);
            ec_ruleName.closest('.form-group').addClass('has-error');
            ec_ruleName.focus();
            event.preventDefault();
        }

        // Check if pool was ( Erasure ) : the selected "Rule" Max Size must be greater than or equal to (k+m) :
        // -----------------------------------------------------------------------------------------------------

        else if (selected_Rule_Max_value < sum) {
            $("#lbl_EC_RuleName").text(messages.add_ec_pool_lbl_rule_max_size);
            ec_ruleName.closest('.form-group').addClass('has-error');
            ec_ruleName.focus();
            event.preventDefault();
        }

        // Check if pool was ( Erasure ) : the selected "Rule" Min Size must be less than or equal to (k+m) :
        // --------------------------------------------------------------------------------------------------

        else if (selected_Rule_Min_value > sum) {
            $("#lbl_EC_RuleName").text(messages.add_ec_pool_lbl_rule_min_size);
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


