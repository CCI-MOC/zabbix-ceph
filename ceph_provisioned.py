#! /bin/python

"""Calculate provisioned space"""

import sys
import subprocess
import json
import multiprocessing
from pprint import pprint


def execute_command(command):
    """Execute `command` and return the json output"""
    command += " --format json"
    return json.loads(subprocess.check_output(command.split()))


def get_pools():
    """Return a list of pool names"""
    jsonout = execute_command("ceph osd lspools")
    return [item["poolname"] for item in jsonout]


def get_pool_size(ceph_pool):
    """Get the size of pool.

    It attempts to first find the size assuming it's a pool used for rbd
    storage. If that returns all zero, then we try to get the size using
    ceph df in case the pool was used for rgw or cephfs.
    """

    jsonout = execute_command("rbd du -p " + ceph_pool)

    total_used_size = jsonout["total_used_size"]
    total_provisioned_size = jsonout["total_provisioned_size"]

    if total_used_size != 0 or total_provisioned_size != 0:
        return {"total_used_size": total_used_size,
                "total_provisioned_size": total_provisioned_size}

    # If the total_used_size and total_provisioned_size are both zero, then
    # there's no rbd usage. Then the pool is being used for rgw or cephfs
    # and in that case the provisioned usage is the same as allocated, and we
    # get those numbers from ceph df.

    jsonout = execute_command("ceph df")
    jsonout = jsonout["pools"]
    for item in jsonout:
        if item["name"] == ceph_pool:
            total_used_size = item["stats"]["bytes_used"]
            total_provisioned_size = item["stats"]["bytes_used"]
            break
    return {"total_used_size": total_used_size,
            "total_provisioned_size": total_provisioned_size}


def get_replication_factor(ceph_pool):
    """Get the replication factor.

    This returns the factor to multiply our pool size with to get the actual
    space used on disk. This factor depends on if the pool is erasure coded
    or simply a replicated pool.
    """

    jsonout = execute_command("ceph osd pool get " + ceph_pool + " all")
    if "erasure_coded_profile" in jsonout:
        ec_profile = jsonout["erasure_coded_profile"]
        jsonout = execute_command("ceph osd erasure-code-profile get " + ec_profile)
        return 1 + jsonout["m"] / jsonout["k"]
    else:
        return jsonout["size"]


def get_pool_root_map():
    """
    Figure out the root to pool map.

    Returns a dict which maps pool name to their root name.

    """
    # This is rule_id and root_name mapping.
    jsonout = execute_command("ceph osd crush dump")
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
    jsonout = execute_command("ceph osd pool ls detail")

    pool_root_map = {}
    for item in jsonout:
        root_name = rules[item["crush_rule"]]
        pool_name = item["pool_name"]
        pool_root_map[pool_name] = root_name

    return pool_root_map


def get_pool_crush_rule_map():
    """Returns the pool names and crush rule being used"""
    command = "ceph osd pool ls detail --format json"
    jsonout = json.loads(subprocess.check_output(command.split()))
    pool_crush_rule_map = []
    for item in jsonout:
        pool_crush_rule_map.append((item["pool_name"], item["crush_rule"]))
    return pool_crush_rule_map


def main():
    """main"""

    pools = get_pools()
    pool_root_map = get_pool_root_map()
    results = []
    for pool in pools:
        d = {}
        d = get_pool_size(pool)
        d["pool_name"] = pool
        d["replication_factor"] = get_replication_factor(pool)
        d["raw_total_used_size"] = d["total_used_size"] * d["replication_factor"]
        d["raw_total_provisioned_size"] = d["total_provisioned_size"] * \
            d["replication_factor"]
        d["pool_root"] = pool_root_map[pool]
        results.append(d)

    print("Results breakdown:")
    pprint(results)

    root_results = {}
    for item in results:
        if item["pool_root"] in root_results:
            root_results[item["pool_root"]]["raw_total_used_size"] += item["raw_total_used_size"]
            root_results[item["pool_root"]]["raw_total_provisioned_size"] += item["raw_total_provisioned_size"]
        else:
            root_results[item["pool_root"]] = {"raw_total_used_size": item["raw_total_used_size"], "raw_total_provisioned_size": item["raw_total_provisioned_size"]}

    print("Results that matter for zabbix")
    pprint(root_results)

if __name__ == "__main__":
    main()

