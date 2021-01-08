import argparse
import logging
import os
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from common.common_functionalities import normalize_scheduling_probabilities, create_input_file, copy_input_files, \
    get_ingress_nodes_and_cap
from siminterface.simulator import Simulator
from spinterface import SimulatorAction
from tqdm import tqdm

log = logging.getLogger(__name__)
DATETIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


def get_placement(nodes_list, sf_list):
    """  places each sf on each node of the network with some capacity

    Parameters:
        nodes_list
        sf_list

    Returns:
        a Dictionary with:
            key = nodes of the network
            value = list of all the SFs on the node
    """
    placement = defaultdict(list)
    for node in nodes_list:
        placement[node] = sf_list
    return placement


def get_schedule(nodes_list, nodes_with_cap, sf_list, sfc_list):
    """  return a dict of schedule for each node of the network
       '''
        Schedule is of the following form:
            schedule : dict
                {
                    'node id' : dict
                    {
                        'SFC id' : dict
                        {
                            'SF id' : dict
                            {
                                'node id' : float (Inclusive of zero values)
                            }
                        }
                    }
                }
        '''
    Parameters:
        nodes_list
        sf_list
        sfc_list

    Returns:
         schedule of the form shown above
    """
    schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    for outer_node in nodes_list:
        for sfc in sfc_list:
            for sf in sf_list:
                # all 0's list
                uniform_prob_list = [0 for _ in range(len(nodes_with_cap))]
                # Uniformly distributing the schedules between all nodes
                uniform_prob_list = normalize_scheduling_probabilities(uniform_prob_list)
                for inner_node in nodes_list:
                    if inner_node in nodes_with_cap:
                        schedule[outer_node][sfc][sf][inner_node] = uniform_prob_list.pop()
                    else:
                        schedule[outer_node][sfc][sf][inner_node] = 0
    return schedule


def parse_args():
    parser = argparse.ArgumentParser(description="Load Balance Algorithm")
    parser.add_argument('-i', '--iterations', required=False, default=10, dest="iterations", type=int)
    parser.add_argument('-s', '--seed', required=False, dest="seed", type=int)
    parser.add_argument('-n', '--network', required=True, dest='network')
    parser.add_argument('-sf', '--service_functions', required=True, dest="service_functions")
    parser.add_argument('-c', '--config', required=True, dest="config")
    return parser.parse_args()


def main():
    # Parse arguments
    args = parse_args()
    if not args.seed:
        args.seed = random.randint(1, 9999)
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("coordsim").setLevel(logging.WARNING)

    # Creating the results directory variable where the simulator result files will be written
    network_stem = os.path.splitext(os.path.basename(args.network))[0]
    service_function_stem = os.path.splitext(os.path.basename(args.service_functions))[0]
    simulator_config_stem = os.path.splitext(os.path.basename(args.config))[0]

    results_dir = f"{PROJECT_ROOT}/results/{network_stem}/{service_function_stem}/{simulator_config_stem}" \
                  f"/{DATETIME}_seed{args.seed}"

    # creating the simulator
    simulator = Simulator(os.path.abspath(args.network),
                          os.path.abspath(args.service_functions),
                          os.path.abspath(args.config), test_mode=True, test_dir=results_dir)
    init_state = simulator.init(args.seed)
    log.info("Network Stats after init(): %s", init_state.network_stats)
    nodes_list = [node['id'] for node in init_state.network.get('nodes')]
    nodes_with_capacity = []
    for node in simulator.network.nodes(data=True):
        if node[1]['cap'] > 0:
            nodes_with_capacity.append(node[0])
    sf_list = list(init_state.service_functions.keys())
    sfc_list = list(init_state.sfcs.keys())
    ingress_nodes = get_ingress_nodes_and_cap(simulator.network)
    # we place every sf on each node of the network with some capacity, so placement is calculated only once
    placement = get_placement(nodes_with_capacity, sf_list)
    # Uniformly distributing the schedule for all Nodes with some capacity
    schedule = get_schedule(nodes_list, nodes_with_capacity, sf_list, sfc_list)
    # Since the placement and the schedule are fixed , the action would also be the same throughout
    action = SimulatorAction(placement, schedule)
    # iterations define the number of time we wanna call apply()
    log.info(f"Running for {args.iterations} iterations...")
    for i in tqdm(range(args.iterations)):
        _ = simulator.apply(action)
    # We copy the input files(network, simulator config....) to  the results directory
    copy_input_files(results_dir, os.path.abspath(args.network), os.path.abspath(args.service_functions),
                     os.path.abspath(args.config))
    # Creating the input file in the results directory containing the num_ingress and the Algo used attributes
    create_input_file(results_dir, len(ingress_nodes), "LB")
    log.info(f"Saved results in {results_dir}")


if __name__ == '__main__':
    main()
