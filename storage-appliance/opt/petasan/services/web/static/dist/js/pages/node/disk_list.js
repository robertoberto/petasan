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

var journalDiskList = [];
var cacheDiskList = [];
var linked_osds_to_journal = [];
var linked_osds_to_cache = [];
var isGetDiskListRequestFinish = true;

var disksInfo = {};

// ==================================================================================================== //


function get_linked_devices(diskData) {
    var linked_devices = "";
    var caches = "";

    if (diskData.hasOwnProperty('linked_journal'))
    {
        var internal_journal = diskData['linked_journal'].includes(diskData['name']);
        if (diskData['linked_journal'].length > 0 && internal_journal === false) {
            linked_devices = linked_devices + "Journal: " + diskData['linked_journal'] + diskData['linked_journal_part_num'] + "<br>";
        }
    }

    if (diskData.hasOwnProperty('linked_cache'))
    {
        if (diskData['linked_cache'].length > 0)
        {
            if (diskData['linked_cache'].length > 1)
            {
                caches = caches + "Caches: ";
            }
            else
            {
                caches = caches + "Cache: ";
            }

            var last_index = diskData['linked_cache'].length - 1;
            for (var i = 0; i < diskData['linked_cache'].length; i++)
            {
                if (i === last_index)
                {
                    caches = caches + diskData['linked_cache'][i];
                }
                else
                {
                    caches = caches + diskData['linked_cache'][i] + ", ";
                }
            }
        }
    }

    linked_devices = linked_devices + caches;

    return linked_devices;
}

// ################################################################################################################## //
// ################################################################################################################## //

////////////////////////////////////////////
//  Functions of : addStorageDeviceModal  //
////////////////////////////////////////////

function load_add_storage_device_options(disk_name)
{
    // var btn_id = 'add_device_' + disk_name ;
    // var target = $("#" + btn_id).attr('data-target');

    if (node_storage_role === "True")
    {
        $('#addStorageDeviceModal').modal("show");

        // ##################################################################################
        // Fill the 2 Comboboxes "cache_disk_name" & "journal_disk_name"
        // of "add_storage_device" modal from the 2 lists "journalDiskList" & "cacheDiskList"
        // ##################################################################################
        var journal_disk_name_select = document.getElementById('journal_disk_name');
        var cache_disk_name_select = document.getElementById('cache_disk_name');

        // Adding the items of the list "journalDiskList" as options to the select "journal_disk_name" :
        journal_disk_name_select.options.length = 0;
        journal_disk_name_select.options[journal_disk_name_select.options.length] = new Option("Auto", "auto");
        journalDiskList.forEach(function (element) {
            journal_disk_name_select.options[journal_disk_name_select.options.length] = new Option(element, element);
        });

        // Adding the items of the list "cacheDiskList" as options to the select "cache_disk_name" :
        cache_disk_name_select.options.length = 0;
        cache_disk_name_select.options[cache_disk_name_select.options.length] = new Option("Auto", "auto");
        cacheDiskList.forEach(function (element) {
            cache_disk_name_select.options[cache_disk_name_select.options.length] = new Option(element, element);
        });
        // ##################################################################################

        //$('#storageDeviceOptionsArea').hide();
        //$('#add_img').show();

        // Show the name of the selected disk :
        // ====================================
        document.getElementById('physical_disk').value = disk_name ;

        // Reset all options :
        // ===================
        document.getElementById('add_as').value = 'osd';
        document.getElementById('external_journal').value = 'disabled';
        document.getElementById('journal_disk_name').value = 'auto';
        document.getElementById('external_cache').value = 'disabled';
        document.getElementById('cache_disk_name').value = 'auto';
        document.getElementById('partitions').value = '1';

        if (document.getElementById('add_as').value === "osd") {
            $('#external_journal_disk_div').show();
            $('#external_cache_disk_div').show();
            $('#partitions_div').hide();
        }

        if (document.getElementById('external_journal').value === "disabled") {
            $('#journal_disk_lbl').hide();
            $('#journal_disk_name').hide();
        }

        if (document.getElementById('external_cache').value === "disabled") {
            $('#cache_disk_lbl').hide();
            $('#cache_disk_name').hide();
        }

        $('#add_img').hide();
        $('#storageDeviceOptionsArea').show();
    }
    else
    {
        alert(node_storage_message);
        $('#addStorageDeviceModal').modal("hide");
    }
}


