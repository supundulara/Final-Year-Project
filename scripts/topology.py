# scripts/topology.py

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel

def create_topology():
    """
    Creates a warehouse surveillance network:
    - 15 camera hosts
    - 1 edge processing host
    - 1 cloud host
    - Switches connecting cameras -> edge -> cloud
    """

    net = Mininet(switch=OVSSwitch, link=TCLink, controller=RemoteController)

    # ---------- Add controller ----------
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    # ---------- Add nodes ----------
    cameras = [net.addHost(f'cam{i}', cpu=0.1) for i in range(1, 16)]
    edge = net.addHost('edge', cpu=0.8)
    cloud = net.addHost('cloud', cpu=1.0)
    
    # ---------- Add switches ----------
    s1 = net.addSwitch('s1')  # Switch for cameras -> edge
    s2 = net.addSwitch('s2')  # Switch for edge -> cloud

    # ---------- Connect cameras to s1 ----------
    for cam in cameras:
        net.addLink(cam, s1, bw=10, delay='2ms', max_queue_size=200)

    # ---------- Connect s1 to edge ----------
    net.addLink(s1, edge, bw=20, delay='5ms', max_queue_size=500)

    # ---------- Connect s1 to s2 ----------
    net.addLink(s1, s2, bw=50, delay='20ms', max_queue_size=1000)

    # ---------- Connect s2 to cloud ----------
    net.addLink(s2, cloud, bw=100, delay='50ms', max_queue_size=2000)

    return net, cameras, edge, cloud