import argparse
import logging
import os
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from common.common_functionalities import normalize_scheduling_probabilities, create_input_file, \
    copy_input_files, get_ingress_nodes_and_cap
from siminterface.simulator import Simulator
from spinterface import SimulatorAction
from tqdm import tqdm

log = logging.getLogger(__name__)
DATETIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


def get_closest_neighbours(network, nodes_list):
    # Finding the closest neighbours to each node in the network. For each node of the network we maintain a list of
    # neighbours sorted in increasing order of distance to it.
    all_pair_shortest_paths = network.graph['shortest_paths']
    closest_neighbours = defaultdict(list)
    for source in nodes_list:
        neighbours = defaultdict(int)
        for dest in nodes_list:
            if source != dest:
                delay = all_pair_shortest_paths[(source, dest)][1]
                neighbours[dest] = delay
        sorted_neighbours = [k for k, v in sorted(neighbours.items(), key=lambda item: item[1])]
        closest_neighbours[source] = sorted_neighbours
    return closest_neighbours


def next_neighbour(index, num_vnfs_filled, node, placement, closest_neighbours, sf_list, nodes_cap):
    """
    Args:
        index: closest neighbours of 'node' is a list, index tells which closest neighbour to start looking from
        num_vnfs_filled: Tells the number of VNFs present on all nodes e.g: every node in the network has atleast 1 VNF,
                          some might have more than that. This tells us the minimum every node has
        node: The node whose closest neighbour is to be found
        placement: plaecement of VNFs in the entire network
        closest_neighbours: neighbours of each node in the network in the increasing order of distance
        sf_list: The VNFs in the network
        nodes_cap: Capacity of each node in the network

    Returns:
            The next closest neighbour of the requested node that:
            - has some capacity
            - while some of the nodes in the network have 0 VNFs it returns the closest neighbour that has 0 VNFs,
              If some nodes in the network has just 1 VNF, it returns the closest neighbour with just 1 VNF and so on
    """
    while len(placement[closest_neighbours[node][index]]) > num_vnfs_filled[0] or \
            nodes_cap[closest_neighbours[node][index]] == 0:
        index += 1
        if index == len(closest_neighbours[node]):
            num_vnfs_filled[0] += 1
            index = 0
        if num_vnfs_filled[0] > len(sf_list):
            index = 0
            break
    return index


