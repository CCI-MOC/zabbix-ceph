#! /bin/python

"""This script discovers ceph roots and returns usage details per pool"""

import json
import subprocess
import sys
import re

pattern = re.compile(r'(\d*\.?\d*)\s?(B|KiB|MiB|GiB|TiB|PiB)')
size = {"B": 1, "KiB": 2**10, "MiB": 2**20,
        "GiB": 2**30, "TiB": 2**40, "PiB": 2**50}


def get_roots():
    """Return ceph roots"""
    command = "sudo ceph osd df tree"
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    output = filter(lambda item: "root" in item, output.split("\n"))

    roots = {"data": []}
    for item in output:
        temp = item.split()
        rootname = temp[temp.index("root") + 1]
        if get_total(rootname) == 0:
            continue
        roots["data"].append({"{#ROOTNAME}": rootname})
    return roots


def get_usage(root):
    """Returns a list that includes usage information like
    [Total, Used, Available]
    """

    command = "sudo ceph osd df tree"
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = proc.communicate()[0]

    output = filter(lambda item: root in item, output.split("\n"))
    if output == []:
        sys.exit("Ceph root not found")
    assert len(output) == 1, "Provided root matched multiple lines " + root
    usage = pattern.findall(output[0])
    return usage


def get_total(root):
    """Get total size of ceph root in bytes"""
    temp = get_usage(root)[0]
    size_in_bytes = float(temp[0]) * size[temp[1]]
    return long(round(size_in_bytes))


def get_used(root):
    """Returns used byes of ceph root"""
    temp = get_usage(root)[1]
    size_in_bytes = float(temp[0]) * size[temp[1]]
    return long(round(size_in_bytes))


if len(sys.argv) != 3:
    sys.stdout.write(json.dumps(get_roots()))
elif sys.argv[1] == 'total':
    sys.stdout.write(str(get_total(sys.argv[2])))
elif sys.argv[1] == 'used':
    sys.stdout.write(str(get_used(sys.argv[2])))
else:
    get_roots()
