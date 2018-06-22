#!/usr/bin/env python

#
# test_fabricd_butterfly_08_unnumbered_expanding.py.py
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
test_fabricd_butterfly_08_unnumbered_expanding.py: Test for OpenFabric Butterfly Topo.

Unnumbered topology

Test steps
- Create 6x5 topology (A-F, 0-4), but start only 4x5 topology 
  with B0 and G4 as tier 0 (other routers stay disabled)
- Verify for topology to converge
- Verify tier on all routers
- Verify routing table on all routers
- Enable remaining routers 
- Verify for topology to re-converge
- Verify tier on all routers
- Verify routing table on all routers
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

from lib.fabric_helper import *


fatal_error = ""

# Read Topology from file
topoJson = open('{0}/topo/unnumbered/butterfly_topo_expanding.json'.format(CWD)).read()
topo = json.loads(topoJson)


class FoldedClosTopo(Topo):
    "Test topology builder"
    def build(self, *_args, **_opts):
        "Build function"
        tgen = get_topogen(self)

        build_topo_from_json(tgen, topo)


def setup_module(mod):
    "Sets up the pytest environment"
    # This function initiates the topology build with Topogen...
    tgen = Topogen(FoldedClosTopo, mod.__name__)
    # ... and here it calls Mininet initialization functions.
    tgen.start_topology()

    topo['openfabric_net_counter'] = 1

    configure_fabric_routers(tgen, topo)

    # After loading the configurations, this function starts configured daemons.
    tgen.start_router()


def teardown_module(mod):
    "Teardown the pytest environment"
    tgen = get_topogen()

    # This function tears down the whole topology.
    tgen.stop_topology()


# def test_call_mininet_cli():
#     "Dummy test that just calls mininet CLI so we can interact with the build."
#     tgen = get_topogen()
#     # Don't run this test if we have any failure.
#     if tgen.routers_have_failure():
#         pytest.skip(tgen.errors)

#     logger.info('calling mininet CLI')
#     tgen.mininet_cli()


def test_check_convergence():
    "Verifies OpenFabric Network has converged by checking for Tier"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    if not wait_fabric_convergence(tgen, 'g2'):
        fatal_error = 'Topology failed to converge'
        raise AssertionError(fatal_error)


def test_verify_tier_level():
    "Verifies correct OpenFabric Tier discovered for each router."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    errors = verify_tier_levels(tgen, topo, [0, 1, 2, 1, 0])

    if errors != "":
        errors.rstrip()
        fatal_error = 'Tier level calculation failed'
        raise AssertionError(errors)


def test_verify_ipv4_routing_table_before_expaning():
    "Test IPv4 Routing table."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes_before_expand.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv4', filename, loopback_only=True)

    if fatal_error != '':
        raise AssertionError(fatal_error)


def test_verify_ipv6_routing_table_before_expaning():
    "Test IPv6 Routing table."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes_before_expand.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv6', filename, loopback_only=True)

    if fatal_error != '':
        raise AssertionError(fatal_error)


def test_add_expansion():
    "Start disabled routers"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    # Get list of previously disabled routers
    stoppedRouters = []
    for routerN in topo['routers'].items():
        # Select routers NOT yet started
        if topo['routers'][routerN[0]]['started'] == 0:
            stoppedRouters.append(routerN[0])
    stoppedRouters.sort()

    configure_fabric_routers(tgen, topo, stoppedRouters)

    # Start additional routers
    for curRouter in stoppedRouters:
        tgen.gears[curRouter].start()
        topo['routers'][curRouter]['started'] = 1


def test_check_convergence_expanded():
    "Verifies OpenFabric Network has converged by checking for Tier"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    if not wait_fabric_convergence(tgen, 'l2'):
        fatal_error = 'Expanded Topology failed to converge'
        raise AssertionError(fatal_error)


def test_verify_tier_level_expanded():
    "Verifies correct OpenFabric Tier discovered for each router."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    errors = verify_tier_levels(tgen, topo, [0, 1, 2, 1, 0])

    if errors != "":
        errors.rstrip()
        fatal_error = 'Tier level calculation failed'
        raise AssertionError(errors)


def test_verify_ipv4_routing_table_after_expand():
    "Test IPv4 Routing table after expanding topo"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes_after_expand.json'
    errors = verify_routing_table(tgen, topo, 'ipv4', filename, loopback_only=True)

    if errors != '':
        raise AssertionError(errors)


def test_verify_ipv6_routing_table_after_expand():
    "Test IPv6 Routing table."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes_after_expand.json'
    errors = verify_routing_table(tgen, topo, 'ipv6', filename, loopback_only=True)

    if errors != '':
        raise AssertionError(errors)


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