function viewDiskOption(sel)
{
    var sel_value = sel.value;

    if (sel_value === "journal") {
        $('#external_journal_disk_div').hide();
        $('#external_cache_disk_div').hide();
        $('#partitions_div').hide();
    }
    else if (sel_value === "cache") {
        $('#external_journal_disk_div').hide();
        $('#external_cache_disk_div').hide();
        $('#partitions_div').show();
    }
    else if (sel_value === "osd") {
        $('#external_journal_disk_div').show();
        $('#external_cache_disk_div').show();
        $('#partitions_div').hide();
    }
}


function showJournalDisks(sel)
{
    var sel_value = sel.value;

    if (sel_value === "disabled") {
        $('#journal_disk_lbl').hide();
        $('#journal_disk_name').hide();
    }
    else if (sel_value === "enabled") {
        $('#journal_disk_lbl').show();
        $('#journal_disk_name').show();
    }
}


function showCacheDisks(sel)
{
    var sel_value = sel.value;

    if (sel_value === "disabled") {
        $('#cache_disk_lbl').hide();
        $('#cache_disk_name').hide();
    }
    else if (sel_value === "writecache") {
        $('#cache_disk_lbl').show();
        $('#cache_disk_name').show();
    }
}


function setFormAction()
{
    var sel_value = document.getElementById("add_as").value ;
    // alert("You select : " + sel_value);

    var sel_disk_name = document.getElementById('physical_disk').value ;

    if (sel_value === "journal")
    {
        var checkJournal = doAddJournal(sel_disk_name) ;
        if (checkJournal === true)
        {
            var url_add_journal_action_final = (url_add_journal_action.slice(0, -1)) + '/' + sel_disk_name ;
            document.getElementById("add_storage_device_form").action = url_add_journal_action_final ;

            // Hide the modal --> addStorageDeviceModal //
            //$('#addStorageDeviceModal').css("display", "none");
            $('#addStorageDeviceModal').removeClass("in");

            return true ;
        }
        else
        {
            return false ;
        }
    }
    else if (sel_value === "cache")
    {
        var checkCache = doAddCache(sel_disk_name) ;
        if (checkCache === true)
        {
            var url_add_cache_action_final = (url_add_cache_action.slice(0, -1)) + '/' + sel_disk_name ;
            document.getElementById("add_storage_device_form").action = url_add_cache_action_final;

            // Hide the modal --> addStorageDeviceModal //
            $('#addStorageDeviceModal').removeClass("in");

            return true ;
        }
        else
        {
            return false ;
        }
    }
    else if (sel_value === "osd")
    {
        // If there is no available cache disk :
        if(document.getElementById('external_cache').value === "writecache" && document.getElementById('cache_disk_name').value === 'auto' && cacheDiskList.length === 0)
        {
            alert(no_available_cache_disk);
            return false;
        }
        // --------------------------------------------------
        // If there is no available journal disk :
        if(document.getElementById('external_journal').value === "enabled" && document.getElementById('journal_disk_name').value === 'auto' && journalDiskList.length === 0)
        {
            alert(no_available_journal_disk);
            return false;
        }
        // --------------------------------------------------
        // If adding OSD with Journal & Cache :
        if(document.getElementById('external_journal').value === "enabled" && document.getElementById('external_cache').value === "writecache")
        {
            var checkOSDJournalCache = doAddOsdJournalCache(sel_disk_name) ;
            if (checkOSDJournalCache === true)
            {
                var url_add_with_journal_cache_action_final = (url_add_with_journal_cache_action.slice(0, -1)) + '/' + sel_disk_name ;
                document.getElementById("add_storage_device_form").action = url_add_with_journal_cache_action_final ;

                // Hide the modal --> addStorageDeviceModal //
                $('#addStorageDeviceModal').removeClass("in");

                return true ;
            }
            else
            {
                return false ;
            }
        }
        // --------------------------------------------------
        // If adding OSD with Journal :
        if(document.getElementById('external_journal').value === "enabled" && document.getElementById('external_cache').value === "disabled")
        {
            var checkOSDJournal = doAddOsdJournal(sel_disk_name) ;
            if (checkOSDJournal === true)
            {
                var url_add_with_journal_action_final = (url_add_with_journal_action.slice(0, -1)) + '/' + sel_disk_name ;
                document.getElementById("add_storage_device_form").action = url_add_with_journal_action_final ;

                // Hide the modal --> addStorageDeviceModal //
                $('#addStorageDeviceModal').removeClass("in");

                return true ;
            }
            else
            {
                return false ;
            }
        }
        // --------------------------------------------------
        // If adding OSD with Cache :
        if(document.getElementById('external_journal').value === "disabled" && document.getElementById('external_cache').value === "writecache")
        {
            var checkOSDCache = doAddOsdCache(sel_disk_name) ;
            if (checkOSDCache === true)
            {
                var url_add_with_cache_action_final = (url_add_with_cache_action.slice(0, -1)) + '/' + sel_disk_name ;
                document.getElementById("add_storage_device_form").action = url_add_with_cache_action_final ;

                // Hide the modal --> addStorageDeviceModal //
                $('#addStorageDeviceModal').removeClass("in");

                return true ;
            }
            else
            {
                return false ;
            }
        }
        // --------------------------------------------------
        // If adding pure OSD :
        if(document.getElementById('external_journal').value === "disabled" && document.getElementById('external_cache').value === "disabled")
        {
            var checkOSD = doAdd(sel_disk_name) ;
            if (checkOSD === true)
            {
                var url_add_action_final = (url_add_action.slice(0, -1)) + '/' + sel_disk_name ;
                document.getElementById("add_storage_device_form").action = url_add_action_final ;

                // Hide the modal --> addStorageDeviceModal //
                $('#addStorageDeviceModal').removeClass("in");

                return true ;
            }
            else
            {
                return false ;
            }
        }
    }
}