def get_placement_schedule(network, nodes_list, sf_list, sfc_list, ingress_nodes, nodes_cap):
    """
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
        network: A NetworkX object
        nodes_list: all the nodes in the network
        sf_list: all the sf's in the network
        sfc_list: all the SFCs in the network, right now assuming to be just 1
        ingress_nodes: all the ingress nodes in the network
        nodes_cap: Capacity of each node in the network

    Returns:
        - a placement Dictionary with:
              key = nodes of the network
              value = list of all the SFs in the network
        - schedule of the form shown above
    """
    placement = defaultdict(list)
    schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float))))
    # Initializing the schedule for all nodes, for all SFs to 0
    for src in nodes_list:
        for sfc in sfc_list:
            for sf in sf_list:
                for dstn in nodes_list:
                    schedule[src][sfc][sf][dstn] = 0
    # Getting the closest neighbours to each node in the network
    closest_neighbours = get_closest_neighbours(network, nodes_list)

    # - For each Ingress node of the network we start by placing the first VNF of the SFC on it and then place the
    #  2nd VNF of the SFC on the closest neighbour of the Ingress, then the 3rd VNF on the closest neighbour of the node
    #  where we placed the 2nd VNF and so on.
    # - The closest neighbour is chosen based on the following criteria:
    #   - while some nodes in the network has 0 VNFs , the closest neighbour cannot be an Ingress node
    #   - The closest neighbour must have some capacity
    #   - while some of the nodes in the network have 0 VNFs it chooses the closest neighbour that has 0 VNFs,
    #     If some nodes in the network has just 1 VNF, it returns the closest neighbour with just 1 VNF and so on
    for ingress in ingress_nodes:
        node = ingress
        # We choose a list with just one element because a list is mutable in python and we want 'next_neighbour'
        # function to change the value of this variable
        num_vnfs_filled = [0]
        # Placing the 1st VNF of the SFC on the ingress nodes if the ingress node has some capacity
        # Otherwise we find the closest neighbour of the Ingress that has some capacity and place the 1st VNF on it
        if nodes_cap[ingress] > 0:
            if sf_list[0] not in placement[node]:
                placement[node].append(sf_list[0])
            schedule[node][sfc_list[0]][sf_list[0]][node] += 1
        else:
            # Finding the next neighbour which is not an ingress node and has some capacity
            index = next_neighbour(0, num_vnfs_filled, ingress, placement, closest_neighbours, sf_list, nodes_cap)
            while num_vnfs_filled[0] == 0 and closest_neighbours[ingress][index] in ingress_nodes:
                if index + 1 >= len(closest_neighbours[ingress]):
                    break
                index = next_neighbour(index + 1, num_vnfs_filled, ingress, placement, closest_neighbours,
                                       sf_list, nodes_cap)
            node = closest_neighbours[ingress][index]
            if sf_list[0] not in placement[node]:
                placement[node].append(sf_list[0])
            schedule[ingress][sfc_list[0]][sf_list[0]][node] += 1

        # For the remaining VNFs in the SFC we look for the closest neighbour and place the VNFs on them
        for j in range(len(sf_list) - 1):
            index = next_neighbour(0, num_vnfs_filled, node, placement, closest_neighbours, sf_list, nodes_cap)
            while num_vnfs_filled[0] == 0 and closest_neighbours[node][index] in ingress_nodes:
                if index + 1 >= len(closest_neighbours[node]):
                    break
                index = next_neighbour(index + 1, num_vnfs_filled, node, placement, closest_neighbours,
                                       sf_list, nodes_cap)
            new_node = closest_neighbours[node][index]
            if sf_list[j + 1] not in placement[new_node]:
                placement[new_node].append(sf_list[j + 1])
            schedule[node][sfc_list[0]][sf_list[j + 1]][new_node] += 1
            node = new_node

    # Since the sum of schedule probabilities for each SF of each node may not be 1 , we make it 1 using the
    # 'normalize_scheduling_probabilities' function.
    for src in nodes_list:
        for sfc in sfc_list:
            for sf in sf_list:
                unnormalized_probs_list = list(schedule[src][sfc][sf].values())
                normalized_probs = normalize_scheduling_probabilities(unnormalized_probs_list)
                for i in range(len(nodes_list)):
                    schedule[src][sfc][sf][nodes_list[i]] = normalized_probs[i]
    return placement, schedule


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
    # os.makedirs("logs", exist_ok=True)
    logging.basicConfig(level=logging.INFO)
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
    sf_list = list(init_state.service_functions.keys())
    sfc_list = list(init_state.sfcs.keys())
    ingress_nodes, nodes_cap = get_ingress_nodes_and_cap(simulator.network, cap=True)
    # getting the placement and schedule
    placement, schedule = get_placement_schedule(simulator.network, nodes_list, sf_list, sfc_list, ingress_nodes,
                                                 nodes_cap)
    # Since the placement and the schedule are fixed , the action would also be the same throughout
    action = SimulatorAction(placement, schedule)
    # iterations define the number of time we wanna call apply(); use tqdm for progress bar
    log.info(f"Running for {args.iterations} iterations...")
    for i in tqdm(range(args.iterations)):
        _ = simulator.apply(action)
        # log.info("Network Stats after apply() # %s: %s", i + 1, apply_state.network_stats)
    # We copy the input files(network, simulator config....) to  the results directory
    copy_input_files(results_dir, os.path.abspath(args.network), os.path.abspath(args.service_functions),
                     os.path.abspath(args.config))
    # Creating the input file in the results directory containing the num_ingress and the Algo used attributes
    create_input_file(results_dir, len(ingress_nodes), "SP")
    log.info(f"Saved results in {results_dir}")


if __name__ == '__main__':
    main()
