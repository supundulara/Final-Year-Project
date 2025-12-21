#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"   
#include <fstream>
#include <nlohmann/json.hpp>

using namespace ns3;
using json = nlohmann::json;

NS_LOG_COMPONENT_DEFINE("WarehouseSimulation");

struct CameraConfig {
    std::string id;
    std::string zone;
    uint32_t packetSize;   // bytes
    double interval;       // seconds
    std::string processingLocation; // "camera", "edge", "cloud"
    std::string modelType;          // "small", "medium", "heavy"
};

int main(int argc, char *argv[])
{
    Time::SetResolution(Time::NS);
    LogComponentEnable("WarehouseSimulation", LOG_LEVEL_INFO);

    // Command-line scenario
    uint32_t scenario = 1;
    CommandLine cmd;
    cmd.AddValue("scenario", "Scenario ID", scenario);
    cmd.Parse(argc, argv);

    NS_LOG_INFO("Scenario: " << scenario);

    // Camera definitions per scenario
    std::vector<CameraConfig> cameras;
    uint32_t numCameras = 6;

    // Define scenarios
    switch (scenario) {
        case 1:
            cameras = {
                {"cam_01", "exit", 1024, 0.1, "camera", "medium"},
                {"cam_02", "aisle", 512, 0.2, "edge", "small"},
                {"cam_03", "aisle", 512, 0.2, "edge", "small"},
                {"cam_04", "exit", 2048, 0.05, "cloud", "heavy"},
                {"cam_05", "aisle", 512, 0.2, "edge", "small"},
                {"cam_06", "aisle", 512, 0.2, "edge", "small"}
            };
            break;
        case 2:
            cameras = {
                {"cam_01", "aisle", 512, 0.2, "edge", "small"},
                {"cam_02", "exit", 1024, 0.1, "camera", "medium"},
                {"cam_03", "aisle", 512, 0.2, "edge", "small"},
                {"cam_04", "exit", 1024, 0.1, "cloud", "medium"},
                {"cam_05", "aisle", 512, 0.2, "edge", "small"},
                {"cam_06", "aisle", 512, 0.2, "camera", "small"}
            };
            break;
        // Add more scenarios here
        default:
            NS_LOG_WARN("Scenario not defined. Using default scenario 1");
            scenario = 1;
            cameras = {
                {"cam_01", "exit", 1024, 0.1, "camera", "medium"},
                {"cam_02", "aisle", 512, 0.2, "edge", "small"},
                {"cam_03", "aisle", 512, 0.2, "edge", "small"},
                {"cam_04", "exit", 2048, 0.05, "cloud", "heavy"},
                {"cam_05", "aisle", 512, 0.2, "edge", "small"},
                {"cam_06", "aisle", 512, 0.2, "edge", "small"}
            };
            break;
    }

    NS_LOG_INFO("Creating nodes...");
    NodeContainer cameraNodes;
    cameraNodes.Create(numCameras);
    NodeContainer edgeNode; edgeNode.Create(1);
    NodeContainer cloudNode; cloudNode.Create(1);

    NodeContainer allNodes; allNodes.Add(cameraNodes); allNodes.Add(edgeNode); allNodes.Add(cloudNode);

    // WiFi setup for cameras -> edge
    WifiHelper wifi;
    wifi.SetStandard("802.11n");
    YansWifiPhyHelper phy;
    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    phy.SetChannel(channel.Create());
    WifiMacHelper mac;
    Ssid ssid = Ssid("warehouse-net");
    mac.SetType("ns3::StaWifiMac","Ssid",SsidValue(ssid),"ActiveProbing",BooleanValue(false));
    NetDeviceContainer cameraDevices = wifi.Install(phy, mac, cameraNodes);

    mac.SetType("ns3::ApWifiMac","Ssid",SsidValue(ssid));
    NetDeviceContainer edgeDevice = wifi.Install(phy, mac, edgeNode);

    // Point-to-point edge->cloud
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
    p2p.SetChannelAttribute("Delay", StringValue("5ms"));
    NetDeviceContainer cloudLink = p2p.Install(edgeNode.Get(0), cloudNode.Get(0));

    InternetStackHelper stack;
    stack.Install(allNodes);

    Ipv4AddressHelper address;
    address.SetBase("10.0.0.0", "255.255.255.0");
    Ipv4InterfaceContainer cameraIfaces = address.Assign(cameraDevices);
    Ipv4InterfaceContainer edgeIfaces = address.Assign(edgeDevice);
    Ipv4InterfaceContainer cloudIfaces = address.Assign(cloudLink);

    // Static mobility
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(allNodes);

    // Create traffic for each camera
    NS_LOG_INFO("Creating CV traffic...");
    for (uint32_t i = 0; i < cameras.size(); i++) {
        Ptr<Node> cam = cameraNodes.Get(i);
        Ptr<Node> destNode;
        if (cameras[i].processingLocation == "camera") destNode = cam;
        else if (cameras[i].processingLocation == "edge") destNode = edgeNode.Get(0);
        else destNode = cloudNode.Get(0);

        uint16_t port = 5000 + i;
        OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(destNode->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(), port));
        onoff.SetConstantRate(DataRate(cameras[i].packetSize*8/cameras[i].interval), cameras[i].packetSize);
        ApplicationContainer app = onoff.Install(cam);
        app.Start(Seconds(1.0));
        app.Stop(Seconds(10.0));
    }

    // FlowMonitor for metrics
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    // Save scenario configuration as JSON
    json configJson;
    configJson["scenario"] = scenario;
    for (auto &cam : cameras) {
        configJson["cameras"].push_back({
            {"id", cam.id},
            {"zone", cam.zone},
            {"processing", cam.processingLocation},
            {"model", cam.modelType},
            {"packetSize", cam.packetSize},
            {"interval", cam.interval}
        });
    }
    configJson["edge"] = { { "id", "edge_01", "bandwidth", "1Gbps", "delay", "5ms" } };
    configJson["cloud"] = { { "id", "cloud_01", "bandwidth", "10Gbps", "delay", "10ms" } };
    std::string jsonFile = "warehouse_config_" + std::to_string(scenario) + ".json";
    std::ofstream file(jsonFile); file << configJson.dump(4); file.close();

    // Run simulation
    NS_LOG_INFO("Running simulation...");
    Simulator::Stop(Seconds(12.0));
    Simulator::Run();

    // Save FlowMonitor XML
    std::string xmlFile = "warehouse_flow_" + std::to_string(scenario) + ".xml";
    monitor->SerializeToXmlFile(xmlFile, true, true);

    NS_LOG_INFO("Simulation completed. FlowMonitor saved to " << xmlFile << " and config saved to " << jsonFile);

    Simulator::Destroy();
    return 0;
}

