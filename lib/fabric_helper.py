#!/usr/bin/env python

#
# fabric_helper.py
# Library of helper functions for fabric Topology Tests
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

import re
import json
import os
import sys

from time import sleep
from pprint import pprint
import ipaddr

# pylint: disable=C0413
# Import topogen and topotest helpers
from lib import topotest
from lib.topogen import Topogen, TopoRouter, get_topogen
from lib.topolog import logger

# Required to instantiate the topology builder class.
from mininet.topo import Topo

def fabric_row(routerName):
    """
    Returns the row number for the router.
    Calculation based on name a0 = row 0, a1 = row 1, b2 = row 2, z23 = row 23 etc
    """
    return int(routerName[1:])

def fabric_column(routerName):
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

    logger.info('Starting Router {}'.format(routerName))
    tgen.gears[routerName].start()

def build_topo_from_json(tgen, json_topo):
    "Builds topology from json structure"

    # Topology is built with direct P2P links, no switches between them

    # List of routers as read from structure.
    # Needed to mark which routers have the links already added
    listRouters = []

    # Create Topology - Step 1 STARTED routers:
    for routerN in sorted(json_topo['routers'].iteritems()):
        logger.info('Topo: Add router {}'.format(routerN[0]))
        # Create new router
        tgen.add_router(routerN[0])
        # Add to list of routers
        listRouters.append(routerN[0])

    # Keep interfaces consistent - need to process list of routers
    # in predicatable order
    listRouters.sort()

    if 'ipv4base' in json_topo:
        ipv4Next = ipaddr.IPv4Address(json_topo['link_ip_start']['ipv4'])
        ipv4Step = 2**(32-json_topo['link_ip_start']['v4mask'])
        if json_topo['link_ip_start']['v4mask'] < 31:
            ipv4Next += 1
    if 'ipv6base' in json_topo:
        ipv6Next = ipaddr.IPv6Address(json_topo['link_ip_start']['ipv6'])
        ipv6Step = 2**(128-json_topo['link_ip_start']['v6mask'])
        if json_topo['link_ip_start']['v6mask'] < 127:
            ipv6Next += 1

    # Create and save interface names as part of the link creation
    for router in listRouters:
        json_topo['routers'][router]['nextIfname'] = 0

    while listRouters != []:
        curRouter = listRouters.pop(0)
        for destRouter, data in sorted(json_topo['routers'][curRouter]['links'].iteritems()):
            if destRouter in listRouters:
                # print("   Add connection from ", curRouter, " to ", destRouter)
                json_topo['routers'][curRouter]['links'][destRouter]['interface'] = \
                    '{}-{}-eth{}'.format(curRouter, destRouter, json_topo['routers'][curRouter]['nextIfname'])
                json_topo['routers'][destRouter]['links'][curRouter]['interface'] = \
                    '{}-{}-eth{}'.format(destRouter, curRouter, json_topo['routers'][destRouter]['nextIfname'])
                json_topo['routers'][curRouter]['nextIfname'] += 1
                json_topo['routers'][destRouter]['nextIfname'] += 1
                tgen.gears[curRouter].add_link(
                    tgen.gears[destRouter],
                    json_topo['routers'][curRouter]['links'][destRouter]['interface'],
                    json_topo['routers'][destRouter]['links'][curRouter]['interface'])
                #print("   Added connection from ", curRouter,
                #      topo['routers'][curRouter]['links'][destRouter]['interface'],
                #      " to ", destRouter,
                #      topo['routers'][destRouter]['links'][curRouter]['interface'])
                #
                # Now assign IPv4 & IPv6 addresses where needed
                if 'ipv4' in json_topo['routers'][curRouter]['links'][destRouter]:
                    # IPv4 address on this link
                    if json_topo['routers'][curRouter]['links'][destRouter]['ipv4'] == 'auto':
                        # Need to assign addresses for this link
                        json_topo['routers'][curRouter]['links'][destRouter]['ipv4'] = \
                            '{}/{}'.format(ipv4Next, json_topo['link_ip_start']['v4mask'])
                        #ipv4Next += 1
                        json_topo['routers'][destRouter]['links'][curRouter]['ipv4'] = \
                            '{}/{}'.format(ipv4Next+1, json_topo['link_ip_start']['v4mask'])
                        ipv4Next += ipv4Step
                if 'ipv6' in json_topo['routers'][curRouter]['links'][destRouter]:
                    # IPv6 address on this link
                    if json_topo['routers'][curRouter]['links'][destRouter]['ipv6'] == 'auto':
                        # Need to assign addresses for this link
                        json_topo['routers'][curRouter]['links'][destRouter]['ipv6'] = \
                            '{}/{}'.format(ipv6Next, json_topo['link_ip_start']['v6mask'])
                        #ipv6Next += 1
                        json_topo['routers'][destRouter]['links'][curRouter]['ipv6'] = \
                            '{}/{}'.format(ipv6Next+1, json_topo['link_ip_start']['v6mask'])
                        ipv6Next = ipaddr.IPv6Address(int(ipv6Next)+ipv6Step)
        # Assign Loopback IPs
        if 'lo' in json_topo['routers'][curRouter]:
            if json_topo['routers'][curRouter]['lo']['ipv4'] == 'auto':
                json_topo['routers'][curRouter]['lo']['ipv4'] = \
                    '{}{}.{}/{}'.format(json_topo['lo_prefix']['ipv4'],
                                        fabric_row(curRouter), fabric_column(curRouter),
                                        json_topo['lo_prefix']['v4mask'])
            if json_topo['routers'][curRouter]['lo']['ipv6'] == 'auto':
                json_topo['routers'][curRouter]['lo']['ipv6'] = \
                    '{}{}:{}/{}'.format(json_topo['lo_prefix']['ipv6'],
                                        fabric_row(curRouter), fabric_column(curRouter),
                                        json_topo['lo_prefix']['v6mask'])
    # Print calculated Topology
    # pprint(topo, indent=2)


