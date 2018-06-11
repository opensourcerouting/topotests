#!/usr/bin/env python

#
# test_fabricd_folded_clos.py
# Part of NetDEF Topology Tests
#
# Copyright (c) 2018 by
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
test_fabricd_folded_clos.py: Test for OpenFabric Folded Clos Topo.
"""

import os
import sys
import re
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

fatal_error = ""

# Read Topology from file
topoJson = open("clos_topo_multiple_tier0.json").read()
topo = json.loads(topoJson)

def row(routerName):
    """
    Returns the row number for the router.
    Calculation based on name a0 = row 0, a1 = row 1, b2 = row 2, z23 = row 23 etc
    """
    return int(routerName[1:])

def column(routerName):
    """
    Returns the column number for the router.
    Calculation based on name a0 = columnn 0, a1 = column 0, b2= column 1, z23 = column 26 etc
    """
    return ord(routerName[0])-97

def disable_router(routerName):
    "Disable selected router"

    tgen = get_topogen()

    logger.info('Stopping Router {}'.format(routerName))
    tgen.net[routerName].stopRouter(True)


def enable_router(routerName):
    "Disable selected router"

    tgen = get_topogen()

    logger.info('Stopping Router {}'.format(routerName))
    tgen.gears[routerName].start()



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
            logger.info('Topo: Add router {}'.format(routerN[0]))
            # Create new router
            tgen.add_router(routerN[0])
            # Add to list of routers
            listRouters.append(routerN[0])

        # Keep interfaces consistent - need to process list of routers
        # in predicatable order
        listRouters.sort()

        if 'ipv4base' in topo:
            ipv4Next = ipaddr.IPv4Address(topo['link_ip_start']['ipv4'])
            ipv4Step = 2**(32-topo['link_ip_start']['v4mask'])
            if topo['link_ip_start']['v4mask'] < 31:
                ipv4Next += 1
        if 'ipv6base' in topo:
            ipv6Next = ipaddr.IPv6Address(topo['link_ip_start']['ipv6'])
            ipv6Step = 2**(128-topo['link_ip_start']['v6mask'])
            if topo['link_ip_start']['v6mask'] < 127:
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
                        '{}-{}-eth{}'.format(curRouter, destRouter, topo['routers'][curRouter]['nextIfname'])
                    topo['routers'][destRouter]['links'][curRouter]['interface'] = \
                        '{}-{}-eth{}'.format(destRouter, curRouter, topo['routers'][destRouter]['nextIfname'])
                    topo['routers'][curRouter]['nextIfname'] += 1
                    topo['routers'][destRouter]['nextIfname'] += 1
                    tgen.gears[curRouter].add_link(
                        tgen.gears[destRouter],
                        topo['routers'][curRouter]['links'][destRouter]['interface'],
                        topo['routers'][destRouter]['links'][curRouter]['interface'])
                    #print("   Added connection from ", curRouter,
                    #      topo['routers'][curRouter]['links'][destRouter]['interface'],
                    #      " to ", destRouter,
                    #      topo['routers'][destRouter]['links'][curRouter]['interface'])
                    #
                    # Now assign IPv4 & IPv6 addresses where needed
                    if 'ipv4' in topo['routers'][curRouter]['links'][destRouter]:
                        # IPv4 address on this link
                        if topo['routers'][curRouter]['links'][destRouter]['ipv4'] == 'auto':
                            # Need to assign addresses for this link
                            topo['routers'][curRouter]['links'][destRouter]['ipv4'] = \
                                '{}/{}'.format(ipv4Next, topo['link_ip_start']['v4mask'])
                            #ipv4Next += 1
                            topo['routers'][destRouter]['links'][curRouter]['ipv4'] = \
                                '{}/{}'.format(ipv4Next+1, topo['link_ip_start']['v4mask'])
                            ipv4Next += ipv4Step
                    if 'ipv6' in topo['routers'][curRouter]['links'][destRouter]:
                        # IPv6 address on this link
                        if topo['routers'][curRouter]['links'][destRouter]['ipv6'] == 'auto':
                            # Need to assign addresses for this link
                            topo['routers'][curRouter]['links'][destRouter]['ipv6'] = \
                                '{}/{}'.format(ipv6Next, topo['link_ip_start']['v6mask'])
                            #ipv6Next += 1
                            topo['routers'][destRouter]['links'][curRouter]['ipv6'] = \
                                '{}/{}'.format(ipv6Next+1, topo['link_ip_start']['v6mask'])
                            ipv6Next = ipaddr.IPv6Address(int(ipv6Next)+ipv6Step)
            # Assign Loopback IPs
            if 'lo' in topo['routers'][curRouter]:
                if topo['routers'][curRouter]['lo']['ipv4'] == 'auto':
                    topo['routers'][curRouter]['lo']['ipv4'] = \
                        '{}{}.{}/{}'.format(topo['lo_prefix']['ipv4'],
                                            row(curRouter), column(curRouter),
                                            topo['lo_prefix']['v4mask'])
                if topo['routers'][curRouter]['lo']['ipv6'] == 'auto':
                    topo['routers'][curRouter]['lo']['ipv6'] = \
                        '{}{}:{}/{}'.format(topo['lo_prefix']['ipv6'],
                                            row(curRouter), column(curRouter),
                                            topo['lo_prefix']['v6mask'])

        # Print calculated Topology
        # pprint(topo, indent=2)


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
                conffile.write('interface lo\n')
                conffile.write(' description Loopback Router '+curRouter+'\n')
                conffile.write(' ip address '+topo['routers'][curRouter]['lo']['ipv4']+'\n')
                conffile.write(' ipv6 address '+topo['routers'][curRouter]['lo']['ipv6']+'\n')
                conffile.write('!\n')
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
            conffile.write('interface lo\n')
            conffile.write(' ip router openfabric 1\n')
            conffile.write(' ipv6 router openfabric 1\n')
            conffile.write(' openfabric passive\n')
            conffile.write('!\n')
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
            conffile.write(' spf-delay-ietf init-delay 30 short-delay 500 long-delay 5000 holddown 5000 time-to-learn\n')
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

    # After loading the configurations, this function loads configured daemons.
    tgen.start_router()


def teardown_module(mod):
    "Teardown the pytest environment"
    tgen = get_topogen()

    # This function tears down the whole topology.
    tgen.stop_topology()


def test_check_convergence():
    "Verifies OpenFabric Network has converged by checking for Tier"

    global fatal_error

    # We verify the convergence by a "show openfabric database detail"
    # and checking that no node shows "Tier: undefined"
    # Only need to check a single node. using C2 in middle

    logger.info('Waiting for convergence')

    tgen = get_topogen()
    timeout = 60
    while timeout > 0:
        logger.info('Waiting for convergence (timeout {}s)'.format(timeout))
        database = tgen.gears['c2'].vtysh_cmd('show openfabric database detail', isjson=False)
        m = re.search('Tier: undefined', database, re.DOTALL)
        if m:
            # Still have undefined Tier levels in topology
            sleep(4)
            timeout -= 4
        else:
            # All tier levels computed
            break

    if timeout == 0:
        fatal_error = 'Topology failed to converge'
        raise AssertionError('Topology failed to converge')


def test_verify_tier_level():
    "Verifies correct OpenFabric Tier discovered for each router."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    # Tiers 0..4 for this topo. Row 0 and 4 are Tier 0,
    # Row 1 and 3 are Tier 2 and Row 2 is Tier 2
    tier_rows = ["0", "1", "2", "1", "0"]

    logger.info('verifying Tier levels on all routers')

    tgen = get_topogen()
    errors = ''
    for routerN in topo['routers'].items():
        ofsummary = tgen.gears[routerN[0]].vtysh_cmd('show openfabric summary', isjson=False)
        m = re.search('Tier: ([0-9a-z]+)', ofsummary, re.DOTALL)
        if m:
            actualTier = m.group(1)
            #logger.info('Router {} reports tier {}'.format(routerN[0], actualTier))

            if tier_rows[row(routerN[0])] != actualTier:
                errors = errors+'Router {} shows tier {}, but expected tier {}\n'.format( \
                    routerN[0], actualTier, tier_rows[row(routerN[0])])
        else:
            errors = errors+'No Tier level found on Router {}'.format(routerN[0])

    if errors != "":
        errors.rstrip()
        fatal_error = 'Tier level calculation failed'
        raise AssertionError(errors)


def test_verify_ipv4_routing_table():
    "Dummy test that just calls mininet CLI so we can interact with the build."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    listRouters = []
    for routerN in topo['routers'].items():
        listRouters.append(routerN[0])
    listRouters.sort()

    for curRouter in listRouters:
        filename = '{0}/testdata/{1}_ipv4_routes.json'.format(CWD, curRouter)
        expected = json.loads(open(filename, 'r').read())
        actual = tgen.gears[curRouter].vtysh_cmd('show ip route json', isjson=True)

        logger.info('verifying IPv4 Routing table on Router {}'.format(curRouter))

        assertmsg = "Router '{}' routes mismatch".format(curRouter)
        assert topotest.json_cmp(actual, expected) is None, assertmsg


def test_verify_ipv6_routing_table():
    "Dummy test that just calls mininet CLI so we can interact with the build."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    listRouters = []
    for routerN in topo['routers'].items():
        listRouters.append(routerN[0])
    listRouters.sort()

    for curRouter in listRouters:
        filename = '{0}/testdata/{1}_ipv6_routes.json'.format(CWD, curRouter)
        expected = json.loads(open(filename, 'r').read())
        actual = tgen.gears[curRouter].vtysh_cmd('show ipv6 route json', isjson=True)

        logger.info('verifying IPv6 Routing table on Router {}'.format(curRouter))

        assertmsg = "Router '{}' routes mismatch".format(curRouter)
        assert topotest.json_cmp(actual, expected) is None, assertmsg


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
