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

(function ($) {
    var pathsSettings = null;
    var count_check_boxes = 0;

    $.fn.paths = function (options) {
        var defaults = {
            pathsData: null,
            nodeList: null,
            showSelectCol: false,
            ShowStatusCol: false
        };
        var node_list = [];
        pathsSettings = $.extend(defaults, options);

        var pathsData = pathsSettings.pathsData;
        var nodeList = pathsSettings.nodeList;


        ////for each object pathsSettings.nodeList draw the parent container set its id to node_”+node_name
        nodeList.forEach(function (nodeElement) {

            var select = "";
            var status = "";
            var node_table = "";
            var no_paths = "";


            if (pathsSettings.showSelectCol) {
                select = '<th width="5%;"><input type="checkbox" id="select_all_' + nodeElement + '"/></th>';

            }
            else if (pathsSettings.ShowStatusCol) {
                status = '<th width="30%;">Status</th>';

            }


            node_table += '<table style="border-collapse: unset;display: none" class="table table-bordered" id="node_' + nodeElement + '">' + '<thead><tr class="table_head" style="background-color: lightgrey">' + select +
                '<th width="30%;">IP Address</th><th width="30%;">Interface</th><th width="30%;">Disk Name</th>' + status +
                '</tr><thead>';

            var no_Paths = '<label><span id="no_paths_' + nodeElement + '">0</span><span> Paths</span></label>';

            $('#paths_table').append('<div class="panel-group" ><div class=""><h4 class="panel-title"><button class="btn btnpaths" id="button_' + nodeElement + '" style="background-color: white;" data-target="#collapse_' + nodeElement +
                '" onclick="return false">' + '<label>' + nodeElement + '</label></button>' + no_Paths + '</h4></div> <div id="collapse_' + nodeElement + '" class="panel-collapse collapse in" style="margin-left: 5%; width: 40%;">' + node_table + '</div>');

            $("#button_" + nodeElement + "").append('<i class="glyphicon glyphicon-chevron-right" style="padding-left: 10px;"></i>');


            //By default, expanded paths table so arrow down
            $('#button_' + nodeElement + '').find("i").attr("class", "glyphicon glyphicon-chevron-down");

            //arrow right when collapse /arrow down wen expand
            $('#collapse_' + nodeElement + '').on('show.bs.collapse', function () {
                $('#button_' + nodeElement + '').find("i").attr("class", "glyphicon glyphicon-chevron-down");
            })
            $('#collapse_' + nodeElement + '').on('hide.bs.collapse', function () {
                $('#button_' + nodeElement + '').find("i").attr("class", "glyphicon glyphicon-chevron-right");
            })
        });

        pathsData.forEach(function (pathElement0) {

            node_list.push(pathElement0);


        });
        function sorting() {
            node_list.sort(function (a, b) {
                var x = a.ip.toLowerCase();
                var y = b.ip.toLowerCase();
                if (x < y) {
                    return -1;
                }
                if (x > y) {
                    return 1;
                }
                return 0;
            });
        }

        sorting();
        node_list.reverse();

        ////for  each object in pathsData get the node_name property try to get its html control
        //// by its id  “node_”+ node_name then build its children info of path depend on settings ShowStatusCol and showSelectCol

        pathsData.forEach(function (pathElement) {

            pathElement = node_list.pop();
            var nodeTable = $("#" + 'node_' + pathElement.node + "");
            var paths = parseInt($("#no_paths_" + pathElement.node + "").text());

            $("#no_paths_" + pathElement.node + "").text((++paths).toString());
            if (paths == 1) {
                $("#button_" + pathElement.node + "").attr("data-toggle", "collapse");
                nodeTable.show();

            }


            var disk = '<td>' + pathElement.ip + '</td><td>' + pathElement.interface + '</td><td>' + pathElement.disk_name + '</td>';

            var select = "";
            var status = "";


            if (pathsSettings.showSelectCol) {
                select = '<td ><input type="checkbox" class="option_path_' + pathElement.node + '" id="' + pathElement.node + '##' + pathElement.disk_id + '##' + pathElement.ip + '" id="' + pathElement.node + '##' + pathElement.disk_id + '##' + pathElement.ip + '" name="option_path[]" value="' + pathElement.node + '##' + pathElement.disk_name + '##' + pathElement.ip + '##' + pathElement.disk_id + '"/></td>';

            } else if (pathsSettings.ShowStatusCol) {

                switch (pathElement.status) {
                    case 0:
                        status = '<td><span class="badge bg-pending">Moving</span></td>';
                        break;
                    case 1:
                        status = '<td ><span class="badge bg-pending">Pending</span></td>';
                        break;
                    case 2:
                        status = '<td><span class="badge bg-started">Moved</span></td>';
                        break;
                    case 3:
                        status = '<td><span class="badge bg-stop">Failed</span></td>';
                        break;
                    default:
                        status = '<td></td>';
                }

            }


            nodeTable.append('<tr>' + select + disk + status + '</tr>');
        });


        // Select all
        nodeList.forEach(function (nodeElement) {
            $("#select_all_" + nodeElement + "").click(function () {
                $(".option_path_" + nodeElement + "").prop('checked', $(this).prop('checked'));
            });
            $(".option_path" + nodeElement + "").change(function () {
                if (!$(this).prop("checked")) {
                    $("#select_all_" + nodeElement + "").prop("checked", false);
                }
            });
        });


        $.fn.getSelectedPaths = function () {

            var selected_paths = new Array();
            count_check_boxes = 0;
            nodeList.forEach(function (nodeElement) {
                $('.option_path_' + nodeElement + ':checked').each(function (index, element) {
                    selected_paths.push(element.id)
                });

            });
            return selected_paths;

        };


        $.fn.collapseAll = function () {

            $('.panel-collapse').collapse('hide');
        };

        $.fn.expandAll = function () {

            $('.panel-collapse').collapse('show');
        };


    };
    $.fn.clean = function () {
        $('#paths_table').html("");
    };

}(jQuery));
