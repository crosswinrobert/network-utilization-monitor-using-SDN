from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
import pox.lib.packet as pkt
import time
import threading

log = core.getLogger()

class OrangeSwitch(object):
    def __init__(self, connection):
        self.connection = connection
        self.mac_to_port = {}
        self.port_stats = {}
        self.stats_interval = 5
        connection.addListeners(self)
        self._start_stats_poller()

    def _start_stats_poller(self):
        def poll():
            while True:
                self._request_stats()
                time.sleep(self.stats_interval)
        thread = threading.Thread(target=poll)
        thread.daemon = True
        thread.start()

    def _request_stats(self):
        msg = of.ofp_stats_request(body=of.ofp_port_stats_request())
        self.connection.send(msg)

    def _handle_PortStatsReceived(self, event):
        stats = event.stats
        now = time.time()
        for stat in stats:
            port_no = stat.port_no
            rx_bytes = stat.rx_bytes
            tx_bytes = stat.tx_bytes
            total_bytes = rx_bytes + tx_bytes

            prev = self.port_stats.get(port_no, {})
            prev_bytes = prev.get('bytes', 0)
            prev_time = prev.get('time', now)

            byte_diff = total_bytes - prev_bytes
            time_diff = now - prev_time
            if time_diff > 0:
                bps = (byte_diff * 8) / time_diff
                mbps = bps / 1_000_000
                log.info(f"Port {port_no}: {mbps:.2f} Mbps | Total Bytes: {total_bytes}")
            else:
                log.info(f"Port {port_no}: 0 Mbps | Total Bytes: {total_bytes}")

            self.port_stats[port_no] = {'bytes': total_bytes, 'time': now}

    def _handle_PacketIn(self, event):
        #FIREWALL AND FORWARDING CODE
        packet = event.parsed
        dpid = event.connection.dpid
        in_port = event.port

        self.mac_to_port[packet.src] = in_port

        if packet.type == pkt.ethernet.IP_TYPE:
            ip_pkt = packet.payload
            if ip_pkt.protocol == pkt.ipv4.ICMP_PROTOCOL:
                src_ip = ip_pkt.srcip
                dst_ip = ip_pkt.dstip
                if (src_ip == IPAddr("10.0.0.2") and dst_ip == IPAddr("10.0.0.3")) or \
                   (src_ip == IPAddr("10.0.0.3") and dst_ip == IPAddr("10.0.0.2")):
                    log.info(f"Firewall: Blocking ICMP {src_ip} -> {dst_ip}")
                    msg = of.ofp_flow_mod()
                    msg.priority = 100
                    msg.match.dl_type = pkt.ethernet.IP_TYPE
                    msg.match.nw_proto = pkt.ipv4.ICMP_PROTOCOL
                    msg.match.nw_src = src_ip
                    msg.match.nw_dst = dst_ip
                    event.connection.send(msg)
                    return

        dst_mac = packet.dst
        if dst_mac in self.mac_to_port:
            out_port = self.mac_to_port[dst_mac]
            msg = of.ofp_flow_mod()
            msg.priority = 10
            msg.match.dl_src = packet.src
            msg.match.dl_dst = dst_mac
            msg.match.in_port = in_port
            msg.idle_timeout = 60
            msg.hard_timeout = 300
            msg.actions.append(of.ofp_action_output(port=out_port))
            event.connection.send(msg)
        else:
            out_port = of.OFPP_FLOOD

        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.in_port = in_port
        event.connection.send(msg)

def launch():
    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        OrangeSwitch(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)
