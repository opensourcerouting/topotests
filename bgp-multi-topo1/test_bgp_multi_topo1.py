#!/usr/bin/env python

#
# test_bgp_multi_topo1.py
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
test_bgp_multi_topo1.py: Test BGP running in multiple different
configurations:

* Single homed AS
* Multi homed AS - non-transit
* Multi homed AS - transit
* ECMP inside the same AS
* ECMP with different ASes
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
from lib.topolog import logger

# Required to instantiate the topology builder class.
from mininet.topo import Topo

class TemplateTopo(Topo):
    "Test topology builder"
    def build(self, *_args, **_opts):
        "Build function"
        tgen = get_topogen(self)

        # AS 1 routers
        tgen.add_router('r1')
        tgen.add_router('r2')
        tgen.add_router('r3')

        # AS 10 routers
        tgen.add_router('r10')
        tgen.add_router('r11')

        # AS 20 routers
        tgen.add_router('r20')
        tgen.add_router('r21')
        tgen.add_exabgp_peer('peer20', '10.2.1.10/24', '10.2.1.1/24')
        tgen.add_exabgp_peer('peer21', '10.2.1.11/24', '10.2.1.1/24')
        tgen.add_exabgp_peer('peer22', '10.2.2.10/24', '10.2.2.1/24')
        tgen.add_exabgp_peer('peer23', '10.2.2.11/24', '10.2.2.1/24')

        # AS 30 routers
        tgen.add_router('r30')
        tgen.add_router('r31')
        tgen.add_exabgp_peer('peer30', '10.3.1.10/24', '10.3.1.1/24')
        tgen.add_exabgp_peer('peer31', '10.3.1.11/24', '10.3.1.1/24')
        tgen.add_exabgp_peer('peer32', '10.3.2.10/24', '10.3.2.1/24')
        tgen.add_exabgp_peer('peer33', '10.3.2.11/24', '10.3.2.1/24')

        # Interconnect AS 0
        switch = tgen.add_switch('s1')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r3'])
        switch = tgen.add_switch('s2')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r2'])
        switch = tgen.add_switch('s3')
        switch.add_link(tgen.gears['r2'])
        switch.add_link(tgen.gears['r3'])

        # Interconnect AS 10
        switch = tgen.add_switch('s10')
        switch.add_link(tgen.gears['r10'])
        switch = tgen.add_switch('s11')
        switch.add_link(tgen.gears['r10'])
        switch = tgen.add_switch('s12')
        switch.add_link(tgen.gears['r10'])
        switch.add_link(tgen.gears['r11'])

        # Interconnect AS 20
        switch = tgen.add_switch('s22')
        switch.add_link(tgen.gears['r20'])
        switch.add_link(tgen.gears['r21'])
        switch = tgen.add_switch('s23')
        switch.add_link(tgen.gears['r20'])
        switch.add_link(tgen.gears['peer20'])
        switch.add_link(tgen.gears['peer21'])
        switch = tgen.add_switch('s24')
        switch.add_link(tgen.gears['r21'])
        switch.add_link(tgen.gears['peer22'])
        switch.add_link(tgen.gears['peer23'])

        # Interconnect AS 30
        switch = tgen.add_switch('s32')
        switch.add_link(tgen.gears['r30'])
        switch.add_link(tgen.gears['r31'])
        switch = tgen.add_switch('s33')
        switch.add_link(tgen.gears['r30'])
        switch.add_link(tgen.gears['peer30'])
        switch.add_link(tgen.gears['peer31'])
        switch = tgen.add_switch('s34')
        switch.add_link(tgen.gears['r31'])
        switch.add_link(tgen.gears['peer32'])
        switch.add_link(tgen.gears['peer33'])

        # Interconnect ASes
        switch = tgen.add_switch('s13')
        switch.add_link(tgen.gears['r1'])
        switch.add_link(tgen.gears['r11'])
        switch = tgen.add_switch('s20')
        switch.add_link(tgen.gears['r2'])
        switch.add_link(tgen.gears['r20'])
        switch = tgen.add_switch('s21')
        switch.add_link(tgen.gears['r3'])
        switch.add_link(tgen.gears['r21'])
        switch = tgen.add_switch('s30')
        switch.add_link(tgen.gears['r2'])
        switch.add_link(tgen.gears['r30'])
        switch = tgen.add_switch('s31')
        switch.add_link(tgen.gears['r3'])
        switch.add_link(tgen.gears['r31'])


def setup_module(mod):
    "Sets up the pytest environment"
    # This function initiates the topology build with Topogen...
    tgen = Topogen(TemplateTopo, mod.__name__)
    # ... and here it calls Mininet initialization functions.
    tgen.start_topology()

    # This is a sample of configuration loading.
    router_list = tgen.routers()

    # For all registered routers, load the zebra configuration file
    for rname, router in router_list.iteritems():
        router.load_config(
            TopoRouter.RD_ZEBRA,
            os.path.join(CWD, '{}/zebra.conf'.format(rname))
        )

        # Only load configuration if they are available
        bgpd_path = os.path.join(CWD, '{}/bgpd.conf'.format(rname))
        ospfd_path = os.path.join(CWD, '{}/ospfd.conf'.format(rname))
        if os.path.isfile(bgpd_path):
            router.load_config(TopoRouter.RD_BGP, bgpd_path)
        if os.path.isfile(ospfd_path):
            router.load_config(TopoRouter.RD_OSPF, ospfd_path)

    # After loading the configurations, this function loads configured daemons.
    tgen.start_router()

def teardown_module(mod):
    "Teardown the pytest environment"
    tgen = get_topogen()

    # This function tears down the whole topology.
    tgen.stop_topology()

def test_call_mininet_cli():
    "Dummy test that just calls mininet CLI so we can interact with the build."
    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    logger.info('calling mininet CLI')
    tgen.mininet_cli()

# Memory leak test template
def test_memory_leak():
    "Run the memory leak test and report results."
    tgen = get_topogen()
    if not tgen.is_memleak_enabled():
        pytest.skip('Memory leak test/report is disabled')

    tgen.report_memory_leaks()

if __name__ == '__main__':
    args = ["-s"] + sys.argv[1:]
    sys.exit(pytest.main(args))
