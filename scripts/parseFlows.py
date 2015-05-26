#
# flowParser.py
#
# Copyright 2014, Veena S L
#
# Sample parser to extract MAC addresses and other info from a cli command like: ovs-dpctl dump-flows ovs-system
#in_port(2),eth(src=00:50:56:80:16:0d,dst=33:33:00:01:00:02),eth_type(0x86dd),ipv6(src=fe80::f46b:c6fb:577f:8009,dst=ff02::1:2,label=0,proto=17,tclass=0,hlimit=1,frag=no),udp(src=546,dst=547), packets:0, bytes:0, used:never, actions:1,9
#tunnel(tun_id=0x1,src=193.170.192.143,dst=193.170.192.142,tos=0x0,ttl=64,flags(key)),in_port(6),eth(src=fa:16:3e:5a:ee:d2,dst=fa:16:3e:a7:1c:7f),eth_type(0x0800),ipv4(src=50.50.1.2,dst=61.174.51.209,proto=6,tos=0,ttl=64,frag=no),tcp(src=22,dst=6000), packets:0, bytes:0, used:never, actions:8
#in_port(2),eth(src=00:26:55:e8:b0:43,dst=bc:30:5b:f7:07:fc),eth_type(0x0800),ipv4(src=1.93.24.85,dst=193.170.192.142,proto=6,tos=0,ttl=31,frag=no),tcp(src=44447,dst=22), packets:8, bytes:980, used:4.048s, flags:P., actions:1

from pyparsing import *
import datetime,time
import os
import subprocess
import sched
import novaclient.v1_1.client as nvclient
from credentials import get_nova_creds

scheduler = sched.scheduler(time.time, time.sleep)
creds = get_nova_creds()
nova = nvclient.Client(**creds)
hypervisors = nova.hypervisors.list()
ip_list = nova.floating_ips.list()
instances = nova.servers.list()
nodes = []
instance_ip = {}
instance_host = {}
#sid = did = 0
for h in hypervisors:
        nodes.append(h.hypervisor_hostname)
print nodes
for i in ip_list:
        instance_ip[i.instance_id] = i.ip
for instance in instances:
        for i in ip_list:
                if(i.instance_id == instance.id):
                        instance_host[i.ip] = [instance.id, instance.__dict__.get('OS-EXT-SRV-ATTR:hypervisor_hostname')]

LBRACE,RBRACE,COMMA,EQUAL,COLON,HYPHEN = map(Suppress,'(),=:-')
in_port = packets = proto = tos = ttl = src = dst = op = label = tclass = hlimit = Word(nums)
ipAddress = Combine(Word(nums) + ('.' + Word(nums))*3)
twohex = Word(hexnums,exact=2)
fourhex = Word(hexnums,exact=4)
ipv6Address = Combine(fourhex + (':'+fourhex)*7)
macAddress = Combine(twohex + (':'+twohex)*5)
eth_type = Combine('0x' + Word(hexnums,exact=4))
frag = oneOf("yes no first")
tun_id = Combine('0x' + Word(nums))
flags = oneOf("(key) yes")
flow_pkts = {}
c = d = {}
eighthex = Word(hexnums,exact=8)
twelvehex = Word(hexnums,exact=12)
sid = did = Combine(eighthex + ('-' + fourhex)*3 + '-' + twelvehex) 
eth = Group("eth" + LBRACE +
                "src" + EQUAL + macAddress("src") + COMMA +
                "dst" + EQUAL + macAddress("dst") +
                RBRACE)
arp = Group("arp" + LBRACE +
                "sip" + EQUAL + ipAddress("sip") + COMMA +
                "tip" + EQUAL + ipAddress("tip") + COMMA +
                "op" + EQUAL + op("op") + COMMA +
                "sha" + EQUAL + macAddress("sha") + COMMA +
                "tha" + EQUAL + macAddress("tha") +
                RBRACE)
ipv4 = Group("ipv4" + LBRACE + "src" + EQUAL + ipAddress("src") + COMMA +
                "dst" + EQUAL + ipAddress("dst") + COMMA +
                "proto" + EQUAL + proto("proto") + COMMA +
                "tos" + EQUAL + tos("tos") + COMMA +
                "ttl" + EQUAL + ttl("ttl") + COMMA +
                "frag" + EQUAL + frag("frag") +
                RBRACE)
ipv6 = Group("ipv6" + LBRACE + "src" + EQUAL + ipv6Address("src") + COMMA +
                "dst" + EQUAL + ipv6Address("dst") + COMMA + "label" + EQUAL + label("label") + COMMA +
                "proto" + EQUAL + proto("proto") + COMMA +
                "tclass" + EQUAL + tclass("tclass") + COMMA +
                "hlimit" + EQUAL + ttl("hlimit") + COMMA +
                "frag" + EQUAL + frag("frag") +
                RBRACE)
tcp = Group("tcp" + LBRACE +
                "src" + EQUAL + src("srcPkt") + COMMA +
                "dst" + EQUAL + dst("dstPkt") +
                RBRACE)
