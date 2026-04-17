#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class SimpleTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        for h in range(1,4):
            host = self.addHost(f'h{h}', ip=f'10.0.0.{h}/24')
            self.addLink(host, s1)

if __name__ == '__main__':
    setLogLevel('info')
    topo = SimpleTopo()
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633))
    net.start()
    CLI(net)
    net.stop()
