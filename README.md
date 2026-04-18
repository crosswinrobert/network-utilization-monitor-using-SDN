# SDN Mininet Project – Orange Problem: Network Utilization Monitor

## 📌 Problem Statement

This project implements an SDN-based solution using **Mininet** and the **POX controller** to demonstrate:

- Controller-switch interaction (Packet-In events and flow rule installation)
- Firewall functionality (blocking specific traffic between chosen hosts)
- Network utilization monitoring (measuring and displaying bandwidth per switch port in real time)

The goal is to understand how a centralized SDN controller can manage network behavior dynamically while observing performance and traffic statistics.

---

## 🛠️ Setup Instructions (Beginner-Friendly)

### ✅ Prerequisites

- A virtual machine or physical computer running **Ubuntu 20.04 or 22.04**
- Internet connection inside the VM
- Sudo (administrator) privileges

### 📦 Step 1: Install Mininet

Mininet creates a virtual network of hosts, switches, and links on your single machine.

Open a terminal and run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install mininet -y
```

**Verify the installation:**

```bash
sudo mn --test pingall
```

You should see all pings succeed with `0% packet loss`. Type `exit` to quit the Mininet CLI.

### 📦 Step 2: Install POX Controller

POX is a Python-based OpenFlow controller that will manage the switch.

```bash
git clone https://github.com/noxrepo/pox
```

POX requires **Python 3.9 or 3.10** for full compatibility. If you are using Ubuntu 22.04+ (which comes with Python 3.12), create a virtual environment with Python 3.10:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv -y
python3.10 -m venv ~/pox_env
source ~/pox_env/bin/activate
```

Then navigate to the POX directory and it will be ready to run.

---

## 📁 Project Files

This repository contains three main files:

| File | Description |
|------|-------------|
| `simple_topo.py` | Mininet custom topology (1 switch, multiple hosts) |
| `orange_controller.py` | POX controller application (learning switch + firewall + monitor) |
| `README.md` | This documentation |

---

## 🚀 How to Run the Project

### ▶️ Step 1: Start the POX Controller

Open a terminal and navigate to the POX folder:

```bash
cd ~/pox
```

Copy the `orange_controller.py` file into this directory if it's not already there:

```bash
cp ~/orange-sdn-project/orange_controller.py .
```

Launch the controller:

```bash
./pox.py orange_controller
```

You will see output like:

```
INFO:core:POX 0.7.0 (gar) is up.
INFO:openflow.of_01:[00-00-00-00-00-01 2] connected
```

**Leave this terminal running.** Every 5 seconds it will print bandwidth statistics for each switch port.

### ▶️ Step 2: Start the Mininet Topology

Open a **second terminal** and run:

```bash
cd ~/orange-sdn-project
sudo python3 simple_topo.py
```

The Mininet CLI will appear:

```
mininet>
```

You can now type commands to test the network.

---

## 🧪 Test Scenarios (Allowed vs Blocked)

### ✅ Allowed Communication

In the Mininet CLI, ping from `h1` to `h2`:

```
mininet> h1 ping -c 3 h2
```

**Expected Output:** All three pings succeed. The first ping may take ~40–80 ms (controller processing), while subsequent pings take <0.1 ms (hardware flow match).

### ❌ Blocked Communication (Firewall)

The controller is programmed to **block ICMP (ping) traffic between `h2` and `h3`**. Test this by running:

```
mininet> h2 ping -c 3 h3
```

**Expected Output:** 100% packet loss. The POX terminal will log:

```
INFO:orange_controller:Firewall: Blocking ICMP 10.0.0.2 -> 10.0.0.3
```

### 📋 View the Installed Flow Rules

To see the exact OpenFlow rules installed in the switch, run:

```
mininet> sh ovs-ofctl dump-flows s1
```

You will see:
- A **priority=100** rule that drops ICMP between `10.0.0.2` and `10.0.0.3`.
- Several **priority=10** rules that forward traffic based on MAC addresses.

---

## 📊 Network Utilization Monitor

The controller includes a background thread that requests port statistics from the switch every 5 seconds. It calculates the bandwidth in Mbps and logs it to the POX terminal.

### 🔍 How to Observe Bandwidth

1. Start the controller and Mininet as described above.
2. Generate traffic between two hosts, for example, using `iperf`:

   ```
   mininet> h1 iperf -s &
   mininet> h2 iperf -c 10.0.0.1 -t 15
   ```

3. Watch the **POX terminal** while `iperf` runs. You will see output like:

   ```
   INFO:orange_controller:Port 1: 44966.97 Mbps | Total Bytes: 102539248538
   INFO:orange_controller:Port 2: 44966.97 Mbps | Total Bytes: 102539248538
   INFO:orange_controller:Port 3: 0.00 Mbps | Total Bytes: 5390
   ```

**Interpretation:**
- Port 1 (connected to `h1`) and Port 2 (connected to `h2`) show high, symmetrical bandwidth during the test.
- Port 3 (connected to `h3`) remains idle.
- After `iperf` finishes, the bandwidth returns to `0.00 Mbps`.

---

## 📈 Performance Observation & Analysis

### ⏱️ Latency (Ping)

| Scenario | RTT | Why? |
|----------|-----|------|
| First ping (cold start) | ~40–80 ms | Packet goes to controller → flow installed → ARP resolved |
| Subsequent pings | ~0.04–0.20 ms | Packet hits installed flow in kernel datapath (fast path) |

### 📡 Throughput (iperf)

Running `iperf` between `h1` and `h2` yields **~40 Gbps** (depending on VM performance). This high throughput confirms that data plane forwarding operates at near line rate once flows are installed.

### 🧾 Flow Table Statistics

The `dump-flows` command shows how many packets matched each rule. The drop rule's packet count increases with each blocked ping, while forwarding flows' counts increase with successful traffic.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Unable to contact remote controller" | Make sure POX is running before starting Mininet. |
| POX fails to start with Python errors | Use Python 3.10 virtual environment (see setup). |
| `iperf` command not found | Install it: `sudo apt install iperf -y` |
| Flow table empty | The switch may not have connected; restart POX, then Mininet. |

---

## 🎥 Demo Videos / Screenshots

*(Add your screenshots here, e.g., using Markdown image syntax)*

```
![Ping Allowed](screenshots/ping_allowed.png)
![Ping Blocked](screenshots/ping_blocked.png)
![Flow Table](screenshots/flow_table.png)
![iperf Throughput](screenshots/iperf_throughput.png)
![Monitoring Logs](screenshots/monitoring_log.png)
```

---

## 📚 References

- Mininet: [https://mininet.org/](https://mininet.org/)
- POX Controller: [https://github.com/noxrepo/pox](https://github.com/noxrepo/pox)
- OpenFlow 1.0 Specification: [https://opennetworking.org/](https://opennetworking.org/)

---

## 👨‍💻 Author

**Krassveen Robert**  
GitHub: [@crosswinrobert](https://github.com/crosswinrobert)

---

*This project was completed as part of the Computer Networks (UE24CS252B) SDN assignment.*