def configure_fabric_routers(tgen, json_topo, nodes=None):
    "Build configuration and apply to nodes. Default to all nodes \
     marked as started unless specified otherwise"

    if nodes == None:
        # Default - all routers marked as started in json
        # Get list of routers
        listRouters = []
        for routerN in json_topo['routers'].items():
            if json_topo['routers'][routerN[0]]['started'] == 1:
                listRouters.append(routerN[0])
    else:
        listRouters = nodes
        # Mark routers as started
        for curRouter in listRouters:
            json_topo['routers'][curRouter]['started'] = 1

    listRouters.sort()

    logger.info('Configuring nodes')

    for curRouter in listRouters:
        # Router is enabled - create config
        #
        # zebra.conf
        conffile = open('/tmp/zebra.conf', 'w')
        conffile.write('frr defaults traditional\n\n')
        conffile.write('hostname '+curRouter+'\n!\n')
        for destRouter, data in sorted(json_topo['routers'][curRouter]['links'].iteritems()):
            conffile.write('interface lo\n')
            conffile.write(' description Loopback Router '+curRouter+'\n')
            conffile.write(' ip address '+json_topo['routers'][curRouter]['lo']['ipv4']+'\n')
            conffile.write(' ipv6 address '+json_topo['routers'][curRouter]['lo']['ipv6']+'\n')
            conffile.write('!\n')
            conffile.write('interface '+
                           json_topo['routers'][curRouter]['links'][destRouter]['interface']+'\n')
            conffile.write(' description Link '+curRouter+' to '+destRouter+'\n')
            if 'ipv4' in json_topo['routers'][curRouter]['links'][destRouter]:
                # We have IPv4 address to configure
                conffile.write(' ip address '+
                               json_topo['routers'][curRouter]['links'][destRouter]['ipv4']+'\n')
            if 'ipv6' in json_topo['routers'][curRouter]['links'][destRouter]:
                # We have IPv6 address to configure
                conffile.write(' ipv6 address '+
                               json_topo['routers'][curRouter]['links'][destRouter]['ipv6']+'\n')
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
        for destRouter, data in sorted(json_topo['routers'][curRouter]['links'].iteritems()):
            conffile.write('interface '+
                           json_topo['routers'][curRouter]['links'][destRouter]['interface']+'\n')
            conffile.write(' ip router openfabric 1\n')
            conffile.write(' ipv6 router openfabric 1\n')
            conffile.write('!\n')

        conffile.write('router openfabric 1\n')
        conffile.write(' net 49.0000.0000.{:04x}.00\n'.format(json_topo['openfabric_net_counter']))
        json_topo['openfabric_net_counter'] += 1
        conffile.write(' lsp-gen-interval 2\n')
        conffile.write(' spf-delay-ietf init-delay 30 short-delay 500 long-delay 5000 holddown 5000 time-to-learn\n')
        if 'openfabric' in json_topo['routers'][curRouter]:
            if 'tier' in json_topo['routers'][curRouter]['openfabric']:
                conffile.write(' fabric-tier {}\n'.format(json_topo['routers'][curRouter]['openfabric']['tier']))
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
    os.remove('/tmp/zebra.conf')
    os.remove('/tmp/fabricd.conf')


