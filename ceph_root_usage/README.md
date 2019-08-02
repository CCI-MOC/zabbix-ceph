# Ceph Root Usage


## What's this?

The script `ceph.py` discovers what ceph roots are available and returns
raw total capacity and raw usage per root.

## How do I use it?

* Place the script `ceph.py` at `/etc/zabbix-ceph/` (create the directory if it doesn't exist.)

* Copy the `zabbix_ceph.conf` to `/etc/zabbix/zabbix_agentd.conf.d/`.

* Import the template `zabbix_ceph_templates.xml` into zabbix, and apply it host.

* You will need to allow the zabbix user to execute ceph commands.

 Create a file for the zabbix user under `/etc/sudoers.d/`
 Let's call it `zabbix`. Then add this line to the file
 ```
 zabbix ALL=(ALL) NOPASSWD: /usr/bin/ceph
 ```

That's it.
