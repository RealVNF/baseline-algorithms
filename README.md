[![Build Status](https://travis-ci.com/RealVNF/baseline-algorithms.svg?branch=cnsm2020)](https://travis-ci.com/RealVNF/baseline-algorithms)

# baseline-algorithms

Baseline algorithms for coordination of service mesh consisting of multiple microservices. Includes Non-RL algorithms (Random Schedule, Shortest Path, & Load Balance).

<p align="center">
  <img src="docs/realvnf_logo.png" height="150" hspace="30"/>
	<img src="docs/upb.png" width="200" hspace="30"/>
	<img src="docs/huawei_horizontal.png" width="250" hspace="30"/>
</p>

## Project structure

- `src/algorithms`: Random Schedule, Shortest Path and Load Balance algorithm implementation.

## Algorithms

### Random Schedule

- Places all VNFs on all nodes of the networks
- Creates random schedules for each source node, each SFC, each SF , each destination node
- All the schedules for an SF sum-up to 1

### Load Balance algorithm

Always returns equal distribution for all nodes having capacities and SFs. Places all SFs on all nodes having some capacity.

### Shortest Path algorithm

Based on network topology, SFC, and ingress nodes, calculates for each ingress node:

- Puts 1st VNF on ingress, 2nd VNF on closest neighbor, 3rd VNF again on closest neighbor of 2nd VNF and so on.
- Stores placement of VNFs and avoids placing 2 VNFs on the same node as long as possible. If all nodes are filled,
  continue placing a 2nd VNF on all nodes, but avoid placing 3 VNFs and so on.
- Avoids nodes without any capacity at all (but ignores current utilization).

## Installation

### Create a venv

On your local machine:

```bash
# clone this repo and enter dir
git clone --single-branch --branch cnsm2020 git@github.com:RealVNF/baseline-algorithms.git
cd baseline-algorithms
# create venv once
python3.6 -m venv ./venv
# activate the venv (always)
source venv/bin/activate
```

### Install dependencies from the main directory of the repo

```bash
pip install -r requirements.txt
```

This also installs the required [coord-sim](https://github.com/RealVNF/coord-sim/tree/cnsm2020) simulator and [common-utils](https://github.com/RealVNF/common-utils/tree/cnsm2020) package.

## Usage

### How to run the Random Schedule algorithm against the Simulator

```bash
rs -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```

### How to run the Load Balance algorithm against the Simulator

```bash
lb -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```

### How to run the Load Balance algorithm against the Simulator

```bash
sp -n "res/networks/triangle.graphml" -sf "res/service_functions/abc.yaml" -c "res/config/sim_config.yaml" -i 200
```

### Using the parallel script to run multiple experiments:

There is script provided in the `scripts` folder that utilizes the [GNU Parallel](https://www.gnu.org/software/parallel/) utility to run multiple experiments at the same time to speed up the process. It can run one algorithm at a time, so you need to choose the algo you wanna run at the beginning of the file.

From [scripts directory](scripts) configure the following files:

- [network_files](scripts/network_files.txt): 1 network file location per line
- [config_files](scripts/config_files.txt): 1 simulator config. file location per line
- [service_files](scripts/service_files.txt): 1 SFC file location per line
- [30seeds](scripts/30seeds.txt): 1 seed per run of the simulator. By default using 30 seeds. Add/Remove as per requirement

From the main directory (where the README.md file is) using a Terminal run:

```bash
bash scripts/run_parallel
```

## Acknowledgement

This project has received funding from German Federal Ministry of Education and Research ([BMBF](https://www.bmbf.de/)) through Software Campus grant 01IS17046 ([RealVNF](https://realvnf.github.io/)).

<p align="center">
	<img src="docs/software_campus.png" width="200"/>
	<img src="docs/BMBF_sponsored_by.jpg" width="250"/>
</p>
