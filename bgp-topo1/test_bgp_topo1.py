#!/usr/bin/env python

#
# test_bgp_topo1.py
# Part of NetDEF Topology Tests
#
# Copyright (c) 2017 by
# Network Device Education Foundation, Inc. ("NetDEF")
#
# Permission to use, copy, modify, and/or distribute this software
# for any purpose with or without fee is hereby granted, provided
# that the above copyright notice and this permission notice appear
# in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NETDEF DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NETDEF BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
#

"""
test_bgp_topo1.py: Test BGP topology with ECMP (Equal Cost MultiPath).
"""

import os
import sys
import pytest

# Save the Current Working Directory to find configuration files.
CWD = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(CWD, '../'))

# pylint: disable=C0413
# Import topogen and topotest helpers
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen

# Required to instantiate the topology builder class.
from mininet.topo import Topo

class BGPTopo(Topo):
    "Test topology builder"
    def build(self, *_args, **_opts):
        "Build function"
        tgen = get_topogen(self)

        # Create 7 routers
        for routern in range(1, 13):
            tgen.add_router('r{}'.format(routern))

        # Create the edge network.
        switch = tgen.add_switch('s1')
        switch.add_link(tgen.gears['r1'])

        # Create all r1 connections with the middle boxes
        switch = tgen.add_switch('s2')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r2'])
        switch = tgen.add_switch('s3')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r3'])
        switch = tgen.add_switch('s4')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r4'])
        switch = tgen.add_switch('s5')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r5'])
        switch = tgen.add_switch('s6')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r6'])
        switch = tgen.add_switch('s7')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r7'])
        switch = tgen.add_switch('s8')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r8'])
        switch = tgen.add_switch('s9')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r9'])
        switch = tgen.add_switch('s10')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r10'])

        # Create all middle boxes connection with the other edge end
        switch = tgen.add_switch('s11')
        switch.add_link(tgen.gears['r2'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s12')
        switch.add_link(tgen.gears['r3'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s13')
        switch.add_link(tgen.gears['r4'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s14')
        switch.add_link(tgen.gears['r5'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s15')
        switch.add_link(tgen.gears['r6'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s16')
        switch.add_link(tgen.gears['r7'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s17')
        switch.add_link(tgen.gears['r8'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s18')
        switch.add_link(tgen.gears['r9'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s19')
        switch.add_link(tgen.gears['r10'])
        switch.add_link(tgen.gears['r11'])

        # Create r11 and connect it with r12
        switch = tgen.add_switch('s20')
        switch.add_link(tgen.gears['r11'])
        switch.add_link(tgen.gears['r12'])

def setup_module(_m):
    "Sets up the pytest environment"
    tgen = Topogen(BGPTopo)
    tgen.start_topology()

    # This is a sample of configuration loading.
    router_list = tgen.routers()

    # For all registred routers, load the zebra configuration file
    for rname, router in router_list.iteritems():
        router.load_config(
            TopoRouter.RD_ZEBRA,
            os.path.join(CWD, '{}/zebra.conf'.format(rname))
        )
        router.load_config(
            TopoRouter.RD_BGP,
            os.path.join(CWD, '{}/bgpd.conf'.format(rname))
        )

    # After loading the configurations, this function loads configured daemons.
    tgen.start_router()

def teardown_module(_m):
    "Teardown the pytest environment"
    tgen = get_topogen()
    tgen.stop_topology()

def test_bgp_ecmp():
    "Test BGP convergence with a 9 way ECMP path."
    tgen = get_topogen()
    r11 = tgen.gears['r11']

    # Comparison data
    expected = {
        'routerId': '10.2.255.1',
        'routes': {
            '10.0.1.0/24': [
                {'aspath': '100 10',
                 'multipath': True,
                 'nexthops': [{
                     'afi': 'ipv4',
                     'ip': '172.16.10.1',
                     'used': True,
                     }],
                 'peerId': '172.16.10.1',
                 'valid': True,
                 'weight': 0,
                },
                {'aspath': '101 10',
                 'multipath': True,
                 'peerId': '172.16.11.1',
                 'valid': True},
                {'aspath': '102 10',
                 'multipath': True,
                 'peerId': '172.16.12.1',
                 'valid': True},
                {'aspath': '103 10',
                 'multipath': True,
                 'peerId': '172.16.13.1',
                 'valid': True},
                {'aspath': '104 10',
                 'multipath': True,
                 'peerId': '172.16.14.1',
                 'valid': True},
                {'aspath': '105 10',
                 'multipath': True,
                 'peerId': '172.16.15.1',
                 'valid': True},
                {'aspath': '106 10',
                 'multipath': True,
                 'peerId': '172.16.16.1',
                 'valid': True},
                {'aspath': '107 10',
                 'multipath': True,
                 'peerId': '172.16.17.1',
                 'valid': True},
                {'aspath': '108 10',
                 'multipath': True,
                 'peerId': '172.16.18.1',
                 'valid': True},
                ],
            '10.0.2.0/24': [{
                'multipath': None,
                'valid': True,
            }]
        }
    }

    # Comparison function
    def _compare_output():
        result = r11.vtysh_cmd('show ip bgp json', isjson=True)
        return topotest.json_cmp(result, expected)

    # Test or wait until the timeout expires.
    _, diff = topotest.run_and_expect(_compare_output, None, count=20, wait=1)
    assertmsg = 'Router "{}" did not converge as expected:\n{}'.format(r11.name, diff)
    assert diff is None, assertmsg

if __name__ == '__main__':
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
