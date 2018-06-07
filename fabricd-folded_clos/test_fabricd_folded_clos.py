#!/usr/bin/env python

#
# <template>.py
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
<template>.py: Test <template>.
"""

import os
import sys
import json
import ipaddr
from time import sleep
from pprint import pprint
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

# Read Topology from file
topo_json = open("clos_topo.json").read()
topo = json.loads(topo_json)

class FoldedClosTopo(Topo):
    "Test topology builder"
    def build(self, *_args, **_opts):
        "Build function"
        tgen = get_topogen(self)

        # Fabricd Folded Clos Topology is built with
        # direct P2P links, no switches between

        # List of routers as read from structure.
        # Needed to mark which routers have the links already added
        listRouters = []

        # Create Topology - Step 1 routers:
        for routerN in sorted(topo['routers'].iteritems()):
            print("Topo: Add router ", routerN[0])
            # Create new router
            tgen.add_router(routerN[0])
            # Add to list of routers
            listRouters.append(routerN[0])

        # Keep interfaces consistent - need to process list of routers
        # in predicatable order
        listRouters.sort()

        if 'ipv4base' in topo:
            ipv4Next = ipaddr.IPv4Address(topo['ipv4base'])
            ipv4Step = 2**(32-topo['ipv4mask'])
            if topo['ipv4mask'] < 31:
                ipv4Next += 1
        if 'ipv6base' in topo:
            ipv6Next = ipaddr.IPv6Address(topo['ipv6base'])
            ipv6Step = 2**(128-topo['ipv6mask'])
            if topo['ipv6mask'] < 127:
                ipv6Next += 1

        # Create and save interface names as part of the link creation
        for router in listRouters:
            topo['routers'][router]['nextIfname'] = 0

        while listRouters != []:
            curRouter = listRouters.pop(0)
            for destRouter, data in sorted(topo['routers'][curRouter]['links'].iteritems()):
                if destRouter in listRouters:
                    # print("   Add connection from ", curRouter, " to ", destRouter)
                    topo['routers'][curRouter]['links'][destRouter]['interface'] = \
                        '{}-eth{}'.format(curRouter, topo['routers'][curRouter]['nextIfname'])
                    topo['routers'][destRouter]['links'][curRouter]['interface'] = \
                        '{}-eth{}'.format(destRouter, topo['routers'][destRouter]['nextIfname'])
                    topo['routers'][curRouter]['nextIfname'] += 1
                    topo['routers'][destRouter]['nextIfname'] += 1
                    tgen.gears[curRouter].add_link(
                        tgen.gears[destRouter],
                        topo['routers'][curRouter]['links'][destRouter]['interface'],
                        topo['routers'][destRouter]['links'][curRouter]['interface'])
                    print("   Added connection from ", curRouter,
                          topo['routers'][curRouter]['links'][destRouter]['interface'],
                          " to ", destRouter,
                          topo['routers'][destRouter]['links'][curRouter]['interface'])
                    #
                    # Now assign IPv4 & IPv6 addresses where needed
                    if 'ipv4' in topo['routers'][curRouter]['links'][destRouter]:
                        # IPv4 address on this link
                        if topo['routers'][curRouter]['links'][destRouter]['ipv4'] == 'auto':
                            # Need to assign addresses for this link
                            topo['routers'][curRouter]['links'][destRouter]['ipv4'] = '{}/{}'.format(ipv4Next, topo['ipv4mask'])
                            #ipv4Next += 1
                            topo['routers'][destRouter]['links'][curRouter]['ipv4'] = '{}/{}'.format(ipv4Next+1, topo['ipv4mask'])
                            ipv4Next += ipv4Step
                    if 'ipv6' in topo['routers'][curRouter]['links'][destRouter]:
                        # IPv6 address on this link
                        if topo['routers'][curRouter]['links'][destRouter]['ipv6'] == 'auto':
                            # Need to assign addresses for this link
                            topo['routers'][curRouter]['links'][destRouter]['ipv6'] = '{}/{}'.format(ipv6Next, topo['ipv6mask'])
                            #ipv6Next += 1
                            topo['routers'][destRouter]['links'][curRouter]['ipv6'] = '{}/{}'.format(ipv6Next+1, topo['ipv6mask'])
                            ipv6Next = ipaddr.IPv6Address(int(ipv6Next)+ipv6Step)

        # Print calculated Topology
        pprint(topo, indent=2)

def setup_module(mod):
    "Sets up the pytest environment"
    # This function initiates the topology build with Topogen...
    tgen = Topogen(FoldedClosTopo, mod.__name__)
    # ... and here it calls Mininet initialization functions.
    tgen.start_topology()

    # Get list of routers
    listRouters = []
    for routerN in topo['routers'].items():
        listRouters.append(routerN[0])
    listRouters.sort()

    topo['openfabric_net_counter'] = 1

    for curRouter in listRouters:
        if topo['routers'][curRouter]['started'] == 1:
            # Router is enabled - create config
            #
            # zebra.conf
            conffile = open('/tmp/zebra.conf', 'w')
            conffile.write('frr defaults traditional\n\n')
            conffile.write('hostname '+curRouter+'\n!\n')
            for destRouter, data in sorted(topo['routers'][curRouter]['links'].iteritems()):
                conffile.write('interface '+
                               topo['routers'][curRouter]['links'][destRouter]['interface']+'\n')
                conffile.write(' description Link '+curRouter+' to '+destRouter+'\n')
                if 'ipv4' in topo['routers'][curRouter]['links'][destRouter]:
                    # We have IPv4 address to configure
                    conffile.write(' ip address '+
                                   topo['routers'][curRouter]['links'][destRouter]['ipv4']+'\n')
                if 'ipv6' in topo['routers'][curRouter]['links'][destRouter]:
                    # We have IPv6 address to configure
                    conffile.write(' ipv6 address '+
                                   topo['routers'][curRouter]['links'][destRouter]['ipv6']+'\n')
                conffile.write('!\n')
            conffile.close()
            sleep(1)
            #
            # fabricd.conf
            conffile = open('/tmp/fabricd.conf', 'w')
            for destRouter, data in sorted(topo['routers'][curRouter]['links'].iteritems()):
                conffile.write('interface '+
                               topo['routers'][curRouter]['links'][destRouter]['interface']+'\n')
                conffile.write(' ip router openfabric 1\n')
                conffile.write(' ipv6 router openfabric 1\n')
                conffile.write('!\n')

            conffile.write('router openfabric 1\n')
            conffile.write(' net 49.0000.0000.{:04x}.00\n'.format(topo['openfabric_net_counter']))
            topo['openfabric_net_counter'] += 1
            conffile.write(' lsp-gen-interval 2\n')
            conffile.write(' spf-delay-ietf init-delay 30 short-delay 500 long-delay 5000 holddown 5000 time-to-learn 500')
            if 'openfabric' in topo['routers'][curRouter]:
                if 'tier' in topo['routers'][curRouter]['openfabric']:
                    conffile.write(' fabric-tier {}\n'.format(topo['routers'][curRouter]['openfabric']['tier']))
            conffile.write('!\n')
            conffile.close()
            sleep(1)

        # Load config
        tgen.gears[curRouter].load_config(
            TopoRouter.RD_ZEBRA,
            '/tmp/zebra.conf'
            #os.path.join(CWD, '{}/zebra.conf'.format(rname))
        )
        tgen.gears[curRouter].load_config(
            TopoRouter.RD_FABRICD,
            '/tmp/fabricd.conf'
            #os.path.join(CWD, '{}/fabricd.conf'.format(rname))
        )

    # # This is a sample of configuration loading.
    # router_list = tgen.routers()

    # # For all registred routers, load the zebra configuration file
    # for rname, router in router_list.iteritems():

    #     router.load_config(
    #         TopoRouter.RD_ZEBRA,
    #         #os.path.join(CWD, '{}/zebra.conf'.format(rname))
    #     )
    #     router.load_config(
    #         TopoRouter.RD_FABRICD,
    #         #os.path.join(CWD, '{}/fabricd.conf'.format(rname))
    #     )

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

