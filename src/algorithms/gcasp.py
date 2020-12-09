# GCASP: Greedy Coordination with Adaptive Shortest Paths
# Code: https://github.com/CN-UPB/distributed-coordination/blob/master/src/algorithms/greedy/gpasp.py

import random
import copy

import click
import networkx as nx

from sprinterface.params import Params
from sprinterface.wrapper import SPRSimWrapper

from auxiliary.link import Link


class GCASP:
    def __init__(self, sim_wrapper):
        self.sim_wrapper = sim_wrapper
        self.simulator = sim_wrapper.simulator
        self.all_node_ids = list(self.simulator.network.nodes)
        self.network_degree = self.sim_wrapper.params.net_degree
        # copy of network for safe calculations without modifying real network
        self.network_copy = self.get_network_copy()

    def get_network_copy(self) -> nx.Graph:
        """
        Returns a deepcopy of the network topology and its current state. The returned network can be used by external
        algorithms for e.g. calculating shortest path based on their restricted knowledge, without altering the internal
        simulator state.
        """
        graph = nx.Graph()
        for n in self.simulator.network.nodes(data=True):
            graph.add_node(n[0], type=n[1]['type'], cap=n[1]['cap'], remaining_cap=n[1]['cap'],
                           available_sf=copy.deepcopy(n[1]['available_sf']))
        for e in self.simulator.network.edges(data=True):
            graph.add_edge(e[0], e[1], delay=e[2]['delay'], cap=e[2]['cap'], remaining_cap=e[2]['cap'])
        return graph

    def init_flow(self, flow):
        assert not hasattr(flow, 'metadata'), f"Flow {flow.flow_id} was already initialized by GCASP."
        flow.metadata = dict()
        flow.metadata['state'] = 'greedy'
        flow.metadata['target_node_id'] = flow.egress_node_id
        flow.metadata['blocked_links'] = []
        try:
            self.set_new_path(flow)
        except nx.NetworkXNoPath:
            flow.metadata['state'] = 'drop'
            flow.metadata['path'] = []

    def get_neighbor(self, node_id):
        """Return neighbor index for given node ID. Raises an error if the node_id is not a neighbor."""
        return self.sim_wrapper.node_and_neighbors.index(node_id)

    def set_new_path(self, flow):
        """
        Calculate and set shortest path to the target node defined by target_node_id, taking blocked links into account.
        """
        assert self.network_copy.number_of_edges() == self.simulator.params.network.number_of_edges(), \
            f'Pre edge count mismatch with internal state! Flow {flow.flow_id}'
        for link in flow.metadata['blocked_links']:
            self.network_copy.remove_edge(link[0], link[1])
        try:
            shortest_path = nx.shortest_path(self.network_copy, flow.current_node_id, flow['target_node_id'],
                                             weight='delay')
            shortest_path.pop(0)
            flow.metadata['path'] = shortest_path
        except nx.NetworkXNoPath:
            raise
        finally:
            for link in flow.metadata['blocked_links']:
                self.network_copy.add_edge(link[0], link[1], **link.attributes)
            assert self.network_copy.number_of_edges() == self.simulator.params.network.number_of_edges(), \
                'Post edge count mismatch with internal state!'

    def forward_flow(self, flow):
        """
        This function will handle the necessary actions to forward a flow from the associated node. A call to this
        function requires the flow to have a precomputed path. If a flow can be forwarded along th precomputed path
        the flow_forwarding_rules for the associated node will be set. If a flow cannot be forwarded, due missing link
        resources, all incident links will be checked and all unsuitable links will be added to the blocked link list
        of the flow. Subsequent a new path is attempted to calculate.
        """
        node_id = flow.current_node_id
        assert len(flow.metadata['path']) > 0
        next_neighbor_id = flow.metadata['path'].pop(0)
        edge = self.simulator.params.network[node_id][next_neighbor_id]

        # Can forward?
        if edge['remaining_cap'] >= flow.dr:
            # yes => forward to next neighbor on path
            return self.get_neighbor(next_neighbor_id)
        else:
            # no => adapt path
            # remove all incident links which cannot be crossed
            for incident_edge in self.simulator.params.network.edges(node_id, data=True):
                if (incident_edge[2]['remaining_cap'] - flow.dr) < 0:
                    link = Link(incident_edge[0], incident_edge[1], **incident_edge[2])
                    if link not in flow.metadata['blocked_links']:
                        flow.metadata['blocked_links'].append(link)
            try:
                # Try to find new path
                self.set_new_path(flow)
                assert len(flow.metadata['path']) > 0
                next_neighbor_id = flow.metadata['path'].pop(0)
                # Set forwarding rule
                return self.get_neighbor(next_neighbor_id)
            except nx.NetworkXNoPath:
                # all outgoing links are exhausted
                flow.metadata['state'] = 'drop'
                flow.metadata['path'] = []

        # default to random action
        print("No neighbor selected!")
        return random.randint(0, self.network_degree)

    def compute_action(self, state):
        """Copied and adjusted: https://github.com/CN-UPB/distributed-coordination/blob/master/src/algorithms/greedy/gpasp.py#L88"""
        # state: info about the incoming flow as well as node, link capacities, and distances of each neighbor
        flow = state['flow']
        node_rem_cap = state['rem_node_cap']
        link_rem_cap = state['rem_link_cap']
        dist_to_eg = state['dist_to_eg']

        # init metadata for flow, needed by GCASP
        if not hasattr(flow, 'metadata'):
            self.init_flow(flow)

        node_id = flow.current_node_id
        new_target = False
        # Is flow processed?
        if flow.current_position == len(flow.sfc_components):
            # Needs the state to change?
            if flow.metadata['state'] != 'departure':
                # yes => switch to departure, forward to egress node
                flow.metadata['state'] = 'departure'
                flow.metadata['target_node_id'] = flow.egress_node_id
                flow.metadata['blocked_links'] = []
                try:
                    self.set_new_path(flow)
                except nx.NetworkXNoPath:
                    flow.metadata['state'] = 'drop'
                    flow.metadata['path'] = []
        else:
            # no, not fully processed
            if node_id == flow.metadata['target_node_id']:
                # has flow arrived at targte node => set new random target distinct from the current node
                while flow.metadata['target_node_id'] == node_id:
                    flow.metadata['target_node_id'] = random.choice(self.all_node_ids)
                flow.metadata['blocked_links'] = []
                try:
                    self.set_new_path(flow)
                    new_target = True
                except nx.NetworkXNoPath:
                    flow.metadata['state'] = 'drop'
                    flow.metadata['path'] = []

        # Determine Flow state
        if flow.metadata['state'] == 'greedy':
            # One the way to the target, needs processing
            # Can flow be processed at current node?
            # TODO: adjust for other resource functions like here:
            #  https://github.com/CN-UPB/distributed-coordination/blob/master/src/algorithms/greedy/gpasp.py#L140
            if node_rem_cap[0] >= flow.dr:
                # process locally (neighbor 0 = this node)
                return 0
            else:
                # no => forward
                return self.forward_flow(flow)

        elif flow['state'] == 'departure':
            # Return to destination as soon as possible, no more processing necessary
            if node_id != flow.egress_node_id:
                return self.forward_flow(flow)

        # fall back to action 0
        print("No action selected, falling back to local processing!")
        return 0


    # def compute_action(self, state):
    #     """
    #     Select the next action according to GCASP algorithm.
    #
    #     :param state: Current simulator state for the given node.
    #     :return: Action where 0 means process flow locally, and i>0 means forward to neighbor i
    #     """
    #     # state: info about the incoming flow as well as node, link capacities, and distances of each neighbor
    #     flow = state['flow']
    #     node_rem_cap = state['rem_node_cap']
    #     link_rem_cap = state['rem_link_cap']
    #     dist_to_eg = state['dist_to_eg']
    #
    #     # init metadata for flow, needed by GCASP
    #     if not hasattr(flow, 'metadata'):
    #         self.init_flow(flow)
    #
    #     action = random.randint(0, len(dist_to_eg))
    #
    #     return action


