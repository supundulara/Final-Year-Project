#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

#include <fstream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <random>
#include <nlohmann/json.hpp>

using namespace ns3;
using json = nlohmann::json;

NS_LOG_COMPONENT_DEFINE("AirportSimulation");

// ================= CAMERA CONFIG =================
struct CameraConfig {
    uint32_t id;
    uint32_t accessId;
    uint32_t aggregationId;
    uint32_t coreId;
    std::string processing;   // camera / access / aggregation / core
    std::string model;        // small / medium / heavy
    uint32_t frameSize;       // bytes
    double frameInterval;     // seconds
    double inferenceDelay;    // seconds
    uint32_t resultSize;      // bytes
};

// ================= UTILS =================
double GetInferenceDelay(const std::string& model, std::mt19937 &gen) {
    double base;
    if (model == "small") base = 0.01;
    else if (model == "medium") base = 0.05;
    else base = 0.12; // heavy
    std::normal_distribution<double> dist(base, 0.2 * base);
    return std::max(0.001, dist(gen));
}

uint32_t GetResultSize(const std::string& model, std::mt19937 &gen) {
    uint32_t base;
    if (model == "small") base = 200;
    else if (model == "medium") base = 500;
    else base = 1200;
    std::normal_distribution<double> dist(base, 0.15 * base);
    return std::max(50u, (uint32_t)dist(gen));
}

uint32_t GetFrameSize(const std::string& model, std::mt19937 &gen) {
    uint32_t base;
    if (model == "small") base = 1000;
    else if (model == "medium") base = 1500;
    else base = 2000;
    std::normal_distribution<double> dist(base, 0.1 * base);
    return std::max(500u, (uint32_t)dist(gen));
}

double GetFrameInterval(const std::string& processing, std::mt19937 &gen) {
    double base;
    if (processing == "camera") base = 0.15;
    else if (processing == "access") base = 0.1;
    else if (processing == "aggregation") base = 0.08;
    else base = 0.05;
    std::normal_distribution<double> dist(base, 0.05*base);
    return std::max(0.01, dist(gen));
}

