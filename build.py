'''
Created on Oct 2, 2013
@author: tkraus
This script will create 3 Internal Logical Switches, 1 VDR, 1 SVC Edge, connect them all and configure OSPF

'''
import base64
import urllib2
import httplib
import xml.etree.ElementTree as ET

global switches 
global vwires
global headers

nsx_ip="192.168.110.72"
nsx_port = 443
username = "admin"
password = "VMware1!"
vdn_scope = 'vdnscope-1'
edge_datastore ='datastore-121'
edge_cluster = 'domain-c26'
vdr_edge_name = 'VDR-01'
vdr_mgmt_pg = 'dvportgroup-38'
internal_ls_names = ['Web-Tier-LS','App-Tier-LS','DB-Tier-LS'] 
transport_ls_name = 'Transport-Network-01' 
tz_name = 'TZ1'
datacenter_id =  'datacenter-21'
svc_edge_name = 'Services_Edge_1'
svc_edge_uplink_dvpg = 'dvportgroup-40'
svc_edge_uplink_int_ip = '192.168.110.240'
svc_edge_uplink_int_mask = '255.255.255.0'
svc_edge_uplink_gw = '192.168.110.2'
svc_edge_router_id = '192.168.10.1'
creds= base64.urlsafe_b64encode(username + ':' + password)
headers = {'Content-Type' : 'application/xml','Authorization' : 'Basic ' + creds }

def create_tz(tz_name):
    url='https://' + nsx_ip + '/api/2.0/vdn/scopes'
    xml_string ='<vdnScope><name>TZ1</name><objectId></objectId><clusters><cluster><cluster><objectId>domain-c26</objectId></cluster></cluster><cluster><cluster><objectId>domain-c25</objectId></cluster></cluster><cluster><cluster><objectId>domain-c27</objectId></cluster></cluster></clusters></vdnScope>'
    req=urllib2.Request(url=url,data=xml_string, headers=headers)
    response=urllib2.urlopen(req)
    tz_id=response.read()
    return tz_id

def create_ls(ls_name):
    url='https://' + nsx_ip + '/api/2.0/vdn/scopes/'+vdn_scope+'/virtualwires'
    xml_string ='<virtualWireCreateSpec><name>' + ls_name + '</name><description>Created via REST API</description><tenantId>virtual wire tenant</tenantId><controlPlaneMode>UNICAST_MODE</controlPlaneMode></virtualWireCreateSpec>'
    req = urllib2.Request(url=url,data=xml_string,headers=headers)
    response=urllib2.urlopen(req)
    vwire_id=response.read()
    return vwire_id

def create_vdr(edge_name):
    xml_string ='<edge><datacenterMoid>' + datacenter_id + '</datacenterMoid><type>distributedRouter</type><appliances><appliance><resourcePoolId>'+edge_cluster+'</resourcePoolId><datastoreId>'+edge_datastore+'</datastoreId><vmHostname>' + edge_name + '</vmHostname></appliance></appliances><mgmtInterface><connectedToId>'+vdr_mgmt_pg+'</connectedToId></mgmtInterface></edge>'
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('POST', 'https://' + nsx_ip + '/api/4.0/edges',xml_string,headers)
    response = conn.getresponse()
    location = response.getheader('location', default=None)
    if response.status != 201:
            print str(response.status) +" VDR Not created..."
            exit(1)
    else:
            location = response.getheader('location', default=None)
            split = location.split('/')
            edge_id = split[-1]
            print "VDR " + str(edge_id)+' Created Successfully'
            return edge_id
        
def create_svc_edge(svc_edge_name,dvpg,int_ip,int_mask,int_type,edge_gw_int):
    xml_string ='<edge><datacenterMoid>'+datacenter_id+'</datacenterMoid><name>'+svc_edge_name+'</name><appliances><appliance><resourcePoolId>'+edge_cluster+'</resourcePoolId><datastoreId>'+edge_datastore+'</datastoreId></appliance></appliances><vnics><vnic><index>'+edge_gw_int+'</index><type>'+int_type+'</type><isConnected>true</isConnected><portgroupId>'+dvpg+'</portgroupId><addressGroups><addressGroup><primaryAddress>'+int_ip+'</primaryAddress><subnetMask>'+int_mask+'</subnetMask></addressGroup></addressGroups></vnic></vnics></edge>'
    # Needed to use httplib to get getheader method bc NSX returning the Edge ID as a URI value in a Response Header. 
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('POST', 'https://' + nsx_ip + '/api/4.0/edges',xml_string,headers)
    response = conn.getresponse()
    location = response.getheader('location', default=None)
    if response.status != 201:
            print str(response.status) + " Services Edge Not created..."
            exit(1)
    else:
            location = response.getheader('location', default=None)
            split = location.split('/')
            svc_edge_id = split[-1]
            print "Services Edge " + str(svc_edge_id)+ " Created Successfully"
            return svc_edge_id

