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
#include <filesystem>
#include <nlohmann/json.hpp>

using namespace ns3;
using json = nlohmann::json;
namespace fs = std::filesystem;

NS_LOG_COMPONENT_DEFINE("WarehouseSimulation");

/* ================= CV CONFIG ================= */

struct CameraConfig {
    uint32_t id;
    uint32_t edgeId;
    uint32_t cloudId;
    std::string processing;   // camera / edge / cloud
    std::string model;        // small / medium / heavy
    uint32_t frameSize;       // bytes
    double frameInterval;     // seconds
    double inferenceDelay;    // seconds
    uint32_t resultSize;      // bytes
};

/* ================= UTILS ================= */

double GetInferenceDelay(const std::string& model) {
    if (model == "small") return 0.01;
    if (model == "medium") return 0.05;
    return 0.12; // heavy
}

uint32_t GetResultSize(const std::string& model) {
    if (model == "small") return 200;
    if (model == "medium") return 500;
    return 1200;
}

/* ================= MAIN ================= */

int main(int argc, char *argv[]) {

    Time::SetResolution(Time::NS);
    LogComponentEnable("WarehouseSimulation", LOG_LEVEL_INFO);

    uint32_t scenarioCount = 100;
    CommandLine cmd;
    cmd.AddValue("scenarios", "Number of scenarios", scenarioCount);
    cmd.Parse(argc, argv);

    // Create top-level outputs folder
    fs::create_directories("outputs");

    for (uint32_t scenario = 0; scenario < scenarioCount; scenario++) {

        NS_LOG_INFO("Running scenario " << scenario);

        uint32_t numCameras = 6 + (scenario % 5);   // 6–10 cameras
        uint32_t numEdges   = 2 + (scenario % 2);   // 2–3 edges
        uint32_t numClouds  = 2;

        NodeContainer cameras, edges, clouds, control;
        cameras.Create(numCameras);
        edges.Create(numEdges);
        clouds.Create(numClouds);
        control.Create(1);

        NodeContainer all;
        all.Add(cameras);
        all.Add(edges);
        all.Add(clouds);
        all.Add(control);

        /* ================= WIFI (CAM → EDGE) ================= */
        WifiHelper wifi;
        wifi.SetStandard(WIFI_STANDARD_80211n);

        YansWifiPhyHelper phy;
        YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
        phy.SetChannel(channel.Create());

        WifiMacHelper mac;
        Ssid ssid("warehouse");

        mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid));
        NetDeviceContainer camDevs = wifi.Install(phy, mac, cameras);

        mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
        NetDeviceContainer edgeDevs = wifi.Install(phy, mac, edges);

        /* ================= EDGE ↔ CLOUD ↔ CONTROL (P2P) ================= */
        PointToPointHelper p2p;
        p2p.SetDeviceAttribute("DataRate", StringValue("10Gbps"));
        p2p.SetChannelAttribute("Delay", StringValue("5ms"));

        NetDeviceContainer p2pDevs;
        for (uint32_t i = 0; i < numEdges; i++)
            for (uint32_t j = 0; j < numClouds; j++)
                p2pDevs.Add(p2p.Install(edges.Get(i), clouds.Get(j)));

        p2pDevs.Add(p2p.Install(clouds.Get(0), control.Get(0)));

        InternetStackHelper stack;
        stack.Install(all);

        Ipv4AddressHelper addr;
        addr.SetBase("10.0.0.0", "255.255.0.0");
        addr.Assign(camDevs);
        addr.Assign(edgeDevs);
        addr.Assign(p2pDevs);

        Ipv4GlobalRoutingHelper::PopulateRoutingTables();

        /* ================= MOBILITY ================= */
        MobilityHelper mob;
        mob.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        mob.Install(all);

        /* ================= CAMERA CONFIG ================= */
        std::vector<CameraConfig> configs;

        for (uint32_t i = 0; i < numCameras; i++) {
            std::string model = (i % 3 == 0) ? "heavy" : (i % 2 ? "medium" : "small");
            std::string proc  = (i % 3 == 0) ? "cloud" : (i % 2 ? "edge" : "camera");

            configs.push_back({
                i,
                i % numEdges,
                i % numClouds,
                proc,
                model,
                1500,
                0.1,
                GetInferenceDelay(model),
                GetResultSize(model)
            });
        }

        /* ================= FRAME FLOWS (CAM → EDGE/CLOUD) ================= */
        for (auto &c : configs) {
            Ptr<Node> dst =
                (c.processing == "camera") ? cameras.Get(c.id) :
                (c.processing == "edge")   ? edges.Get(c.edgeId) :
                                             clouds.Get(c.cloudId);

            OnOffHelper src("ns3::UdpSocketFactory",
                InetSocketAddress(dst->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(), 9000 + c.id));

            src.SetConstantRate(DataRate(c.frameSize * 8 / c.frameInterval), c.frameSize);
            auto app = src.Install(cameras.Get(c.id));
            app.Start(Seconds(1.0));
            app.Stop(Seconds(20.0));
        }

        /* ================= RESULT FLOWS (PROCESS → CONTROL) ================= */
        for (auto &c : configs) {
            Ptr<Node> procNode =
                (c.processing == "camera") ? cameras.Get(c.id) :
                (c.processing == "edge")   ? edges.Get(c.edgeId) :
                                             clouds.Get(c.cloudId);

            OnOffHelper res("ns3::UdpSocketFactory",
                InetSocketAddress(control.Get(0)->GetObject<Ipv4>()->GetAddress(1,0).GetLocal(), 10000 + c.id));

            res.SetConstantRate(DataRate(c.resultSize * 8 / 0.5), c.resultSize);
            auto app = res.Install(procNode);
            app.Start(Seconds(1.0 + c.inferenceDelay));
            app.Stop(Seconds(20.0));
        }

        /* ================= FLOW MONITOR ================= */
        FlowMonitorHelper fm;
        Ptr<FlowMonitor> monitor = fm.InstallAll();

        Simulator::Stop(Seconds(22.0));
        Simulator::Run();

        /* ================= OUTPUT FOLDERS ================= */
        std::ostringstream dir;
        dir << "outputs/scenario_" << std::setw(3) << std::setfill('0') << scenario;
        fs::create_directories(dir.str());  

        monitor->SerializeToXmlFile(dir.str() + "/flow.xml", true, true);

        json meta;
        meta["scenario"] = scenario;
        meta["cameras"] = json::array();
        for (auto &c : configs)
            meta["cameras"].push_back({
                {"id", c.id},
                {"processing", c.processing},
                {"model", c.model},
                {"inference_delay", c.inferenceDelay},
                {"result_size", c.resultSize}
            });

        std::ofstream cfg(dir.str() + "/config.json");
        cfg << meta.dump(4);
        cfg.close();

        Simulator::Destroy();
    }

    NS_LOG_INFO("All scenarios completed.");
    return 0;
}