// ================= MAIN =================
int main(int argc, char *argv[]) {
    Time::SetResolution(Time::NS);
    LogComponentEnable("AirportSimulation", LOG_LEVEL_INFO);

    uint32_t scenarioCount = 100; // default
    CommandLine cmd;
    cmd.AddValue("scenarios", "Number of scenarios to simulate", scenarioCount);
    cmd.Parse(argc, argv);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> procDist(0, 3); // processing location

    for (uint32_t scenario = 0; scenario < scenarioCount; scenario++) {
        NS_LOG_INFO("Running scenario " << scenario);

        // ===== PARAMETERS PER SCENARIO =====
        uint32_t numCameras     = 150 + scenario % 51; // 150–200 cameras
        uint32_t numAccessNodes = 10 + scenario % 6;   // 10–15
        uint32_t numAggNodes    = 4 + scenario % 3;    // 4–6
        uint32_t numCoreNodes   = 2;                   // fixed
        uint32_t numCloudNodes  = 1;                   // fixed

        // ===== NODE CREATION =====
        NodeContainer cameras, accessNodes, aggNodes, coreNodes, cloud;
        cameras.Create(numCameras);
        accessNodes.Create(numAccessNodes);
        aggNodes.Create(numAggNodes);
        coreNodes.Create(numCoreNodes);
        cloud.Create(numCloudNodes);

        NodeContainer allNodes;
        allNodes.Add(cameras);
        allNodes.Add(accessNodes);
        allNodes.Add(aggNodes);
        allNodes.Add(coreNodes);
        allNodes.Add(cloud);

        // ===== WIFI CAM → ACCESS =====
        WifiHelper wifi; wifi.SetStandard(WIFI_STANDARD_80211n);
        YansWifiPhyHelper phy; YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
        phy.SetChannel(channel.Create());
        WifiMacHelper mac; Ssid ssid("airport-net");
        mac.SetType("ns3::StaWifiMac","Ssid",SsidValue(ssid));
        NetDeviceContainer camDevs = wifi.Install(phy, mac, cameras);
        mac.SetType("ns3::ApWifiMac","Ssid",SsidValue(ssid));
        NetDeviceContainer accessDevs = wifi.Install(phy, mac, accessNodes);

        // ===== P2P LINKS =====
        PointToPointHelper p2p; 
        p2p.SetDeviceAttribute("DataRate", StringValue("10Gbps"));
        p2p.SetChannelAttribute("Delay", StringValue("5ms"));

        NetDeviceContainer aggDevs, coreDevs, cloudDevs;
        for (uint32_t i=0;i<numAccessNodes;i++)
            for (uint32_t j=0;j<numAggNodes;j++)
                aggDevs.Add(p2p.Install(accessNodes.Get(i), aggNodes.Get(j)));
        for (uint32_t i=0;i<numAggNodes;i++)
            for (uint32_t j=0;j<numCoreNodes;j++)
                coreDevs.Add(p2p.Install(aggNodes.Get(i), coreNodes.Get(j)));
        for (uint32_t i=0;i<numCoreNodes;i++)
            cloudDevs.Add(p2p.Install(coreNodes.Get(i), cloud.Get(0)));

        // ===== INTERNET STACK =====
        InternetStackHelper stack; stack.Install(allNodes);
        Ipv4AddressHelper addr; addr.SetBase("10.0.0.0","255.255.0.0");
        addr.Assign(camDevs); addr.Assign(accessDevs); addr.Assign(aggDevs); addr.Assign(coreDevs); addr.Assign(cloudDevs);
        Ipv4GlobalRoutingHelper::PopulateRoutingTables();

        // ===== MOBILITY =====
        MobilityHelper mob; mob.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        mob.Install(allNodes);

        // ===== CAMERA CONFIGS =====
        std::vector<CameraConfig> configs;
        std::vector<std::string> models = {"small","medium","heavy"};
        std::vector<std::string> procs = {"camera","access","aggregation","core"};

        for (uint32_t i=0;i<numCameras;i++){
            std::string model = models[i % 3];
            std::string proc = procs[procDist(gen)];
            configs.push_back({
                i,
                i % numAccessNodes,
                i % numAggNodes,
                i % numCoreNodes,
                proc,
                model,
                GetFrameSize(model, gen),
                GetFrameInterval(proc, gen),
                GetInferenceDelay(model, gen),
                GetResultSize(model, gen)
            });
        }

        // ===== FRAME FLOWS =====
        for (auto &c:configs){
            Ptr<Node> dst =
                (c.processing=="camera") ? cameras.Get(c.id) :
                (c.processing=="access") ? accessNodes.Get(c.accessId) :
                (c.processing=="aggregation") ? aggNodes.Get(c.aggregationId) :
                                               coreNodes.Get(c.coreId);

            OnOffHelper src("ns3::UdpSocketFactory",
                InetSocketAddress(dst->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(),9000+c.id));
            src.SetConstantRate(DataRate(c.frameSize*8 / c.frameInterval),c.frameSize);
            auto app = src.Install(cameras.Get(c.id));
            app.Start(Seconds(1.0));
            app.Stop(Seconds(20.0));
        }

        // ===== RESULT FLOWS =====
        for (auto &c:configs){
            Ptr<Node> procNode =
                (c.processing=="camera") ? cameras.Get(c.id) :
                (c.processing=="access") ? accessNodes.Get(c.accessId) :
                (c.processing=="aggregation") ? aggNodes.Get(c.aggregationId) :
                                               coreNodes.Get(c.coreId);

            OnOffHelper res("ns3::UdpSocketFactory",
                InetSocketAddress(cloud.Get(0)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(),10000+c.id));
            res.SetConstantRate(DataRate(c.resultSize*8 / 0.5), c.resultSize);
            auto app = res.Install(procNode);
            app.Start(Seconds(1.0+c.inferenceDelay));
            app.Stop(Seconds(20.0));
        }

        // ===== FLOW MONITOR =====
        FlowMonitorHelper fm;
        Ptr<FlowMonitor> monitor = fm.InstallAll();
        Simulator::Stop(Seconds(22.0));
        Simulator::Run();

        // ===== OUTPUT =====
        std::ostringstream dir;
        dir << "outputs/airport_scenarios/scenario_" << std::setw(4) << std::setfill('0') << scenario;
        system(("mkdir -p "+dir.str()).c_str());

        monitor->SerializeToXmlFile(dir.str()+"/flow.xml", true,true);
        json meta;
        meta["scenario"]=scenario;
        meta["cameras"]=json::array();
        for (auto &c:configs)
            meta["cameras"].push_back({
                {"id",c.id},
                {"processing",c.processing},
                {"model",c.model},
                {"frame_size",c.frameSize},
                {"frame_interval",c.frameInterval},
                {"inference_delay",c.inferenceDelay},
                {"result_size",c.resultSize}
            });
        std::ofstream cfg(dir.str()+"/config.json");
        cfg << meta.dump(4); cfg.close();

        Simulator::Destroy();
    }

    NS_LOG_INFO("All scenarios completed.");
    return 0;
}