# Click decorators
@click.command()
@click.argument('network', type=click.Path(exists=True))
@click.argument('simulator_config', type=click.Path(exists=True))
@click.argument('services', type=click.Path(exists=True))
@click.argument('duration', type=int)
@click.option('-s', '--seed', type=int, help="Set the simulator's seed", default=None)
def main(network, simulator_config, services, duration, seed):
    """
    SPR-RL DRL Scaling and Placement main executable
    """
    # Get or set a seed
    if seed is None:
        seed = random.randint(0, 9999)
    print(f"Starting heuristic with seed: {seed}")
    # Create the parameters object
    params = Params(seed, simulator_config, network, services, duration=duration, test_mode=True)

    simulator_wrapper = SPRSimWrapper(params=params)
    gcasp = GCASP(simulator_wrapper)
    state, sim_state = simulator_wrapper.init(seed)
    action = gcasp.compute_action(state)

    while sim_state.network_stats['total_flows'] < duration:
        state, sim_state = simulator_wrapper.apply(action)
        action = gcasp.compute_action(state)


if __name__ == "__main__":
    network = "res/networks/abilene_1-5in-1eg/abilene-in5-rand-cap0-2.graphml"
    services = "res/services/abc-start_delay0.yaml"
    sim_config = "res/simulator/mean-10-poisson.yaml"
    training_duration = "1000"
    main([network, sim_config, services, training_duration])
