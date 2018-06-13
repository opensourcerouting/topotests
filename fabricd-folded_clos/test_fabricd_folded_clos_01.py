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

from lib.fabric_helper import *

fatal_error = ""

# Read Topology from file
topoJson = open('{0}/clos_topo.json'.format(CWD)).read()
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


def test_check_convergence():
    "Verifies OpenFabric Network has converged by checking for Tier"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()

    if not wait_fabric_convergence(tgen, 'c2'):
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


def test_verify_ipv4_routing_table():
    "Test IPv4 Routing table."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv4', filename)

    if fatal_error != '':
        raise AssertionError(fatal_error)


def test_verify_ipv6_routing_table():
    "Test IPv6 Routing table."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv6', filename)

    if fatal_error != '':
        raise AssertionError(fatal_error)


def verify_table_with_router_disabled(selectedRouter):
    "Verify routing table with a router disabled"

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    delayTime = 30

    disable_router(selectedRouter)
    topo['routers'][selectedRouter]['started'] = 0

    logger.info('waiting {0}s after Router {1} is removed'.format(delayTime, selectedRouter))
    sleep(delayTime)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes_'+'{0}_shut.json'.format(selectedRouter)

    fatal_error = verify_routing_table(tgen, topo, 'ipv4', filename)
    if fatal_error != '':
        raise AssertionError(fatal_error)

    fatal_error = verify_routing_table(tgen, topo, 'ipv6', filename)
    if fatal_error != '':
        raise AssertionError(fatal_error)

    enable_router(selectedRouter)
    logger.info('waiting {0}s after Router {1} is restarted'.format(delayTime, selectedRouter))
    sleep(delayTime)

    return ""


def test_verify_routing_table_router_a1_disabled():
    "Shutdown router A1 and retest routing table"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    errors = verify_table_with_router_disabled('a1')
    if errors != "":
        raise AssertionError(errors)


def test_verify_routing_table_router_b2_disabled():
    "Shutdown router A1 and retest routing table"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    errors = verify_table_with_router_disabled('b2')
    if errors != "":
        raise AssertionError(errors)


def test_verify_routing_table_router_c3_disabled():
    "Shutdown router A1 and retest routing table"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    errors = verify_table_with_router_disabled('c3')
    if errors != "":
        raise AssertionError(errors)


def test_verify_routing_table_router_a0_disabled():
    "Shutdown router A0 and retest routing table"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    errors = verify_table_with_router_disabled('a0')
    if errors != "":
        raise AssertionError(errors)


def test_verify_routing_table_router_d4_disabled():
    "Shutdown router D4 and retest routing table"

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    errors = verify_table_with_router_disabled('d4')
    if errors != "":
        raise AssertionError(errors)


def test_verify_ipv4_routing_table_at_end():
    "Test IPv4 Routing table again."

    global fatal_error

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv4', filename)

    if fatal_error != '':
        raise AssertionError(fatal_error)


def test_verify_ipv6_routing_table_at_end():
    "Dummy test that just calls mininet CLI so we can interact with the build."

    global fatal_error

    # Skip if previous fatal error condition is raised
    if (fatal_error != ""):
        pytest.skip(fatal_error)

    tgen = get_topogen()
    # Don't run this test if we have any failure.
    if tgen.routers_have_failure():
        pytest.skip(tgen.errors)

    filename = '{0}/testdata/'.format(CWD)+'{0}_{1}_routes.json'
    fatal_error = verify_routing_table(tgen, topo, 'ipv6', filename)

    if fatal_error != '':
        raise AssertionError(fatal_error)


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
