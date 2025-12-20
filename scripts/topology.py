# scripts/topology.py

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel


def create_topology():
    """
    Creates a default warehouse surveillance network:
    - 15 camera hosts
    - 1 edge processing host
    - 1 cloud host
    - Switches connecting cameras -> edge -> cloud
    
    This is the original simple topology for basic experiments.
    For dataset generation, use create_topology_from_config() instead.
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


def create_topology_from_config(config):
    """
    Creates a configurable warehouse surveillance network based on scenario config.
    
    Args:
        config: Dictionary with topology parameters:
            - num_cameras: Number of camera hosts
            - bandwidth: Dict with 'cam_edge' and 'edge_cloud' bandwidth (Mbps)
            - delay: Dict with 'cam_edge' and 'edge_cloud' delay (e.g., '5ms')
            - queue_size: Dict with 'cam_edge' and 'edge_cloud' queue sizes
    
    Returns:
        tuple: (net, cameras, edge, cloud)
    """
    
    net = Mininet(switch=OVSSwitch, link=TCLink, controller=RemoteController)

    # ---------- Add controller ----------
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    # ---------- Add nodes ----------
    num_cameras = config.get('num_cameras', 15)
    cameras = [net.addHost(f'cam{i}', cpu=0.1) for i in range(1, num_cameras + 1)]
    edge = net.addHost('edge', cpu=0.8)
    cloud = net.addHost('cloud', cpu=1.0)
    
    # ---------- Add switches ----------
    s1 = net.addSwitch('s1')  # Switch for cameras -> edge
    s2 = net.addSwitch('s2')  # Switch for edge -> cloud

    # ---------- Connect cameras to s1 ----------
    cam_edge_bw = config['bandwidth']['cam_edge']
    cam_edge_delay = config['delay']['cam_edge']
    cam_edge_queue = config['queue_size']['cam_edge']
    
    for cam in cameras:
        net.addLink(cam, s1, 
                   bw=cam_edge_bw, 
                   delay=cam_edge_delay, 
                   max_queue_size=cam_edge_queue)

    # ---------- Connect s1 to edge ----------
    net.addLink(s1, edge, 
               bw=cam_edge_bw * 2,  # Double bandwidth for aggregation
               delay=config['delay']['cam_edge'],
               max_queue_size=cam_edge_queue * 2)

    # ---------- Connect s1 to s2 (inter-switch link) ----------
    edge_cloud_bw = config['bandwidth']['edge_cloud']
    edge_cloud_delay = config['delay']['edge_cloud']
    edge_cloud_queue = config['queue_size']['edge_cloud']
    
    net.addLink(s1, s2, 
               bw=edge_cloud_bw, 
               delay=edge_cloud_delay,
               max_queue_size=edge_cloud_queue)

    # ---------- Connect s2 to cloud ----------
    net.addLink(s2, cloud, 
               bw=edge_cloud_bw * 2,  # Higher bandwidth to cloud
               delay=edge_cloud_delay,
               max_queue_size=edge_cloud_queue * 2)

    return net, cameras, edge, cloud