// ################################################################################################################## //
// ################################################################################################################## //

// sleep function created by Ahmed Roshdy
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ################################################################################################################## //
// ################################################################################################################## //

function viewDiskInfo(disk_name)
{
    $('#linked_devices').hide();

    $('#linked_osds').hide();

    $('#avail_partitions').hide();

    $('#status').hide();


    $('#diskInfoArea').hide();
    $('#img_for_details').show();

    $('#name_val').html("");
    $('#size_val').html("");
    $('#ssd_val').html("");
    $('#model_val').html("");
    $('#vendor_val').html("");
    $('#type_val').html("");
    $('#serial_val').html("");
    $('#smart_test_val').html("");
    $('#used_val').html("");
    $('#status_val').html("");
    $('#linked_devices_val').html("");
    $('#linked_osds_val').html("");
    $('#avail_partitions_val').html("");
    $('#partition_title').html("");

    if (disksInfo.hasOwnProperty(disk_name))
    {
        var linked_devices = "";
        var linked_osds = "";

        $('#name_val').html(disk_name);
        $('#size_val').html(disksInfo[disk_name]["size"]);

        if (disksInfo[disk_name]['is_ssd'] == 1)
        {
            $('#ssd_val').html("Yes");
        }
        else
        {
            $('#ssd_val').html("No");
        }

        $('#model_val').html(disksInfo[disk_name]["model"]);
        $('#vendor_val').html(disksInfo[disk_name]["vendor"]);

        $('#type_val').html(disksInfo[disk_name]["type"]);
        $('#serial_val').html(disksInfo[disk_name]["serial"]);
        $('#smart_test_val').html(disksInfo[disk_name]["smart_test"]);


        var diskUsed = "";
        if (disksInfo[disk_name]['usage'] === 0)
        {
            diskUsed = "OSD" + disksInfo[disk_name]['osd_id'];
            linked_devices = get_linked_devices(disksInfo[disk_name]);

            if (linked_devices.length > 0 && linked_devices != ""){
                $('#linked_devices').show();
            }


            $('#status').show();

        }
        else if (disksInfo[disk_name]['usage'] === 1)
        {
            diskUsed = "System";

        }
        else if (disksInfo[disk_name]['usage'] === 2)
        {
            diskUsed = "Mounted";
        }
        else if (disksInfo[disk_name]['usage'] === 3)
        {
            diskUsed = "Journal";
            $('#partition_title').html("(Journal Partition:OSD Disk)");
        }
        else if (disksInfo[disk_name]['usage'] === 4)
        {
            diskUsed = "Cache";
            $('#partition_title').html("(Cache Partition:OSD Disk)");
            $('#avail_partitions').show();
            var avail_partitions = disksInfo[disk_name]['no_available_partitions'] + "/" + disksInfo[disk_name]['no_of_partitions'];
            $('#avail_partitions_val').html(avail_partitions);
        }
        else if (disksInfo[disk_name]['usage'] === -1)
        {
            diskUsed = "None";
        }

        if (disksInfo[disk_name]['usage'] === 3 || disksInfo[disk_name]['usage'] === 4)
        {

            if (disksInfo[disk_name]['linked_osds'].length > 0)
            {
                $('#linked_osds').show();
                var osd;
                var cache;
                var linked_osds_arr = [];

                for (osd of disksInfo[disk_name]['linked_osds']){
                    if (disksInfo[disk_name]['usage'] === 4){
                        for (cache of disksInfo[osd]['linked_cache']){
                            if (cache.includes(disk_name)){
                                var cache_partition = cache;
                                partition_num = cache_partition.replace(disk_name, "");
                                linked_osds_arr.push(partition_num + ":" + osd)
                            }
                        }
                    } else if (disksInfo[disk_name]['usage'] === 3){
                        linked_osds_arr.push(disksInfo[osd]['linked_journal_part_num'] + ":" + osd)
                    }

                }
                linked_osds_arr.sort();

                for (var i = 0; i < linked_osds_arr.length; i++){
                   if (i == 3 && i < linked_osds_arr.length - 1){
                        linked_osds += linked_osds_arr[i] + ", " + "<br>";
                    }else {
                        linked_osds += linked_osds_arr[i] + ", ";
                    }

                }

                if (linked_osds[linked_osds.length - 2] == ","){
                    linked_osds = linked_osds.slice(0, -2);
                }

            }
        }

        $('#used_val').html(diskUsed);

        if (disksInfo[disk_name]['status'] === 0)
        {
            diskStatus = "<span  class='badge bg-stop'>Down</span>";
        }
        else if (disksInfo[disk_name]['status'] === 1)
        {
            diskStatus = "<span class='badge bg-started'>Up</span>";
        }
        else if (disksInfo[disk_name]['status'] === 2)
        {
            diskStatus = " <span class='badge bg-pending'>Adding</span>";
        }
        else if (disksInfo[disk_name]['status'] === 4)
        {
            diskStatus = " <span class='badge bg-pending'>Adding</span>";
        }
        else if (disksInfo[disk_name]['status'] === 5)
        {
            diskStatus = " <span class='badge bg-pending'>Adding</span>";
        }
        else if (disksInfo[disk_name]['status'] === 3)
        {
            diskStatus = " <span class='badge bg-pending'>Deleting</span>";
        }
        else if (disksInfo[disk_name]['status'] === -1)
        {
            diskStatus = "";
        }

        $('#status_val').html(diskStatus);

        $('#linked_devices_val').html(linked_devices);

        $('#linked_osds_val').html(linked_osds);


        $('#img_for_details').hide();
        $('#diskInfoArea').show();

    }

    else
    {
        // type wait for one second and call function again
        sleep(1000).then(() => {
            viewDiskInfo(disk_name);
        });
    }
}

