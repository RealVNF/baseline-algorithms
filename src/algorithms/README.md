# random-scheduling-algo

Random Scheduling coordinator for VNF placement and scheduling. Integrated with the NFV flow simulator.

## Coordination

Simple Random Scheduling coordinator for placement and scheduling/load balancing of VNFs and flows:

* Place all VNFs at all nodes
* Schedule flows randomly in each iteration

## Purpose

* Test, debug integration with the [NFV flow simulator](https://github.com/RealVNF/coordination-simulation)
* Develop standard procedure for writing coordination algorithms that integrate with the simulator
* Baseline coordinator for comparison with future coordinators


## Setup

Install [Python 3.6](https://www.python.org/downloads/release/) and [venv](https://docs.python.org/3/library/venv.html) modules.

```bash
# clone this repo and enter dir
git clone git@github.com:RealVNF/coord-interface.git
cd coord-interface

# create and activate virtual environment
## On Windows
python -m venv venv
.\venv\Scripts\activate

## On Linux and macOS
python3 -m venv venv
source venv/bin/activate

# install package
pip install .
```

## Usage

```
usage: rs [-h] [-i ITERATIONS] [-s SEED] -n NETWORK -sf
                   SERVICE_FUNCTIONS -c CONFIG

Dummy Coordinator

optional arguments:
  -h, --help            show this help message and exit
  -i ITERATIONS, --iterations ITERATIONS
  -s SEED, --seed SEED
  -n NETWORK, --network NETWORK
  -sf SERVICE_FUNCTIONS, --service_functions SERVICE_FUNCTIONS
  -c CONFIG, --config CONFIG
```
Use the following command as an example (from within dummy-coordinator project folder):
```bash
rs -n "res/networks/triangle.graphml" \
            -sf "res/service_functions/abc.yaml" \
            -c "res/config/sim_config.yaml" \
            -i 200
```

This will run the random-scheduling coordinator and call the `apply()` of the sim-interface for 200 times.
The Network metrics would be logged at the `INFO` level.