def connect_ls(edge_id,vwire_name,vwire_id,int_ip,int_mask,int_type):
    print str(vwire_id) +' : ' + str(int_ip) + ' : ' + str(int_type)
    url='https://' + nsx_ip + '/api/4.0/edges/' + edge_id + '/interfaces/?action=patch'
    xml_string ='<interfaces><interface><name>' + vwire_name + '</name><addressGroups><addressGroup><primaryAddress>' + int_ip + '</primaryAddress><subnetMask>'+int_mask+'</subnetMask></addressGroup></addressGroups><mtu>1500</mtu><type>' + int_type + '</type><isConnected>true</isConnected><connectedToId>' + vwire_id + '</connectedToId></interface></interfaces>'
    req = urllib2.Request(url=url,data=xml_string,headers=headers)
    response=urllib2.urlopen(req)
   
def connect_svc_ls(edge_id,vwire_name,vwire_id,int_ip,int_mask,int_type,int_index):
    print str(vwire_id) +' : ' + str(int_ip) + ' : ' + str(int_type)
    url='https://' + nsx_ip + '/api/3.0/edges/' + edge_id + '/vnics/?action=patch'
    xml_string ='<vnics><vnic><index>'+ int_index +'</index><name>' + vwire_name + '</name><addressGroups><addressGroup><primaryAddress>' + int_ip + '</primaryAddress><subnetMask>'+int_mask+'</subnetMask></addressGroup></addressGroups><mtu>1500</mtu><type>' + int_type + '</type><isConnected>true</isConnected><portgroupId>' + vwire_id + '</portgroupId></vnic></vnics>'
    req = urllib2.Request(url=url,data=xml_string,headers=headers)
    response=urllib2.urlopen(req)

def config_vdr(vdr_edge_id,gw,router_id,vnic,proto_add,forward_add):
    xml_string = '<routing><routingGlobalConfig><routerId>'+router_id+'</routerId><logging><enable>false</enable><logLevel>info</logLevel></logging></routingGlobalConfig><staticRouting><defaultRoute><description>defaultRoute</description><vnic>'+vnic+'</vnic><gatewayAddress>'+gw+'</gatewayAddress><mtu>1500</mtu></defaultRoute></staticRouting><ospf><enabled>true</enabled><forwardingAddress>'+forward_add+'</forwardingAddress><protocolAddress>' +proto_add+ '</protocolAddress><ospfAreas><ospfArea><areaId>100</areaId><type>normal</type></ospfArea></ospfAreas><ospfInterfaces><ospfInterface><vnic>'+vnic+'</vnic><areaId>100</areaId><helloInterval>10</helloInterval><deadInterval>40</deadInterval><priority>128</priority><cost>10</cost></ospfInterface></ospfInterfaces><redistribution><enabled>true</enabled><rules><rule><from><ospf>true</ospf> <connected>true</connected></from><action>permit</action></rule></rules></redistribution></ospf></routing>'
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('PUT', 'https://' + nsx_ip + '/api/4.0/edges/' + vdr_edge_id+'/routing/config',xml_string,headers)
    response = conn.getresponse()
    if response.status != 204:
            print response.status
            print str(response.status) + " Routing NOT configured on VDR " + str(vdr_edge_id)
            exit(1)
    else:
            print str(response.status) + " Routing configured on VDR " + str(vdr_edge_id)
            return

def config_edge(svc_edge_id,gw,router_id,edge_ospf_int,edge_gw_int):
    xml_string = '<routing><routingGlobalConfig><routerId>'+router_id+'</routerId><logging><enable>false</enable><logLevel>info</logLevel></logging></routingGlobalConfig><staticRouting><defaultRoute><description>defaultRoute</description><vnic>'+edge_gw_int+'</vnic><gatewayAddress>'+gw+'</gatewayAddress><mtu>1500</mtu></defaultRoute></staticRouting><ospf><enabled>true</enabled><ospfAreas><ospfArea><areaId>100</areaId><type>normal</type></ospfArea></ospfAreas><ospfInterfaces><ospfInterface><vnic>'+edge_ospf_int+'</vnic><areaId>100</areaId><helloInterval>10</helloInterval><deadInterval>40</deadInterval><priority>128</priority><cost>10</cost></ospfInterface></ospfInterfaces><redistribution><enabled>true</enabled><rules><rule><from><ospf>true</ospf> <connected>true</connected></from><action>permit</action></rule></rules></redistribution></ospf></routing>'
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('PUT', 'https://' + nsx_ip + '/api/4.0/edges/' + svc_edge_id+'/routing/config',xml_string,headers)
    response = conn.getresponse()
    if response.status != 204:
            print str(response.status) + " Routing NOT configured on SVC Edge " + str(svc_edge_id)
            exit(1)
    else:
            print str(response.status) + " Routing configured on SVC Edge " + str(svc_edge_id)
            return
        