// ==================================================================================================== //
function bindTable() {
    $('#diskBody').empty();
}

// ==================================================================================================== //
function drawRows(diskData) {
    if (diskData['error_message'] !== "" || diskData['error_message'].length > 0)
    {
        $('#error').show();
        $('#errText').text(diskData['error_message']);
        process_id = 0;
    }

    var diskSSD = 0;
    var diskUsed = 0;
    var diskStatus = 0;
    var journalName = "";
    var cacheName = "";

    if (diskData['is_ssd'] == 1)
    {
        diskSSD = "Yes";
    }
    else
    {
        diskSSD = "No";
    }

    if (diskData['usage'] === 0)
    {
        diskUsed = "OSD" + diskData['osd_id'];
        if(diskData.hasOwnProperty('linked_journal'))
        {
            journalName = diskData['linked_journal'];
        }
        else if(diskData.hasOwnProperty('linked_cache'))
        {
            cacheName = diskData['linked_cache'];
        }
    }
    else if (diskData['usage'] === 1)
    {
        diskUsed = "System";
    }
    else if (diskData['usage'] === 2)
    {
        diskUsed = "Mounted";
    }
    else if (diskData['usage'] === 3)
    {
        diskUsed = "Journal";
        $('#journal_disk').append('<option value="' + diskData['name'] + '">' + diskData['name'] + '</option>');
        linked_osds_to_journal = [];

        for(var i = 0; i <  diskData['linked_osds'].length; i++){
             linked_osds_to_journal.push(diskData['linked_osds'][i]);
        }
    }
    else if (diskData['usage'] === 4)
    {
        diskUsed = "Cache";
        //$('#cache_disk').append('<option value="' + diskData['name'] + '">' + diskData['name'] + '</option>');
        linked_osds_to_cache = [];

        for(var i = 0; i <  diskData['linked_osds'].length; i++)
        {
             linked_osds_to_cache.push(diskData['linked_osds'][i]);
        }
    }
    else if (diskData['usage'] === -1)
    {
        diskUsed = "None";
    }

    if (diskData['status'] === 0)
    {
        diskStatus = "<span  class='badge bg-stop'>Down</span>";
    }
    else if (diskData['status'] === 1)
    {
        diskStatus = "<span class='badge bg-started'>Up</span>";
    }
    else if (diskData['status'] === 2)
    {
        isProcessing = true;
        diskStatus = " <span class='badge bg-pending'>Adding</span>";
    }
    else if (diskData['status'] === 4)
    {
        isProcessing = true;
        diskStatus = " <span class='badge bg-pending'>Adding</span>";
    }
    else if (diskData['status'] === 5)
    {
        isProcessing = true;
        diskStatus = " <span class='badge bg-pending'>Adding</span>";
    }
    else if (diskData['status'] === 3)
    {
        isProcessing = true;
        diskStatus = " <span class='badge bg-pending'>Deleting</span>";
    }
    else if (diskData['status'] === -1)
    {
        diskStatus = "";
    }

    var linked_devices = "";

    if (diskData['usage'] === 0)
    {
        linked_devices = get_linked_devices(diskData);
    }

    // Draw the Row in Data Table //
    // ========================== //
    var disk_row = data_table.row.add([diskData['name'], diskData['size'], diskSSD, diskData['serial'], diskData['smart_test'], diskUsed, diskStatus, linked_devices,  drawActions(diskData['usage'], diskData['status'], diskData['osd_id'], diskData['name'])]).draw().node();

    // This part is responsible for displaying each row in table as a link for disk info //
    // ================================================================================= //
    for (var x = 0; x < number_of_clickable_cols; x++)
    {
        //$(disk_row).find('td').eq(x).addClass(diskData['name'] + x);
        var data = $(disk_row).find('td').eq(x).html();
        $(disk_row).find('td').eq(x).html("<a href='' ></a>");
        diskName = diskData['name'];

        var new_data = "<a href='#' class='clickabe' style='display: block; width: 100%; height: 100%; text-decoration: none;" +
            "color: #000000;'  " +
            "data-toggle='modal' data-target='#viewDiskDetails' onclick=\"return viewDiskInfo('" + diskName + "');\" >" + data + "</a>";
        $(disk_row).find('td').eq(x).html(new_data);
    }

    if (isProcessing === false)
    {
        process_id = 0;
    }
}

