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


var crush_tree = {};
var min_id = 0;
var node_info = {};
var buckets_types = [];
var nodes_out_of_selections = [];

get_buckets_types();

function get_buckets_types() {
    $.get('/crush/tree/read_buckets_types', function (data, status) {
        buckets_types = JSON.parse(data);
        console.log(buckets_types);
        draw_buckets_tree(buckets_types);
    });
}

function set_cancel_add(path) {
    $("#cancel_btn").click(function () {
        window.location = path;
    });
}

function draw_buckets_tree(buckets_types) {
    console.log(buckets_types)
    $.get('/crush/tree/read/'+buckets_types, function (data, status) {

        crush_tree = JSON.parse(data);
        min_id = crush_tree[crush_tree.length - 1];
        crush_tree.splice(crush_tree.length - 1, crush_tree.length);
        //console.log(crush_tree)


        for (bucket in crush_tree) {
            if (crush_tree[bucket].type == buckets_types[buckets_types.length - 1]) {
                bucket_info = "add_root##" + crush_tree[bucket].hash + "##" + crush_tree[bucket].alg + "##" + crush_tree[bucket].name;
                $("#add_root").attr("name", bucket_info);
                $("#add_root").attr("onclick", "getSelectedNode(name);");

            }
        }


        if (buckets_types.length > 0 && buckets_types != null) {
            $(function () {

                $('#tree1').tree({
                    data: crush_tree,
                    autoOpen: true,
                    dragAndDrop: true,
                    //tabIndex: 0,
                    closedIcon: $('<i class="glyphicon glyphicon-chevron-right"></i>'),
                    openedIcon: $('<i class="glyphicon glyphicon-chevron-down"></i>'),
                    onCreateLi: function (node, $li) {
                        // Append a link to the jqtree-element div.
                        // The link has an url '#node-[id]' and a data property 'node-id'.
                        //if(node.type == buckets_types[0]){
                        //    nodes_out_of_selections.push(node.id);
                        //}

                        add_plus_to_node();

                        function add_plus_to_node() {

                            if (node.type != buckets_types[0] && node.type != buckets_types[1]) {  //no remove node at osd and host type and has no children
                                node_type = node.type;
                                node_hash = node.hash;
                                node_alg = node.alg;
                                node_name = node.name;
                                node_id = node.id;
                                node_children = node.children.length;


                                // new //
                                if (node.type != buckets_types[2] && node.name != "default") {
                                    $li.find('.jqtree-element').append(
                                        '<a type="button" id="delete_node_button" style="margin-left: 4px;z-index: 50;" data-tooltip="Delete Bucket" data-tooltip-position="right" class="pull-right btn btn-danger btn-xs" name=' + node_children + "##" + node_name + "##" + node_id + ' onclick="removeNode(name);"  > <span class="glyphicon glyphicon-remove"></span> </a>'
                                        +
                                        '<a type="button" style="z-index: 50;" data-toggle="modal" data-tooltip="Add Bucket" data-tooltip-position="left" class="pull-right btn btn-primary btn-xs" name=' + node_type + "##" + node_hash + "##" + node_alg + "##" + node_name + "##" + node_id + ' onclick="getSelectedNode(name);" data-target="#modal_add_node" ><span class="glyphicon glyphicon-plus"></span> </a>'
                                    );
                                }
                                else {
                                    if(node.name == "default"){
                                       $li.find('.jqtree-element').append( '<a type="button" style="margin-right: 28px; z-index: 50;" data-toggle="modal" data-tooltip="Add Bucket" data-tooltip-position="left" class="pull-right btn btn-primary btn-xs" name=' + node_type + "##" + node_hash + "##" + node_alg + "##" + node_name + "##" + node_id + ' onclick="getSelectedNode(name);" data-target="#modal_add_node" > <span class="glyphicon glyphicon-plus"></span> </a>')
                                    }else{
                                        $li.find('.jqtree-element').append(
                                        '<a type="button" id="delete_node_button" style="margin-left: 4px; z-index: 50;" data-tooltip="Delete Bucket" data-tooltip-position="right" class="pull-right btn btn-danger btn-xs" name=' + node_children + "##" + node_name + "##" + node_id + ' onclick="removeNode(name);"> <span class="glyphicon glyphicon-remove"></span> </a>'
                                    );
                                    }

                                }
                            }
                        }
                    },
                    onCanMoveTo: function(moved_node , target_node){
                        if( buckets_types.indexOf(target_node.type) > buckets_types.indexOf(moved_node.type)){
                            return true;
                        }else{
                            return false;
                        }

                    },
                    onCanMove: function (node) {  //prevent moving osd type node
                        if (node.type == buckets_types[0]) {
                            return false;
                        }
                        else {
                            return true;
                        }
                    }
                });

            });
        }
    });
}


