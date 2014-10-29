'''
Created on Oct 2, 2013
@author: tkraus
This script will Destroy all Logical Switches, VDR's, and SVC Edge devices
'''
import base64
import urllib2
from xml.dom.minidom import parseString
from xml.etree import ElementTree as ET
import httplib

global nsx_ip
global headers

nsx_ip="10.21.23.25"
nsx_port = 443
username = "admin"
password = "VMware1!"
vdn_scope = 'vdnscope-1'
creds= base64.urlsafe_b64encode(username + ':' + password)
headers = {'Content-Type' : 'application/xml','Authorization' : 'Basic ' + creds }

def delete_ls(ls_id):
    body = None
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('DELETE', '/api/2.0/vdn/virtualwires/' + ls_id,body,headers)
    response = conn.getresponse()
    if response.status != 200:
            print str(response.status) + " LS " + str(ls_id) +" NOT Deleted !"
            return
    else:
            print str(response.status) + " LS " + str(ls_id) + " Deleted !\n"
            return

def delete_edge(edge_id):
    body = None
    conn = httplib.HTTPSConnection(nsx_ip, nsx_port)
    conn.request('DELETE', '/api/4.0/edges/' + edge_id,body,headers)
    response = conn.getresponse()
    if response.status != 204:
            print str(response.status) + " Edge " + str(edge_id) +" NOT Deleted !"
            exit(1)
    else:
            print str(response.status) + " Edge " + str(edge_id) + " Deleted !\n"
            return

def get_ls():
    url='https://' + nsx_ip + '/api/2.0/vdn/scopes/'+vdn_scope+'/virtualwires'
    req = urllib2.Request(url=url,  
        headers=headers)
    response=urllib2.urlopen(req)
    data=response.read()
    xmldoc=ET.fromstring(data)
    vwires=xmldoc.findall("./dataPage/virtualWire/objectId")
    return vwires

def get_edges():
    url='https://' + nsx_ip + '/api/4.0/edges'
    req = urllib2.Request(url=url,  
        headers=headers)
    response=urllib2.urlopen(req)
    data=response.read()
    xmldoc=ET.fromstring(data)
    edges=xmldoc.findall("./edgePage/edgeSummary/objectId")
    return edges
    
def main():
    edges=get_edges()
    for edge in edges:
        edge_id = edge.text
        delete_edge(edge_id)
    
    vwires=get_ls()
    for wire in vwires:
        ls_id = wire.text
        delete_ls(ls_id)
    print " Environment Destroyed !"
main()


