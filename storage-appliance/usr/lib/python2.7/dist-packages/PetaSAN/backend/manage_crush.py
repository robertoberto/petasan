'''
 Copyright (C) 2019 Maged Mokhtar <mmokhtar <at> petasan.org>
 Copyright (C) 2019 PetaSAN www.petasan.org


 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Affero General Public License
 as published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU Affero General Public License for more details.
'''


from PetaSAN.core.ceph.api import CephAPI
from flask import json
import os
from PetaSAN.core.config.api import ConfigAPI

class ManageCrush:



    def __init__(self):
        pass



    def get_buckets_tree(self , buckets_types):

        bucket_tree = []
        item_info_list = []
        child_info = {}
        ids_list = []


        # buckets_types = ["osd" , "host" , "chassis" , "rack" , "row" , "pdu" , "pod" , "room" , "datacenter" , "region" , "root"]
        #
        # buckets = [
        # {"id" : -20 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.900" , "osd.1000" , "osd.1010" , "osd.1020" , "osd.500"] , "name" : "Node-07" , "type_id" : 1 , "weight" : 0.109} ,
        # {"id" : -20 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.90" , "osd.100" , "osd.110" , "osd.120" , "osd.600"] , "name" : "Node-06" , "type_id" : 1 , "weight" : 0.109} ,
        # {"id" : -20 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.9" , "osd.10" , "osd.11" , "osd.12" , "osd.700"] , "name" : "Node-05" , "type_id" : 1 , "weight" : 0.109} ,
        # {"id" : -1 ,"class_ids" : { "ssd" : -16 } , "hash" : 0 , "alg" : "straw2"  , "items" : ["rack2"] , "name" : "datacenter1" ,
        #  "type_id" : 8 ,"weight" : 0.109},
        # {"id" : -2 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2"  , "items" : ["rack1"] , "name" : "room1" ,
        #  "type_id" : 7 ,"weight" : 0.109},
        # {"id" : -3 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2"  , "items" : ["Node-03"] , "name" : "rack1" ,
        #  "type_id" : 3 ,"weight" : 0.109},
        # {"id" : -4 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.0" , "osd.1"] , "name" : "Node-03" , "type_id" : 1 , "weight" : 0.109} ,
        # {"id" : -5 , "class_ids" : { "ssd" : -16 }   , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.2" , "osd.3"] , "name" : "Node-01" , "type_id" : 1 , "weight" : 0.109},
        # {"id" : -6 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["datacenter2"] , "name" : "default" ,
        #  "type_id" : 10 ,"weight" : 0.109},
        # {"id" : -7 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["Node-01" , "Node-04"] , "name" : "datacenter2" ,
        #  "type_id" : 8 ,"weight" : 0.109},
        # {"id" : -8 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.4" , "osd.5" , "osd.40" , "osd.50"] , "name" : "Node-02" , "type_id" : 1 , "weight" : 0.109},
        # {"id" : -9 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["osd.6" , "osd.7" , "osd.41" , "osd.51"] , "name" : "Node-04" , "type_id" : 1 , "weight" : 0.109},
        # {"id" : -10 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2"  , "name" : "rack2" ,
        #  "type_id" : 3 ,"weight" : 0.109},
        # {"id" : -11 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2"  , "name" : "default2" ,
        #  "type_id" : 10 ,"weight" : 0.109},
        # {"id" : -12 , "class_ids" : { "ssd" : -16 }  , "hash" : 0 , "alg" : "straw2" , "items" : ["chassis1"] , "name" : "default3" ,
        #  "type_id" : 10 ,"weight" : 0.109},
        # {"id" : -13 , "class_ids" : { "ssd" : -16 } , "hash" : 0 , "alg" : "straw2" , "items" : ["room1"] , "name" : "default4" ,
        #  "type_id" : 10 ,"weight" : 0.109},
        #  {"id" : -14 , "class_ids" : { "ssd" : -16 }   , "hash" : 0 , "alg" : "straw2"  , "items" : ["Node-02" , "Node-05" , "Node-06" ] , "name" : "chassis1" ,
        #  "type_id" : 2 ,"weight" : 0.109},
        # ]


        #buckets_types = CephAPI().get_bucket_types()

        buckets = CephAPI().get_buckets()
        for bucket in buckets:
            if "class_ids" in bucket.keys():
                for class_name , id in bucket["class_ids"].iteritems():
                    ids_list.append(id)





        for i in range(1,len(buckets_types)):
            #  ========================= get hosts first ======================
                if i == 1:
                    for bucket in buckets:
                        if bucket["type_id"] == i:
                            # if host has items
                            if "items" in bucket.keys():
                                for item in bucket["items"]:
                                    if "#" in item:
                                        osd_split = item.split("#")
                                        item_split = osd_split[0]
                                        osd_type = osd_split[1]
                                        id = int(item_split.split(".")[1])
                                        if osd_split[2]:
                                            weight = osd_split[2]
                                            item_info_list.append({"name" : item_split + " ("+osd_type+")" , "type" : buckets_types[0] , "id" : id , "weight" : weight , "osd_type" : osd_type})
                                        else:
                                            item_info_list.append({"name" : item_split + " ("+osd_type+")" , "type" : buckets_types[0] , "id" : id , "osd_type" : osd_type})
                                    else:
                                        item_id = item.split(".")[1]
                                        item_info_list.append({"name" : item , "type" : buckets_types[0] , "id" : item_id})
                                bucket_tree.append({"name" : bucket["name"] , "type" : buckets_types[1] , "class_ids" : bucket["class_ids"] ,"id" : bucket["id"] , "hash" : bucket["hash"] , "alg" : bucket["alg"] , "children" : item_info_list})
                                item_info_list = []

                            # if host has no items
                            else:
                                bucket_tree.append({"name" : bucket["name"] , "type" : buckets_types[1]  , "class_ids" : bucket["class_ids"] ,"id" : bucket["id"] , "hash" : bucket["hash"] , "alg" : bucket["alg"]})

                # =================== get other types from low level to root  ============
                else:
                   parentList = get_buckets_by_type_id(i, buckets)
                   for parentInfo in parentList:
                       # if parent has items
                        if "items" in parentInfo.keys():
                            for child in parentInfo["items"]:
                                child_info = get_child_info(child , bucket_tree)
                                item_info_list.append(child_info)
                                bucket_tree.remove(child_info)
                                child_info = {}

                            bucket_tree.append({"name" : parentInfo["name"] , "type" : buckets_types[i] ,"class_ids" : parentInfo["class_ids"] , "id" : parentInfo["id"], "hash" : parentInfo["hash"] , "alg" : parentInfo["alg"] , "children" : item_info_list})
                            item_info_list = []

                            ids_list.append(parentInfo["id"])
                        # if parent has no items
                        else:
                            bucket_tree.append({"name" : parentInfo["name"] , "type" : buckets_types[i] , "class_ids" : parentInfo["class_ids"] , "id" : parentInfo["id"] , "hash" : parentInfo["hash"] , "alg" : parentInfo["alg"]})
                            ids_list.append(parentInfo["id"])



        min_id = min(ids_list)
        bucket_tree.append(min_id)
        buckets_tree = json.dumps(bucket_tree)
        return buckets_tree


    def get_buckets_types(self):
        ceph_api = CephAPI()
        buckets_type = ceph_api.get_bucket_types()
        return json.dumps(buckets_type)


    def save_buckets_tree(self , buckets):
        ceph_api = CephAPI()
        buckets_types = ceph_api.get_bucket_types()
        buckets_tree = json.loads(buckets)
        crush_map = []
        for bucket_tree in buckets_tree:
            if "children" in bucket_tree.keys():
                get_children_info(bucket_tree , crush_map , buckets_types)
            else:
                crush_map.append({"name" : bucket_tree["name"] , "id" : bucket_tree["id"] , "class_ids" : bucket_tree["class_ids"] ,
                "hash" : bucket_tree["hash"] , "alg" : bucket_tree["alg"] , "type_id" : buckets_types.index(bucket_tree["type"])})

        ceph_api.save_buckets(crush_map)



    def get_rules(self):
        ceph_api = CephAPI()
        rules_info = ceph_api.get_rules()
        return rules_info


    def add_rule(self , name , body):
        ceph_api = CephAPI()
        ceph_api.add_rule(name , body)


    def update_rule(self , name , body):
        ceph_api = CephAPI()
        ceph_api.update_rule(name , body)


    def delete_rule(self , rule_name):
        ceph_api = CephAPI()
        ceph_api.delete_rule(rule_name)


    """
    def get_templates(self):
        templates = {'template1': '{\nid 9\ntype replicated\nmin_size 2\nmax_size 10\nstep take default\nstep choose firstn 0 type osd\nstep emit\n}', 'template2': '{\nid 0\ntype replicated\nmin_size 1\nmax_size 10\nstep take default\nstep choose firstn 0 type osd\nstep emit\n}'}
        return templates
    """

    def get_templates(self):
        templates = {}
        path = ConfigAPI().get_crush_rule_templates_path()
        ceph_api = CephAPI()
        next_id = ceph_api.get_next_rule_id()

        for f in os.listdir(path) :
            if os.path.isdir(path + f) :
                continue

            with open(path + f, 'r') as file:
                lines = file.readlines()

            body = ''
            for line in lines:
                if len(line) == 0:
                    continue
                if line.startswith('id '):
                    body +=  '# Auto generated id. do not modify \n'
                    body += 'id ' + next_id + '\n'
                    continue
                body += line

            templates[f] = body

        return templates