udp = Group("tcp" + LBRACE +
                "src" + EQUAL + src("srcPkt") + COMMA +
                "dst" + EQUAL + dst("dstPkt") +
                RBRACE)
#tunnel(tun_id=0x1,src=193.170.192.143,dst=193.170.192.142,tos=0x0,ttl=64,flags(key)),in_port(6),eth(src=fa:16:3e:5a:ee:d2,dst=fa:16:3e:a7:1c:7f),eth_type(0x0800),ipv4(src=50.50.1.2,dst=61.174.51.209,proto=6,tos=0,ttl=64,frag=no),tcp(src=22,dst=6000), packets:0, bytes:0, used:never, actions:8
'''tunnel = Group("tunnel" + LBRACE + "tun_id" + EQUAL + tun_id("tun_id") + COMMA + "src" + EQUAL + ipAddress("src") + COMMA +
                "dst" + EQUAL + ipAddress("dst") + COMMA +
                "tos" + EQUAL + tos("tos") + COMMA +
                "ttl" + EQUAL + ttl("ttl") + COMMA +
                "flags" + EQUAL + flags("flags") +
                RBRACE)
'''
flowStmt = ("in_port" + LBRACE + in_port("in_port") + RBRACE + COMMA +
            eth("eth") + COMMA +
            Optional("eth_type" + LBRACE + eth_type("eth_type") + RBRACE + COMMA ) +
            Optional(arp("arp") + COMMA) +
            Optional(ipv4("ipv4") + COMMA) + Optional(ipv6("ipv6") + COMMA) +
            Optional(tcp("tcp") + COMMA) + Optional(udp("udp") + COMMA) +
            Optional("packets" + COLON + packets("packets")))

def ovsFlows():
	f = os.popen('ovs-dpctl dump-flows ovs-system')
	flows = f.readlines()
	print "Flows are ", flows
	newflows = []
	for line in flows:
		if not line.startswith('tunnel'):
			newflows.append(line)
	for f in newflows:
        	print f
        	flowValues = flowStmt.parseString(f)
        	print flowValues.dump()
        	print "Total packets = ", flowValues.packets
        	print "Source MAC = ", flowValues.eth.src
        	print "Destination MAC = ", flowValues.eth.dst
        	#write an if statement which checks if the flows has ipv4 pattern, if yes-print the below
        	if f.find('ipv4') != -1:
                	print "Source IP = ", flowValues.ipv4.src
                	print "Destination IP = ", flowValues.ipv4.dst
			if (flowValues.ipv4.src, flowValues.ipv4.dst) in flow_pkts.keys():			
				x = int(flow_pkts[(flowValues.ipv4.src, flowValues.ipv4.dst)])
				y = int(flowValues.packets)
				flow_pkts[(flowValues.ipv4.src, flowValues.ipv4.dst)] = x + y
			else:
				flow_pkts[(flowValues.ipv4.src, flowValues.ipv4.dst)] = flowValues.packets
			#print "New dictionary contents"
			#print "Key",' : ',"Value"
			#for x in flow_pkts.keys():print x,' : ',flow_pkts[x]
			#print ""# Print blank line
        	if f.find('ipv6') != -1:
                	print "Source IP = ", flowValues.ipv6
                	print "Destination IP = ", flowValues.ipv6
        	print
	c = flow_pkts
	c = {k:(int(c[k]) + (int(c[(k[1],k[0])]) if (k[1],k[0]) in c else 0)) for k in set(map(lambda x: tuple(sorted(x)),c.keys()))}
	#c = {k:(int(c.get(k,0)) + int(c.get(k[::-1],0))) for k in set(map(lambda x: tuple(sorted(x)),c.keys()))}
	#for x in c.keys():print x,':',c[x]
        for k, v in sorted(c.items(), key=lambda kv: kv[1], reverse=True):
		d[k] = v
        #for x in d.keys():print x,':',d[x]
	
def scheduler_ovsFlows():
	scheduler.enter(0, 1, ovsFlows, ())
	scheduler.run()
	print "***********************************************************************************************************************************"
	time.sleep(10)
	
for i in range(2):
  scheduler_ovsFlows()

for x in d.keys():print x,':',d[x]
for key in instance_host:
        print key, ':', instance_host[key]
	if any(k[0] == key for k in d):
		print key
for k in d:
	#A condition should be added to check number of packets
	#Complete code below should come under the block of that check 
	#if d[k] > 100,000
	print k[0],k[1]
	for key in instance_host:
		if(k[0] == key):
                	print k[0],'=',instance_host[key][1]
                        a = instance_host[key][1]
			sid = instance_host[key][0]
		elif(k[1] == key):
			print k[1], '=',instance_host[key][1]
			b = instance_host[key][1]
			did = instance_host[key][0]
		else:
			a = b = 0
			print "Address not in VM list"
	if (a == b != 0):
		if (a == b):
			print "Don't migrate VMs"
		else:
			print "Migrate",sid,"to", b
			#sid.live_migrate
			subprocess.call(["nova", "live-migration", sid, b])

