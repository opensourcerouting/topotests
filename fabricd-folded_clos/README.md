# Tests for a OpenFabric Folded Clos Topology

All tests are dual-stack IPv4 and IPv6

## Test script 01 - Numbered Basic functionality
`test_fabricd_folded_clos_01_numbered.py`  - Numbered topology

### Topology
![Folded Clos Topology](OpenFabric_Folded_Clos.png "Folded Clos Topology")

### Test steps
- Bring up basic 4x5 topo	with A0 and D3 as tier 0 marked
- Verify for topology to converge
- Verify tier on all routers
- Verify routing table on all routers
- stop A1, verify routing table
- restart A1
- stop B2, verify routing table
- restart B2
- stop C3, verify routing table
- restart C3
- stop D3, verify routing table
- restart D3
- Verify routing table on all routers

## Test script 02 - Numbered Single Node marked as Tier 0
`test_fabricd_folded_clos_02_numbered_single_tier0.py` - Numbered topology

### Topology
![Folded Clos Topology](OpenFabric_Folded_Clos.png "Folded Clos Topology")

### Test steps
- Bring up basic 4x5 topo - with only A0 as tier 0 marked
- Verify for topology **not** to converge (can't converge with a single Tier0 marked node)
- Mark D3 as a 2nd tier 0
- Verify for topology to converge
- Verify tier on all routers
- Verify routing table on all routers

## Test script 03 - Numbered Many nodes marked as Tier 0
`test_fabricd_folded_clos_03_numbered_multiple_tier0.py` - Numbered topology

### Topology
![Folded Clos Topology](OpenFabric_Folded_Clos.png "Folded Clos Topology")

### Test steps
- Bring up basic 4x5 topo - with A0, B0, C0, D0, A4, B4, C4, D4 as tier 0 marked
- Verify for topology to converge
- Verify tier on all routers
- Verify routing table on all routers

## Test script 04 - Numbered Expanding running topology
`test_fabricd_folded_clos_04_numbered_expanding.py` - Numbered topology

### Topology
![Folded Clos Expanding Topology](OpenFabric_Folded_Clos_expanded.png "Folded Clos Expanding Topology")

### Test steps
- Create 6x5 topology (A-F, 0-4), but start only 4x5 topology with A0 and D3 and D3 as tier 0 (other routers stay disabled)
- Verify for topology to converge
- Verify tier on all routers
- Verify routing table on all routers
- Enable remaining routers (E0, F0, E1, F1, E2, F2 etc)
- Verify for topology to re-converge
- Verify tier on all routers
- Verify routing table on all routers


## Test script 05 - Unnumbered Basic functionality
`test_fabricd_folded_clos_05_unnumbered.py`  - Unumbered topology

Same as Test script 01, but with unnumbered links. Each node only has numbered Loopback interface

## Test script 06 - Unumbered Single Node marked as Tier 0

`test_fabricd_folded_clos_06_unnumbered_single_tier0.py`  - Unumbered topology

Same as Test script 02, but with unnumbered links. Each node only has numbered Loopback interface


## Test script 07 - Unnumbered Many nodes marked as Tier 0
`test_fabricd_folded_clos_07_unnumbered_multiple_tier0.py`  - Unumbered topology

Same as Test script 03, but with unnumbered links. Each node only has numbered Loopback interface


## Test script 08 - Unnumbered Expanding running topology
`test_fabricd_folded_clos_08_unnumbered_expanding.py`  - Unumbered topology

Same as Test script 04, but with unnumbered links. Each node only has numbered Loopback interface