#get children info for each bucket
def get_children_info(bucket_tree , crush_map , buckets_types):
    items = []
    for child in bucket_tree["children"]:
        if child["type"] == buckets_types[0]:
            if "(" in child["name"] and ")" in child["name"]:
                name = child["name"].replace(" (" , "#")
                name = name.replace(")" , "#")
                name = name + child["weight"]
            items.append(name)
        else:
            items.append(child["name"])
        if "children" in child.keys():
            get_children_info(child , crush_map , buckets_types)
        else:
            if child["type"] != buckets_types[0]:
                crush_map.append({"name" : child["name"], "id" : child["id"] , "class_ids" : child["class_ids"] ,
                "hash" : child["hash"] , "alg" : child["alg"] , "type_id" : buckets_types.index(child["type"])})
    crush_map.append({"name" : bucket_tree["name"] , "items" : items , "id" : bucket_tree["id"] , "class_ids" : bucket_tree["class_ids"] ,
                "hash" : bucket_tree["hash"] , "alg" : bucket_tree["alg"] , "type_id" : buckets_types.index(bucket_tree["type"])})




#get the buckets info by it's type id
def get_buckets_by_type_id(typeId, buckets):
    bucketList = []
    for bucket in buckets:
        if bucket["type_id"] == typeId:
            bucketList.append(bucket)
    return bucketList


#get child info for each bucket
def get_child_info(name, tree):
    childInfo = {}
    for row in tree:
        if row["name"] == name:
            childInfo = row
    return childInfo














