#! /bin/python

"""Calculate provisioned space"""

import subprocess
import json
import sys
import multiprocessing


def pool_size(ceph_pool):
    command = "rbd du --format json -p " + ceph_pool
    jsonout = json.loads(subprocess.check_output(command.split()))
    return {"total_used_size": jsonout["total_used_size"],
            "total_provisioned_size": jsonout["total_provisioned_size"],
            "pool_name": ceph_pool}


def pool_root_mapping():
    """
    Figure out the root to pool map.

    Returns a dict which maps pool name to their root name.
    """
    # This is rule_id and root_name mapping.
    command = "ceph osd crush dump --format json"
    jsonout = json.loads(subprocess.check_output(command.split()))
    rules = {}

    for rule in jsonout["rules"]:

        crush_rule_id = rule["rule_id"]
        item_name_found = False

        for step in rule["steps"]:
            if "item_name" in step:
                item_name = step["item_name"]
                item_name_found = True
                break

        if not item_name_found:
            raise Exception("item_name not found.")

        rules[crush_rule_id] = item_name

    # This gives pool name to crush_rule_id mapping.
    command = "ceph osd pool ls detail --format json"
    jsonout = json.loads(subprocess.check_output(command.split()))
    pool_root_map = {}
    for item in jsonout:
        root_name = rules[item["crush_rule"]]
        pool_name = item["pool_name"]

        # if root_name in pool_root_map:
        #     pool_root_map[root_name].append(pool_name)
        # else:
        #     pool_root_map[root_name] = [pool_name]
        pool_root_map[pool_name] = root_name

    return pool_root_map


# get pool names
command = "ceph df --format json"
jsonout = json.loads(subprocess.check_output(command.split()))
ceph_pools = [ceph_pool['name']
              for ceph_pool in jsonout["pools"] if "." not in ceph_pool['name']]

p = multiprocessing.Pool(processes=3)
output = p.map(pool_size, ceph_pools)

returnee = {}
pool_root_map = pool_root_mapping()

for item in output:
    root_name = pool_root_map[item["pool_name"]]
    if root_name in returnee:
        returnee[root_name]["total_used_size"] += item["total_used_size"]
        returnee[root_name]["total_provisioned_size"] += item["total_provisioned_size"]
    else:
        returnee[root_name]["total_used_size"] = item["total_used_size"]
        returnee[root_name]["total_provisioned_size"] = item["total_provisioned_size"]

from pprint import pprint
pprint(returnee)