def fw_svc_edge(svc_edge_id):
    xml_string = '<firewall><defaultPolicy><action>accept</action><loggingEnabled>false</loggingEnabled></defaultPolicy></firewall>'
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('PUT', 'https://' + nsx_ip + '/api/4.0/edges/' + svc_edge_id+'/firewall/config',xml_string,headers)
    response = conn.getresponse()
    if response.status != 204:
            print str(response.status) + " Firewall Default=Accept configured on Edge " + str(svc_edge_id)
            exit(1)
    else:
            print str(response.status) + " Firewall Default=Accept configured on Edge " + str(svc_edge_id)
            return

def main():
    vwires = []
    print " Creating Logical Switches..."
    for i in internal_ls_names:
        vwire_id = create_ls(i)
        vwires.append(vwire_id)
    print "----The following Logical Switches were created:  " + str(vwires)
    
    # Create a VDR
    print " Creating Distributed Logical Router... "
    vdr_edge_id = create_vdr(vdr_edge_name)
    # Configure VDR Edge FW to ALLOW traffic - Default is DENY
    fw_svc_edge(vdr_edge_id)
    
    # Create a Services Edge
    int_type = 'uplink'
    edge_gw_int = '0'
    svc_edge_id = create_svc_edge(svc_edge_name,svc_edge_uplink_dvpg,svc_edge_uplink_int_ip,svc_edge_uplink_int_mask,int_type,edge_gw_int)
    # Configure Services Edge FW to ALLOW traffic - Default is DENY
    fw_svc_edge(svc_edge_id)

    # Create LIFS on VDR create above
    # loop through returned rows of virtual-wires and append virtualwire ID to
    x=10
    print " Creating and configuring VDR Interfaces or LIFs..."
    for index, ls_id in enumerate(vwires):  
        xstring = str(x)
        x+= 10
        int_ip = '172.16.' + xstring + '.1'
        int_mask='255.255.255.0'
        int_type = 'internal'
        name = ls_id +'-API'
        int_lif = connect_ls(vdr_edge_id,name,ls_id,int_ip,int_mask,int_type)
    
    # Create Transport LS and Uplink LIF on VDR
    print "Creating and configuring Transport LS Interface on " + str(vdr_edge_id) + ' Distributed Logical Router'
    int_ip = '192.168.10.2'
    int_mask ='255.255.255.248'
    int_type = 'uplink'
    transport_vwire_id = create_ls(transport_ls_name)
    print "Transport vwire_id String = " + str(transport_vwire_id)
    lif_name=transport_vwire_id + '-API'
    uplk_lif = connect_ls(vdr_edge_id,lif_name,transport_vwire_id,int_ip,int_mask,int_type)
    print "Done. Transport LS Interface configured on " + str(vdr_edge_id)
    
    # Configure Routing on VDR Edge
    gw = '192.168.10.1'
    router_id = '192.168.10.2'
    ospf_int = '2'
    proto_add = '192.168.10.3'
    forward_add = '192.168.10.2'
    config_vdr(vdr_edge_id,gw,router_id,ospf_int,proto_add,forward_add)
    
    # Create Interface on Services Edge
    print "Creating and configuring Transport LS Interface on " + str(svc_edge_id) + ' Services Edge GW'
    int_ip = '192.168.10.1'
    int_mask ='255.255.255.248'
    int_type = 'internal'
    edge_ospf_int ='1'
    uplk_lif = connect_svc_ls(svc_edge_id,name,transport_vwire_id,int_ip,int_mask,int_type,edge_ospf_int)
    print "Done. Transport LS Interface configured on " + str(svc_edge_id) + ' Services Edge GW'
    
    # Configure Routing on SVC Edge
   
    edge_gw_int = '0'
    config_edge(svc_edge_id,svc_edge_uplink_gw,svc_edge_uplink_gw,edge_ospf_int,edge_gw_int)
    
    
    # To be used later
    # tz_id = create_tz(tz_name)
    # print tz_id
    print " \n Successfully created environment ! ! !\n"
   
    
main()

