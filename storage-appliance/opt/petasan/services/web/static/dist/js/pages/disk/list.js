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

var is_finished = true;
var is_finished1 = true;
var is_finished2 = true;
var disk_status_len = 0;
var disk_deleting_id = 0;
var show_modal;
var intervalId;
// delete job //
var delete_job_id;
var local_fsid;

$(document).ready(function () {
    //if ((delete_flag > 0) && (delete_flag != 6) )
    //{
    //    base_url = $("#base_url").val().trim();
    //    indx = base_url.indexOf("list");
    //    base_url = base_url.substring(0, indx + 4);
    //    is_deleting = false;
    //    window.location.href = base_url;
    //}


    // delete disk as a job //
    //delete_job_id = $("#delete_job_id").val().trim();

    //if (delete_job_id > 0) {
    //    var disk_id = $("#disk").val().trim();
    //    loadDiskStatus(disk_id);
    //    setInterval("isDeleteFinished (delete_job_id)", 5000);  // call every 10 seconds
    //    loadDiskStatus(disk_id);
    //}

    // end: delete disk as a job //
});
//////////////////////////////////////////////////////////////////
function loadDiskStatus(disk_id) {

    $("tr.disk").each(function () {

        $this = $(this);
        id = $this.find('.id').text();

        if (id == disk_id && delete_job_id > 0) {

            $('#statusID_' + disk_id).html("<span class='badge bg-pending'>Deleting</span>");
        }

    });

}
/////////////////////////////////////////////////////////
var messages5 = $("#messages5").val();
function doStart(dest_cluster_fsid, disk_name, cluster_fsid) {
    if (cluster_fsid == dest_cluster_fsid) {
        var final_message = messages5.replace('$', disk_name);
        var confirm_var = confirm(final_message);
        if (confirm_var == true) {
            return true;
        } else {
            return false;
        }
    }
}
/////////////////////////////////////////////////////////
function isDeleteFinished(id) {
    if (is_finished2 == false) {
        return
    }
    is_finished2 = false;

    $.ajax({
        url: "/disk/list/get_delete_status/" + id,
        type: "get",
        success: function (data) {
            var deleted_status = JSON.parse(data);
            console.log("====")
            console.log(deleted_status)
            console.log("====")

            if (deleted_status) {

                base_url = $("#base_url").val().trim();

                indx = base_url.indexOf("list");

                base_url = base_url.substring(0, indx + 4);

                $("#delete_job_id").attr("value", 0);

                window.location.href = base_url;

            }
            is_finished2 = true
        }
        ,
        error: function () {
        }
    });
}
/////////////////////////////////////////////////////////
function repeatAjax(disk_url) {

    $('#activePathsTable').empty();

    $.ajax({
        url: disk_url,
        type: "get",
        success: function (data) {
            var id = disk_url.split('/');

            var activePathsData = JSON.parse(data);
            $('#img').hide();
            $('#diskID').show();
            $('#modal').html('Disk ' + id[3]);
            $('#activePathsTable').append('<tr><th>IP</th><th>Interface</th><th style="width: 33%">Assigned Node</th></tr>');
            $('#activePathsTable').show();

            for (var key in activePathsData) {
                keyID = key.split(".").join("_");
                $('#activePathsTable').append('<tr><td  id="key_' + keyID + '">' + key + '</td><td id="key1_' + keyID + '">' + activePathsData[key][1] + '</td><td id="key2_' + keyID + '">' + activePathsData[key][0] + '</td></tr>');
                //$('#IP').html(key);
                //$('#node').html(activePathsData[key]);


            }

        },
        error: function () {

        }

    });
}


function repeatAjax2(disk_url) {

    if (is_finished1 == false) {
        return
    }
    is_finished1 = false;
    $.ajax({
        url: disk_url,
        type: "get",
        success: function (data) {
            show_modal = $("#myModal").hasClass('in');
            //console.log(show_modal);
            if (show_modal == false) {
                clearInterval(intervalId);
            }
            var activePathsData = JSON.parse(data);
            for (var key in activePathsData) {
                keyID = key.split(".").join("_")
                var key0 = "key_" + keyID;
                var key1 = "key1_" + keyID;
                var key2 = "key2_" + keyID;
                $('#' + key0).html(key)
                $('#' + key1).html(activePathsData[key][1])
                $('#' + key2).html(activePathsData[key][0])

            }
            is_finished1 = true
        },
        error: function () {

        }

    });
}