// ==================================================================================================== //
function drawActions(disk_Used, disk_Status, disk_osd_id, disk_name)
{
    if (disk_name === "")
    {
        disk_name = "not_set";
    }

    var action = "";
    //var actionAddJournal = "";

    if ((disk_Used === -1 || disk_Used === 2) && disk_Status === -1) { //in case: disk not use, not mounted, and no status
        //add_journal default case
        //var url_add_journal_action_final = (url_add_journal_action.slice(0, -1)) + '/' + disk_name;
        //actionAddJournal = "<div title='Add journal' class='btn-group'> <form action=" + url_add_journal_action_final + " method='post'> <button type='submit' onclick=\"return doAddJournal('" + disk_name + "');\" id='add_journal' class='btn btn-default'> <i class='fa fa-plus'></i> J </button> </form> </div>";
        //

        //action = "<div title='Add Device' class='btn-group'><form method='post'><button type='submit' onclick='addStorageDevice()'  id='add_device' class='btn btn-default'> <i class='fa fa-plus'></i></button></form></div>";

        action = "<div title='Add Device' class='btn-group'><a id='add_device_"+ disk_name +"' href='#' data-target='#addStorageDeviceModal' data-controls-modal='modal-from-dom' data-backdrop='static' onclick=\"load_add_storage_device_options('" + disk_name + "');\" data-keyboard='true' class='btn btn-default'><i class='fa fa-plus'></i></a></div>";

        //if (journalDiskList.length == 0) { //add osd
        //    var url_add_action_final = (url_add_action.slice(0, -1)) + '/' + disk_name;
        //    action = "<div title='Add OSD' class='btn-group'> <form action=" + url_add_action_final + " method='post'> <button type='submit' onclick=\"return doAdd('" + disk_name + "');\" id='add_btn' class='btn btn-default'> <i class='fa fa-plus'></i></button>&nbsp; </form> </div>";
        //}
        //else if (journalDiskList.length > 0) { //add osd_with_journal
        //    var url_add_with_journal_action_final = (url_add_with_journal_action.slice(0, -1)) + '/' + disk_name;
        //    action = "<div title='Add OSD with journal' class='btn-group'>" + "<button type='submit' onclick=\"return addOsdJournalSettings('" + url_add_with_journal_action_final + "','" + disk_name + "',);\" id='add_with_journal' class='btn btn-default' data-toggle='modal' data-target='#myModal'> <i class='fa fa-plus'></i></button>&nbsp;</div>";
        //}
        ////action = action + actionAddJournal;
    }

    if ((disk_Used === 0 && disk_Status === 0) || (disk_Used === 0 && disk_Status === -1))
    {
        var url_delete_action_final = url_delete_action.slice(0, -2) + '/' + disk_name + '/' + disk_osd_id;
        url_delete_action_final = url_delete_action_final.replace("//", "/");
        action += "&nbsp<div title='Delete OSD' class='btn-group'> <form action=" + url_delete_action_final + " method='post'> <button type='submit' onclick=\"return doDelete('" + disk_name + "');\" id='delete_btn' class='btn btn-default'> <i class='fa fa-remove'></i> </button> </form> </div>";
    }
    //in case old journal from previous cluster
    //no osds linked to exist journal it means they are old from previous installation so show delete journal option
    //delete is  the same as add action that node has a storage role

    if (disk_Used === 3 && node_storage_role === "True" && disk_Status !==  3)
    {
        if (linked_osds_to_journal.length === 0) {
            var url_delete_journal_action_final = url_delete_journal_action.slice(0, -1) + '/' + disk_name;
            action += "&nbsp<div title='Delete journal' class='btn-group'> <form action=" + url_delete_journal_action_final + " method='post'> <button type='submit' onclick=\"return doDeleteJournal('" + disk_name + "');\" id='delete_journal' class='btn btn-default'> <i class='fa fa-remove'></i> </button> </form> </div>";
        }
    }

    if (disk_Used === 4 && node_storage_role === "True" && disk_Status !==  3)
    {
        if (linked_osds_to_cache.length === 0) {
            var url_delete_cache_action_final = url_delete_cache_action.slice(0, -1) + '/' + disk_name;
            action += "&nbsp<div title='Delete cache' class='btn-group'> <form action=" + url_delete_cache_action_final + " method='post'> <button type='submit' onclick=\"return doDeleteCache('" + disk_name + "');\" id='delete_cache' class='btn btn-default'> <i class='fa fa-remove'></i> </button> </form> </div>";

        }
    }

    action += "&nbsp<div title='View Disk Info' class='btn-group'> <a href='#' data-toggle='modal' data-target='#viewDiskDetails' onclick=\"return viewDiskInfo('" + disk_name + "');\"  id='view_disk_info' class='btn btn-default'> <i class='fa fa-info'></i> </a> </div>";

    return action;
}

