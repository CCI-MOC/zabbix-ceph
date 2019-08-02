# Ceph Provisioning Caculator

## What's this?

The script `ceph_provisioned.py` calculates how much space is provisioned in ceph
by running `rbd du -p pool-name` for pool names where we have rbd usage.
It will take into account any redundancy overhead so the final results are actual
raw usage on disk. The results are returned per ceph root (not pool).

* The ceph manager module for zabbix does not gather this information.
The script can takehours to calculate if fast-diff is not enable on rbd images.
* Due to the long running time of the script we use ZabbixTrapper items to gather data.

## How do I use it?

* The script `ceph_root_usage/ceph.py` is required for this one to work because that script
is the one that discovers the roots.

* Create a configuration file at `/etc/zabbix-ceph/config.ini` and modify it with your
setup details. See the sample config file provided in this directory.

* Copy the script `ceph_provisioned.py` to whatever location you like on a host
that can run `ceph` commands to query your ceph cluster.

I would recommend `/etc/zabbix-ceph/ceph_provisioned.py`.

* Import the template provided in this repository and apply that to the appropriate host.

* Setup a cron job to run this script daily (recommended).