function setDiskUrl(disk_url) {

    disk_url1 = disk_url;

    $('#img').show();
    repeatAjax(disk_url1);
    intervalId = setInterval("repeatAjax2(disk_url1)", 3000);  // call every 3 seconds

}

function manage_status(url_stop, url_start, url_edit, url_remove, url_detach, url_attach) {
    $(document).ready(function () {
        $('#activePathsTable').hide();

        setInterval("ajaxd(url_stop,url_start,url_edit,url_remove,url_detach,url_attach)", 10000); // call every 10 seconds
    });
}

function ajaxd(url_stop, url_start, url_edit, url_remove, url_detach, url_attach) {
    if (is_finished == false) {
        console.log("wait");
        return
    }
    is_finished = false;

    var id, name, status, pool;
    $.ajax({
        url: "/disk/disk_list",
        type: "get",
        success: function (data) {


            if (data.indexOf('Sign in') != -1) {
                window.location.href = loginUrl;
            }
            var diskData = JSON.parse(data);
            if (disk_status_len != 0 && disk_status_len != Object.keys(diskData).length )
            {
                base_url = $("#base_url").val().trim();
                indx = base_url.indexOf("list");
                base_url = base_url.substring(0, indx + 4);
                is_deleting = false;
                window.location.href = base_url;
            }
            disk_status_len = Object.keys(diskData).length;
            if (disk_status_len)
            $("tr.disk").each(function () {
                for (var key in diskData) {
                    $this = $(this);
                    id = $this.find('.id').text();
                    name = $this.find('.name').text();
                    pool = $this.find('.pool').text();
                    status = parseInt($this.find("input.input.status").val());
                    var id_pool = id + "/" + pool;
                    local_fsid = $("#cluster_fsid").val();
                    var dest_fsid = $("#"+id).val();
                    if (key == id && diskData[key] != status) {
                        if (diskData[key] == 1) {
                            var url_action = url_stop + id;

                            $('#statusID_' + id).html(" <span class='badge bg-started'>Started</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                            $('#actionID_' + id).html("<div title='Stop' class='btn-group action_buttons_" + id + "'><form action=" + url_action + " method='post'> " +
                                "<button type='submit'   class='btn btn-default'><i class='fa fa-stop'></i> </button> </form></div>");
                        }
                        else if (diskData[key] == 2) {
                            var url_action_start = url_start + id_pool;
                            url_action_start = url_action_start.replace("//", "/");
                            var url_action_edit = url_edit + id_pool;
                            url_action_edit = url_action_edit.replace("//", "/");
                            var url_action_remove = url_remove + id_pool;
                            url_action_remove = url_action_remove.replace("//", "/");
                            var url_action_detach = url_detach + id_pool;
                            url_action_detach = url_action_detach.replace("//", "/");
                            $('#statusID_' + id).html(" <span class='badge bg-stop'>Stopped</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                            $this.find('.action').css('width', '200px');
                            $('#actionID_' + id).html("<div title='Start' class='btn-group action_buttons_" + id + "' style='padding-right: 4px;'><form action= " + url_action_start + " method='post'> " +
                                "<button type='submit' class='btn btn-default' onclick=\"return doStart('" + dest_fsid + "','" + name + "','" + local_fsid + "');\"><i class='fa fa-play'></i> </button> </form></div>" +
                                "<div title='Edit'class='btn-group action_buttons_" + id + "' style='padding-right: 4px;'><form action=" + url_action_edit + " method='post'> " +
                                "<button type='submit' class='btn btn-default'><i class='fa fa-edit'></i> </button> </form></div>" +
                                "<div title='Delete' class='btn-group action_buttons_" + id + "' style='padding-right: 4px;'><form action=" + url_action_remove + " method='post'> " +
                                "<button type='submit' class='btn btn-default' onclick=\"return doDelete('" + name + "');\"><i class='fa fa-remove'></i> </button> </form></div>" +
                                "<div title='Detach' class='btn-group action_buttons_" + id + "'><form action=" + url_action_detach + " method='post'> " +
                                "<button type='submit' class='btn btn-default'><i class='fa fa-chain-broken'></i> </button> </form></div>");
                        }
                        else if (diskData[key] == 3) {
                            var url_action = url_attach + id_pool;
                            url_action = url_action.replace("//", "/");
                            $('#statusID_' + id).html(" <span class='badge bg-unAttached' style='padding-right: 4px;'>Detached</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                            $('#actionID_' + id).html("<div title='Attach' class='btn-group action_buttons_" + id + "'><form action=" + url_action + " method='post'> " +
                                "<button type='submit'   class='btn btn-default'><i class='fa fa-chain'></i> </button> </form></div>" +
                                "<div title='Delete' class='btn-group action_buttons_" + id + "'><form action=" + url_action_remove + " method='post'> " +
                                "<button type='submit' class='btn btn-default' onclick=\"return doDelete('" + name + "');\"><i class='fa fa-remove'></i> </button> </form></div>");
                        }
                        else if (diskData[key] == 4) {
                            var url_action = url_edit + id;
                            $('.action_buttons_'+ id).hide();
                            $('#statusID_' + id).html(" <span class='badge bg-pending'>Stopping</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                        }
                        else if (diskData[key] == 5) {
                            $('.action_buttons_'+ id).hide();
                            $('#statusID_' + id).html(" <span class='badge bg-pending'>Starting</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                        }
                        else if (diskData[key] == 6) {
                            $('.action_buttons_'+ id).hide();
                            $('#statusID_' + id).html(" <span class='badge bg-pending'>Deleting</span>" +
                                "<input type='hidden' class='status' id='disk_status_" + id + "' value='" + status + "'>");
                        }

                    }
                }
            });
            is_finished = true
        },
        error: function () {

        }
    });
}


// function modal view list

function loadDiskInfo(id, name) {
    $('#auth_yes').hide();
    $('#username').html("");
    $('#iqns_section').hide();
    $('.acls').remove();
    $('.iscsi_1').remove();
    $('#iscsi1').hide();
    $('.iscsi_2').remove();
    $('#iscsi2').hide();
    $('#diskInfoArea').hide();
    $('#img_loading').show();

    $.ajax({
        url: "/disk/list/" + id + "/" + name + "",
        type: "get",
        success: function (data) {
            var disk_info = JSON.parse(data);
            $('#disk_id').html(disk_info.id);
            $('#disk_name').html(disk_info.disk_name);
            if (disk_info.size >= 1024) {
                disk_info.size = (parseInt(disk_info.size) / 1024);
                $('#disk_size').html(disk_info.size + " TB");
            } else {
                $('#disk_size').html(disk_info.size + " GB");
            }
            $('#disk_created').html(disk_info.create_date);
            $('#disk_pool').html(disk_info.pool);
            $('#disk_pool_type').html("Replicated");
            if (disk_info.data_pool != null && disk_info.data_pool.length > 0) {
                if (disk_info.data_pool != 'None') {
                    $('#disk_pool').append(" + " + disk_info.data_pool);
                    $('#disk_pool_type').html("EC");
                }
            }
            $('#disk_iqn').html(disk_info.iqn);
            if (disk_info.user != "" && disk_info.user.length > 0) {
                $('#username').html(disk_info.user);
                $('#password_status').html("Yes");
                $('#auth_yes').show();
            } else {
                $('#password_status').html("No");
            }
            if (disk_info.acl != "" && disk_info.acl.length > 0) {
                disk_acls = disk_info.acl.split(',');
                for (i in disk_acls) {
                    $('#iqns_section').append('<p class="acls">' + disk_acls[i] + '</p>');
                }
                $('#acl_status').html("IQN(s)");
                $('#iqns_section').show();
            } else {
                $('#acl_status').html("All");
            }

            if (disk_info.paths_iscsi_1 != "" && disk_info.paths_iscsi_1.length > 0) {
                for (i in disk_info.paths_iscsi_1) {
                    $('#iscsi1').append('<p class="iscsi_1">' + disk_info.paths_iscsi_1[i] + '</p>')
                }
                $('#iscsi1').show();
            }

            if (disk_info.paths_iscsi_2 != "" && disk_info.paths_iscsi_2.length > 0) {
                for (i in disk_info.paths_iscsi_2) {
                    $('#iscsi2').append('<p class="iscsi_2">' + disk_info.paths_iscsi_2[i] + '</p>')
                }
                $('#iscsi2').show();
            }

            if (disk_info.is_replication_target == true) {
                $('#replica_status').html("Yes");
            } else {
                $('#replica_status').html("No");
            }


            $('#img_loading').hide();
            $('#diskInfoArea').show();
        },

        error: function () {

        }
    });


}


function replication_status(id, pool) {
    var bool = false;
    $.ajax({
        url: "/disk/replication_status/" + id + "/" + pool + "",
        type: "get",
        async: false,
        success: function (data) {
            replication_stat = JSON.parse(data);
            if (replication_stat == true) {
                bool = true;
            }
        },

        error: function () {

        }
    });
    return get_replication_status(bool);
}

function get_replication_status(data) {
    var rep_stat = data;
    return rep_stat;
}






