// ==================================================================================================== //
function getDiskList()
{
    isProcessing = false;
    if (isGetDiskListRequestFinish === false){ //for optimization, to prevent request hang and don't make ajax request only if it finished
        return;
    }
    isGetDiskListRequestFinish = false;

    $.ajax({
        url: "/node/list/get_all_disk/" + node_name + "/" + process_id,
        type: "get",
        success: function (disk_ls) {
            if (disk_ls.indexOf('Sign in') !== -1) {
                window.location.href = loginUrl;
            }

            journalDiskList = [];
            cacheDiskList = [];
            data_table.clear().draw();
            $('#journal_disk').empty();
            $('#journal_disk').append('<option value="auto">Auto</option>');
            bindTable();
            $("#size").text("");
            $('#img').hide();
            $('#diskBody').show();
            var diskData = JSON.parse(disk_ls);

            // sloop to check if there is journal before draw rows to solve issue
            // of return before draw all table rows loop of disk list and have no journal
            for (var i = 0; i < diskData.length; i++)
            {
                if (diskData[i]['usage'] === 3) { //disk journal
                    journalDiskList.push(diskData[i]['name']);
                }
                if (diskData[i]['usage'] === 4) { //disk cache
                    cacheDiskList.push(diskData[i]['name']);
                }
                var name = diskData[i]['name'];
                disksInfo[name] = diskData[i];
            }

            for (var i = 0; i < diskData.length; i++)
            {
                drawRows(diskData[i]);
            }

            isGetDiskListRequestFinish = true;
            $("#size").text("Showing 1 to " + diskData.length + " of " + diskData.length + " entries");
        },
        error: function () {
            isGetDiskListRequestFinish = true;

        }
    });
}

