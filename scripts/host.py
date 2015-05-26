#!/usr/bin/env python
from pyparsing import *
import novaclient.v1_1.client as nvclient
from credentials import get_nova_creds
import os

creds = get_nova_creds()
#print creds
nova = nvclient.Client(**creds)
hypervisors = nova.hypervisors.list()
ip_list = nova.floating_ips.list()
instances = nova.servers.list()
fourhex = Word(hexnums,exact=4)
eighthex = Word(hexnums,exact=8)
twelvehex = Word(hexnums,exact=12)
sid = did = Combine(eighthex + ('-' + fourhex)*3 + '-' + twelvehex)
nodes = []
instance_ip = {}
instance_host = {}
for h in hypervisors:
	nodes.append(h.hypervisor_hostname)
print nodes
for i in ip_list:
        instance_ip[i.instance_id] = i.ip
for instance in instances:
	for i in ip_list:
		if(i.instance_id == instance.id):
			instance_host[instance.id] = [i.ip, instance.__dict__.get('OS-EXT-SRV-ATTR:hypervisor_hostname')]
for key in instance_host:
        print key, ':', instance_host[key]
	sid = key
	print sid
	os.system("nova live-migration $key compute1")
for k in instance_ip:
	print k,':', instance_ip[k]