def wait_fabric_convergence(tgen, testnode, timeout=60, log='Waiting for convergence (timeout {}s)'):
    "Waiting for fabric convergence on given node"

    logger.info('Waiting for convergence')

    # We verify the convergence by a "show openfabric database detail"
    # and checking that no node shows "Tier: undefined"
    # Only need to check a single node. using C2 in middle

    while timeout > 0:
        logger.info(log.format(timeout))
        database = tgen.gears[testnode].vtysh_cmd('show openfabric database detail', isjson=False)
        m = re.search('Tier: undefined', database, re.DOTALL)
        if m:
            # Still have undefined Tier levels in topology
            sleep(4)
            timeout -= 4
        else:
            # All tier levels computed
            break
    if timeout == 0:
        return False
    return True


def verify_tier_levels(tgen, json_topo, tiers):
    "Verify tier levels for started routers based on given tiers for the rows"

    # Tiers for topo, ie for a topo with Rows 0..4:
    # Row 0 and 4 are Tier 0, Row 1 and 3 are Tier 2 and Row 2 is Tier 2
    #   Example:  tiers = [0, 1, 2, 1, 0]

    logger.info('verifying Tier levels on all routers')

    errors = ''

    callingTest = os.path.basename(sys._current_frames().values()[0].f_back.f_globals['__file__'])
    callingProc = sys._getframe(1).f_code.co_name
    tiercalc_logfile = '/tmp/tierlevel.{0}.{1}.calc.txt'.format(callingTest, callingProc)

    with open(tiercalc_logfile, 'w') as tiercalc_log:
        for routerN in json_topo['routers'].items():
            if json_topo['routers'][routerN[0]]['started'] == 1:
                ofsummary = tgen.gears[routerN[0]].vtysh_cmd('show openfabric summary', isjson=False)
                tiercalc_log.write('## Router {}\n```\n'.format(routerN[0]))
                m = re.search('Tier: ([0-9a-z]+)', ofsummary, re.DOTALL)
                if m:
                    actualTier = m.group(1)
                    #logger.info('Router {} reports tier {}'.format(routerN[0], actualTier))
                    if str(tiers[fabric_row(routerN[0])]) != actualTier:
                        errors = errors+'Router {} shows tier {}, but expected tier {}\n'.format( \
                            routerN[0], actualTier, tiers[fabric_row(routerN[0])])
                        tiercalc_log.write('** Wrong Tier. Shows {0}, but expected {1} **\n```\n'.format(actualTier, tiers[fabric_row(routerN[0])]))
                    else:
                        tiercalc_log.write('Tier {0} is correct\n```\n'.format(actualTier))
                else:
                    errors = errors+'No Tier level found on Router {}'.format(routerN[0])
                    tiercalc_log.write('** NO Tier. Shows UNDEFINED, but expected {1} **\n```\n'.format(tiers[fabric_row(routerN[0])]))

                tiercalc_log.write(tgen.gears[routerN[0]].run('cat fabricd.log | grep OpenFabric | grep -Ei tier\|found\|T0'))
                tiercalc_log.write('```\n\n')

    if errors != "":
        errors.rstrip()
    else:
        os.remove(tiercalc_logfile)

    return errors


