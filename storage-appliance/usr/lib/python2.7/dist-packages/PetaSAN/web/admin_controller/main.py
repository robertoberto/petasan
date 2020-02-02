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

import requests
from flask import Blueprint, render_template, request, sessions, session, redirect, Response, stream_with_context

from PetaSAN.backend.cluster_leader import ClusterLeader
from PetaSAN.backend.manage_node import ManageNode
from PetaSAN.core.common.log import logger
from PetaSAN.core.security.basic_auth import requires_auth
from PetaSAN.backend.manage_disk import ManageDisk
from PetaSAN.core.cluster.configuration import *
from PetaSAN.core.cluster.state_util import StateUtil
from PetaSAN.backend.maintenance import ManageMaintenance
from PetaSAN.backend.manage_pools import ManagePools

main_controller = Blueprint('main_controller', __name__)



@main_controller.route('/form', methods=['GET'])
@requires_auth
def form():
    return render_template('admin/form_levels.html')



@main_controller.route('/', methods=['GET', 'POST'])
@requires_auth
def dashboard():
    leader = ClusterLeader().get_leader_node()
    config = configuration()
    management_nodes = config.get_management_nodes_config()
    for node in management_nodes:
        if node.name == leader:
            leader_ip = node.management_ip
            break
        else:
            leader_ip = leader
    port = ":3000"
    url = "http://{}{}/".format(leader_ip,port)
    nodes = ManageNode()
    node_list = nodes.get_node_list()
    # get pool_list
    manage_pool = ManagePools()
    pools_list = manage_pool.get_pools_info()
    pool_names =[]
    for pool in pools_list:
        pool_names.append(pool.name)
    # end get pools
    return render_template('admin/dashboard.html', url=url, node_list=node_list, pools_list=sorted(pool_names))


@main_controller.route('/dashboard', methods=['GET'])
@requires_auth
def get_cluster_status():
    if request.method == 'GET':
        manage_disk = ManageDisk()
        cluster_disk_status = manage_disk.get_cluster_disk_status()
        data = cluster_disk_status
        manage_maintenance = ManageMaintenance()
        mode = manage_maintenance.get_maintenance_mode()
        result = ''
        if data:
            result = data + "##" + str(mode)
        return result


@main_controller.route('/login')
def login():
    return render_template('admin/login.html')


@main_controller.route('/403')
@requires_auth
def page_403():
    return render_template('admin/403.html')


@main_controller.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/login')

# proxy

@main_controller.route('/<path:url>')
@requires_auth
def root(url):
    #logger.info("Root route, path: %s", url)
    # If referred from a proxy request, then redirect to a URL with the proxy prefix.
    # This allows server-relative and protocol-relative URLs to work.
    proxy_ref = proxy_ref_info(request)
    if proxy_ref:
        redirect_url = "/p/%s/%s%s" % (proxy_ref[0], url, ("?" + request.query_string if request.query_string else ""))
        logger.info("Redirecting referred URL to: %s", redirect_url)
        return redirect(redirect_url)
    # Otherwise, default behavior
    return redirect('/login')


@main_controller.route('/p/<path:url>')
@requires_auth
def proxy(url):
    leader = ClusterLeader().get_leader_node()
    #leader = "www.google.com"
    port = ":3000"
    res = Response("Page not found.",mimetype="text/plain")
    res.status_code = 404
    if not leader:
        return res

    if "graph" in url or "graph/" in url :
        url= str(url).replace("graph/","")
        url= str(url).replace("graph","")
    else:
        return res

    url = "http://{}{}/{}".format(leader,port,url)
    proxy_ref = proxy_ref_info(request)
    headers = { "Referer" : "http://%s/%s" % (proxy_ref[0], proxy_ref[1])} if proxy_ref else {}
    # Fetch the URL, and stream it back
    #logger.info("Fetching with headers: %s, %s", url, headers)
    r = requests.get(url, stream=True , params = request.args, headers=headers)

    return Response(stream_with_context(r.iter_content()), content_type = r.headers['content-type'])

def split_url(url):
    """Splits the given URL into a tuple of (protocol, host, uri)"""
    proto, rest = url.split(':', 1)
    rest = rest[2:].split('/', 1)
    host, uri = (rest[0], rest[1]) if len(rest) == 2 else (rest[0], "")
    return (proto, host, uri)


def proxy_ref_info(request):
    """Parses out Referer info indicating the request is from a previously proxied page.

    For example, if:
        Referer: http://localhost:8080/p/google.com/search?q=foo
    then the result is:
        ("google.com", "search?q=foo")
    """
    ref = request.headers.get('referer')
    if ref:
        _, _, uri = split_url(ref)
        if uri.find("/") < 0:
            return None
        first, rest = uri.split("/", 1)
        if first in "pd":
            parts = rest.split("/", 1)
            r = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
            #logger.info("Referred by proxy host, uri: %s, %s", r[0], r[1])
            return r
    return None



@main_controller.route('/state', methods=['GET'])
@requires_auth
def state():
    try:
         StateUtil().collect_local_node_state()
         node_name = configuration().get_node_name()
         collected_path = ConfigAPI().get_collect_state_dir()+node_name+'.tar'
         manage_node = ManageNode()
         return Response(stream_with_context(manage_node.read_file(collected_path)),mimetype="application/x-tar",headers={"Content-Disposition" : "attachment; filename={}".format(node_name+'.tar')})
    except Exception as e:
        logger.exception("error download state file")

@main_controller.route('/state_all', methods=['GET'])
@requires_auth
def state_all():
    try:
        StateUtil().collect_all()
        cluster_name = configuration().get_cluster_name()
        cluster_file = '/opt/petasan/log/'+cluster_name+'.tar'
        manage_node = ManageNode()
        return Response(stream_with_context(manage_node.read_file(cluster_file)),mimetype="application/x-tar",headers={"Content-Disposition" : "attachment; filename={}".format(cluster_name+'.tar')})
    except Exception as e:
        logger.exception("error download state all file")


@main_controller.route('/paths', methods=['GET'])
@requires_auth
def paths():
    return render_template('/admin/paths.html')



@main_controller.route('/tree', methods=['GET'])
@requires_auth
def tree():
    return render_template('/admin/tree.html')