// ################################################################################################################## //
// ################################################################################################################## //

var messages = $("#messages").val().split("#");
var node_storage_message = $("#node_storage_role_message").val();
var node_manage_osd_message = $("#node_manage_osd_warning_message").val();
var node_journal_message  = $("#journal_mesg").val().split("#");
// ##########
var no_available_journal_disk = $("#journalDiskListLengthErr").val();
var no_available_cache_disk = $("#cacheDiskListLengthErr").val();

// ################################################################################################################## //
// ################################################################################################################## //

$(document).ready(function () {
    $('#diskBody').hide();
    $('#img').show();
    getDiskList();
    setInterval("getDiskList()", 20000);
});

// ################################################################################################################## //
// ################################################################################################################## //

function doAdd(disk_name)
{
    if (isProcessing === false)
    {
        if (node_storage_role === "True")
        {
            var final_message = messages[0].replace('$', disk_name);
            var confirm_add = confirm(final_message);

            if (confirm_add === true)
            {
                isProcessing = true;
                return true;
            }
            else
            {
                return false;
            }
        }
        else
        {
            alert(node_storage_message);
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

// ==================================================================================================== //
function doAddJournal(disk_name) {//used in html
    if (isProcessing === false)
    {
        if (node_storage_role === "True")
        {
            var final_message = node_journal_message[0].replace('$', disk_name);
            var confirm_add = confirm(final_message);
            if (confirm_add === true)
            {
                isProcessing = true;
                return true;
            }
            else
            {
                return false;
            }
        }
        else
        {
            alert(node_storage_message);
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

// ==================================================================================================== //
function doAddOsdJournal(disk_name)
{
    return doAdd(disk_name);
}

// ==================================================================================================== //
function addOsdJournalSettings(url, disk_name){//used in html
    $("#osd_form").attr("action", url);
    $("#disk_name").val(disk_name);
}

// ==================================================================================================== //
function doDelete(osd_name) {//used in html
    if (isProcessing === false)
    {
        var final_message;
        if (osd_name !== "not_set")
        {
            final_message = messages[1].replace('$', osd_name);
        }
        else
        {
            final_message = messages[1].replace('$', "");
        }

        var confirm_delete = confirm(final_message);
        if (confirm_delete === true)
        {
            isProcessing = true;
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

// ==================================================================================================== //
function doDeleteJournal(disk_name) {//used in html
    if (isProcessing === false)
    {
        var final_message;
        if (disk_name !== "not_set")
        {
            final_message = node_journal_message[1].replace('$', disk_name);
        }
        else
        {
            final_message = node_journal_message[1].replace('$', "");
        }

        var confirm_delete = confirm(final_message);
        if (confirm_delete === true)
        {
            isProcessing = true;
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

function doDeleteCache(disk_name) {//used in html
    if (isProcessing === false)
    {
        var final_message;
        if (disk_name !== "not_set")
        {
            final_message = cache_messages.delete_cache_confirm_mesg.replace('$', disk_name);
        }
        else
        {
            final_message = cache_messages.delete_cache_confirm_mesg.replace('$', "");
        }

        var confirm_delete = confirm(final_message);
        if (confirm_delete === true)
        {
            isProcessing = true;
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

// ==================================================================================================== //
function hide_journal_option (){
    $('#lbl_journal_disk').hide();
    $('#journal_disk').hide();
}

// ==================================================================================================== //
function show_journal_option(){
    $('#lbl_journal_disk').show();
    $('#journal_disk').show();
}

// ==================================================================================================== //
function doAddCache(disk_name)
{
    if (isProcessing === false)
    {
        if (node_storage_role === "True")
        {
            var final_message = cache_messages.add_cache_confirm_mesg.replace('$', disk_name);
            var confirm_add = confirm(final_message);

            if (confirm_add === true)
            {
                isProcessing = true;
                return true;
            }
            else
            {
                return false;
            }
        }
        else
        {
            alert(node_storage_message);
            return false;
        }
    }
    else
    {
        alert(running_job);
        return false;
    }
}

// ==================================================================================================== //
function doAddOsdCache(disk_name)
{
    return doAdd(disk_name);
}

// ==================================================================================================== //
function doAddOsdJournalCache(disk_name)
{
    return doAdd(disk_name);
}

// ################################################################################################################## //
// ################################################################################################################## //