def verify_routing_table(tgen, json_topo, protocol, filename_format, loopback_only=False):
    "Verify Routing table for given protocol against json file"

    # Filename needs to have 2 params {0} and {1} in it.
    # First one is for router name, 2nd one for protocol (ipv4 or ipv6)

    listRouters = []
    for routerN in json_topo['routers'].items():
        if json_topo['routers'][routerN[0]]['started'] == 1:
            listRouters.append(routerN[0])
    listRouters.sort()

    for curRouter in listRouters:
        filename = filename_format.format(curRouter, protocol)
        expected = json.loads(open(filename, 'r').read())
        if loopback_only:
            # Drop all non-loopback routes and nexthop IP info
            routes_to_ignore = []
            for route in expected:
                if json_topo['lo_prefix']['ipv4'] not in route:
                    routes_to_ignore.append(route)
                elif json_topo['lo_prefix']['ipv6'] not in route:
                    routes_to_ignore.append(route)
                else:
                    for routeDetail in expected[route]:
                        for nexthop in routeDetail['nexthops']:
                            nexthop.pop('ip', None)
            for route in routes_to_ignore:
                expected.pop(route)

        # pprint(expected, indent=2)

        if protocol == 'ipv4':
            actual = tgen.gears[curRouter].vtysh_cmd('show ip route json', isjson=True)
        else:
            protocol = 'ipv6'
            actual = tgen.gears[curRouter].vtysh_cmd('show ipv6 route json', isjson=True)

        logger.info('verifying {0} Routing table on Router {1}'.format(protocol, curRouter))

        assertmsg = "Router '{}' routes mismatch".format(curRouter)
        if topotest.json_cmp(actual, expected) != None:
            return assertmsg

    return ""


def save_routing_table(tgen, json_topo, filename_format):
    "Save routing table"

    # Filename needs to have 2 params {0} and {1} in it.
    # First one is for router name, 2nd one for protocol (ipv4 or ipv6)

    # Skip further tests after this one
    fatal_error = "Saved routing table"

    listRouters = []
    for routerN in json_topo['routers'].items():
        if json_topo['routers'][routerN[0]]['started'] == 1:
            listRouters.append(routerN[0])
    listRouters.sort()

    for curRouter in listRouters:
        logger.info('getting Routing table on Router {}'.format(curRouter))

        #
        # IPv4 Routes
        #
        allroutes = tgen.gears[curRouter].vtysh_cmd('show ip route json', isjson=True)
        # pprint(allroutes, indent=2)

        # Remove some elements
        for route in allroutes:
            for routeDetail in allroutes[route]:
                routeDetail.pop('internalFlags', None)
                routeDetail.pop('internalStatus', None)
                routeDetail.pop('uptime', None)
                for nexthop in routeDetail['nexthops']:
                    nexthop.pop('interfaceIndex', None)

        #logger.info('saving Routing table for Router {}'.format(curRouter))

        with open(filename_format.format(curRouter, 'ipv4'), 'w') as route_file:
            #json.dump(allroutes, route_file)
            route_file.write(json.dumps(allroutes, indent=2))

        #
        # IPv6 Routes
        #
        allroutes = tgen.gears[curRouter].vtysh_cmd('show ipv6 route json', isjson=True)
        # pprint(allroutes, indent=2)

        logger.info('fixing routes on Router {}'.format(curRouter))

        # Remove some elements
        for route in allroutes:
            for routeDetail in allroutes[route]:
                routeDetail.pop('internalFlags', None)
                routeDetail.pop('internalStatus', None)
                routeDetail.pop('uptime', None)
                for nexthop in routeDetail['nexthops']:
                    nexthop.pop('interfaceIndex', None)
                    nexthop.pop('ip', None)

        #logger.info('saving Routing table for Router {}'.format(curRouter))

        with open(filename_format.format(curRouter, 'ipv6'), 'w') as route_file:
            #json.dump(allroutes, route_file)
            route_file.write(json.dumps(allroutes, indent=2))


