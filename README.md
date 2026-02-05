# 🚁 Chaos Engineer: ArduPilot SITL Dashboard

A standalone CLI tool designed for **ArduPilot Developers** to streamline fault injection and automated testing in SITL (Software In The Loop).

Instead of manually typing repetitive MAVLink commands, this dashboard provides a structured interface to inject failures (Wind, GPS Glitch) and verify failsafes.

## ✨ Features
- **🛡️ Smart Launch:** Automated Pre-flight checks (Battery, GPS, Altitude) before takeoff.
- **💀 Chaos Injection:** One-click triggering of High Wind (20m/s) and GPS Glitches.
- **🌍 Precision Navigation:** Fly to specific Lat/Lon or relative NED coordinates.
- **🛑 Safety First:** Automated Land and Disarm sequence.
- **📊 Telemetry:** Real-time feedback from the drone.


## 🔮 Future Roadmap (GSoC 2026 Strategy)
This tool is currently a standalone prototype. My goal is to evolve it into a full **Automated Regression Testing Suite** for ArduPilot.

Planned features include:
- [ ] **MAVProxy Module Integration:** Porting this tool to run natively inside the MAVProxy console (`module load chaos`).
- [ ] **Scenario Scripting:** Support for JSON/YAML based mission files to run complex test scenarios automatically.
- [ ] **Automated Reporting:** Generating PDF/HTML test reports with crash data and flight logs after every session.
- [ ] **Docker Support:** Containerizing the environment for one-command setup.


## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/luckys00/ArduPilot-SITL-Chaos-Dashboard.git](https://github.com/luckys00/ArduPilot-SITL-Chaos-Dashboard.git)
   cd ArduPilot-SITL-Chaos-Dashboard
'''

2. Install Dependencies: This tool requires pymavlink to communicate with the drone.

        pip install -r requirements.txt

## 🚀 How to Run

To use this tool, you need two terminals open.

**Step 1: Start ArduPilot Simulator**
Open your first terminal and start the Copter simulation:
   
    sim_vehicle.py -v Copter --console --map

**Step 2: Run the Dashboard
          Open a second terminal,
          go to your folder,
          run the script:
       
           python3 sitl_dashboardup.py

 

