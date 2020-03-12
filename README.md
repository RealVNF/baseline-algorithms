# baseline-algorithms
Baseline algorithms for coordination of chained VNFs. Includes Non-RL algorithms (Random Schedule, Shortest Path, & Load Balance).

## Project structure

* `src/algorithms`: Random Schedule, Shortest Path and Load Balance algorithm implementation.


## Algorithms

### Random Schedule

* Places all VNFs on all nodes of the networks
* Creates random schedules for each source node, each SFC, each SF , each destination node
* All the schedules for an SF sum-up to 1

### Load Balance algorithm

Always returns equal distribution for all nodes and SFs. Places all SFs everywhere.

### Shortest Path algorithm

Based on network topology, SFC, and ingress nodes, calculates for each ingress node:
* Puts 1st VNF on ingress, 2nd VNF on closest neighbor, 3rd VNF again on closest neighbor of 2nd VNF and so on.
* Stores placement of VNFs and avoids placing 2 VNFs on the same node as long as possible. If all nodes are filled,
  continue placing a 2nd VNF on all nodes, but avoid placing 3 VNFs and so on.
* Avoids nodes without any capacity at all (but ignores current utilization).

## Installation

Requires [Python 3.6](https://www.python.org/downloads/release/) and (recommended) [venv](https://docs.python.org/3/library/venv.html).

```bash
python setup.py install
```


## Usage

### How to run the Random Schedule algorithm against the Simulator

```bash
rs -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```
For more information look at the [README](src/algorithms/README.md) of the Random Schedule.

### How to run the Load Balance algorithm against the Simulator

```bash
lb -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```

### How to run the Load Balance algorithm against the Simulator

```bash
sp -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```

### Using the simultaneous script to run multiple experiments:

From [scripts directory](scripts) configure the following files:
- [network_files](scripts/network_files.txt): 1 network file location per line
- [config_files](scripts/config_files.txt): 1 simulator config. file location per line
- [service_files](scripts/service_files.txt): 1 SFC file location per line
- [30seeds](scripts/30seeds.txt): 1 seed per run of the simulator. By default using 30 seeds. Add/Remove as per requirement

From the main directory (where the README.md file is) using a Terminal run:
```bash
bash scripts/run_simultaneous
```

This would link the paths in the `network_files`, `config_files`, and `service_files`, as per line number and then run them for all the seeds within the `30seeds` file. E.g: Network file location at line no. 1 of `network_files` + Simulator Config file location at line no. 1 of `config_files` + SFC file location at line no. 1, would be run for all the seeds within the `30seeds` file. Similary for line numbers 2,3, and so on.