//
//remove_osds_from_multiple_selection();
//
//
//function remove_osds_from_multiple_selection(){
//    for(osd_id in nodes_out_of_selections){
//    var osd = $('#tree1').tree('getNodeById', osd_id);
//    $('#tree1').tree('removeFromSelection', osd);
//}
//}


function getSelectedNode(node_info) {
    $('#node_id').val("");
    $('#name').val("");
    node_info = node_info.split("##");
    type = node_info[0];
    hash = node_info[1];
    alg = node_info[2];
    name = node_info[3];
    node_id = node_info[4];
    $('#hash').val(hash);
    $('#alg').val(alg);
    $('#node_id').val(node_id);
    $('#type').html("");
    if (type == "add_root") {
        $('#parent_lbl').hide();
        $('#parent_value').hide();
        for (i = buckets_types.length - 1; i > 1; i--) {
            $('#type').append('<option value="' + buckets_types[i] + '">' + buckets_types[i] + '</option>');
        }
    } else {
        $('#parent_value').html(name);
        $('#parent_value').show();
        $('#parent_lbl').show();
        type_index = buckets_types.indexOf(type)
        for (i = buckets_types.length - 1; i > 1; i--) {
            if (i < type_index) {
                $('#type').append('<option value="' + buckets_types[i] + '">' + buckets_types[i] + '</option>');
            }
        }

    }

}

function addNode(event) {
    var id = $('#node_id').val();
    console.log(id);
    var name = $("#name");
    var NameValue = $("#name").val();

    if(NameValue.indexOf(' ') >= 0){
        $("#name_lbl").text(messages.add_lbl_bucket_name_space);
        name.closest('.form-group').addClass('has-error');
        name.focus();
        event.preventDefault();
    }

    if (!NameValue) {
        $("#name_lbl").text(messages.add_lbl_bucket_name_empty);
        name.closest('.form-group').addClass('has-error');
        name.focus();
        event.preventDefault();
    }
    var selected_node = $('#tree1').tree('getNodeById', id);
    console.log(selected_node);
    var new_obj = {
        name: $('#name').val(),
        type: $('#type').val(),
        hash: $('#hash').val(),
        alg: $('#alg').val(),
        id: min_id - 1,
        new_bucket: "yes",
        class_ids: {
            ssd: min_id - 2,
            hdd: min_id - 3,
            nvme: min_id - 4
        }

    };

    min_id = new_obj.class_ids.nvme;
    node = $('#tree1').tree(
        'appendNode',
        new_obj,
        selected_node
    );

    $('#modal_add_node').modal('toggle');
    console.log(selected_node);
    $('#node_id').val("");

    $("#name").closest('.form-group').removeClass('has-error');
    $('#name_lbl').text('Name: ');
    $('#name_lbl').append('<font color="red">*</font>');

}


function removeNode(node_info) {
    node_info = node_info.split("##");
    children_count = node_info[0];
    name = node_info[1];
    var id = node_info[2];
    console.log(name);

    if (children_count == 0)
    {
        var result;
        delete_msg = messages.confirm_deleting_bucket;
        delete_msg = delete_msg.replace("$" , name);
        result = confirm(delete_msg);
        if (result)
        {
            var selected_node = $('#tree1').tree('getNodeById', id);
            $('#tree1').tree('removeNode', selected_node);
        }

        else

        {
            return false;
        }
    }

    else

    {
        alert(messages.prevent_delete_bucket);
        return false;
    }

}

function remove_class(){
    $("#name").closest('.form-group').removeClass('has-error');
    $('#name_lbl').text('Name: ');
    $('#name_lbl').append('<font color="red">*</font>');
}




$('#bucket_tree').submit(function (event) {
    var confirm_msg;
    confirm_msg = confirm(messages.confirm_saving_crush_map)
    if(!confirm_msg){
        return false
    }
    //$form = $(this); //wrap this in jQuery
    //alert('the action is: ' + $form.attr('action'));

    var bucket_tree = $('#tree1').tree('toJson');
    $('#bucket').val(bucket_tree);
    console.log($('#bucket').val(bucket_tree) );
});

//onmouseover="$(this).attr(\'title\', \'Delete Bucket\');"
//onmouseover="$(this).attr(\'title\', \'Add Bucket\');"
//onmouseover="$(this).attr('title', 'Add Bucket');"