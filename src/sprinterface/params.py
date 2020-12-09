import os
from shutil import copy2
from datetime import datetime
from coordsim.reader.reader import get_config, read_network, network_diameter
from networkx import DiGraph


class Params:
    def __init__(
        self,
        seed,
        sim_config,
        network,
        services,
        duration=10000,
        test_mode=None
    ):
        # Set the seed of the agent
        self.seed = seed
        # Check to enable test mode
        self.test_mode = test_mode

        # Store paths of config files
        self.sim_config_path = sim_config
        self.services_path = services
        self.network_path = network

        # Get the file stems for result path setup
        self.network_name = os.path.splitext(os.path.basename(self.network_path))[0]
        self.services_name = os.path.splitext(os.path.basename(self.services_path))[0]
        self.sim_config_name = os.path.splitext(os.path.basename(self.sim_config_path))[0]

        # Set training and testing durations
        self.duration = duration


        # Setup items from agent config file: Episode len, reward_metrics_history
        self.episode_length = self.duration  # 1000 arrivals per episode

        # Read the network file, store ingress and egress nodes
        net, self.ing_nodes, self.eg_nodes = read_network(self.network_path)
        self.network: DiGraph = net

        # Get current timestamps - for storing and identifying results
        datetime_obj = datetime.now()
        self.timestamp = datetime_obj.strftime('%Y-%m-%d_%H-%M-%S')
        self.training_id = f"{self.timestamp}_seed{self.seed}"

        # Create results structures
        self.create_result_dir()
        copy2(self.sim_config_path, self.result_dir)
        copy2(self.network_path, self.result_dir)
        copy2(self.services_path, self.result_dir)

        # ## ACTION AND OBSERVATION SPACE CALCULATIONS ## #

        # 1st: Get degree and diameter of network
        self.net_degree = self.get_max_degree()

        # Observation shape
        """ Observation space = (
            processing percentage +
            remaining_node_resource(neighbors+self) +
            remaining_outgoing_link_resources)
        """
        # Size of processing element: 1
        self.processing_size = 1
        # Size of distance to egress: 1
        self.dist_to_egress = 1
        # Size of ttl
        self.ttl_size = 1
        # Size of dr observation
        self.dr_size = 1
        # Node resource usage size = this node + max num of neighbor nodes
        self.node_resources_size = 1 + self.net_degree
        # Link resource usage size = max num of neighbor nodes
        self.link_resources_size = self.net_degree
        # Distance of neighbors to egress
        self.neighbor_dist_to_eg = self.net_degree
        # Component availability status = this node + max num of neighbor nodes
        self.vnf_status = 1 + self.net_degree

        # Observation shape = Above elements combined
        self.observation_shape = (
            self.processing_size +
            self.dist_to_egress +
            self.ttl_size +
            self.dr_size +
            self.vnf_status +
            self.node_resources_size +
            self.link_resources_size +
            self.neighbor_dist_to_eg,
        )

        # Action space limit (no shape in discrete actions):
        # The possible destinations for the flow = This node + max num of neighbor nodes
        self.action_limit = 1 + self.net_degree

    def get_max_degree(self):
        """ Get the max degree of the network """
        # Init degree to zero
        max_degree = 0
        # Iterate over all nodes in the network
        for node in self.network.nodes:
            # Get degree of node, compare with current max
            degree = self.network.degree(node)
            if degree > max_degree:
                max_degree = degree
        return max_degree

    def create_result_dir(self):
        # Set model path
        self.model_path = os.path.join(os.getcwd(), "results",
                                       self.network_name, self.services_name, self.sim_config_name,
                                       self.training_id, "model.zip")
        # Create a result directory structure
        if self.test_mode is not None:
            if self.test_mode is True:
                # We are in append-test
                self.result_dir = os.path.join(os.getcwd(), "results",
                                               self.network_name, self.services_name, self.sim_config_name,
                                               self.training_id, f"t_{self.training_id}")
                self.tb_log_name = os.path.join(self.network_name, self.services_name, self.sim_config_name,
                                                self.training_id, f"t_{self.training_id}")
            else:
                # We are in test mode
                self.result_dir = os.path.join(os.getcwd(), "results",
                                               self.network_name, self.services_name, self.sim_config_name,
                                               self.test_mode, f"t_{self.training_id}")
                self.tb_log_name = os.path.join(self.network_name, self.services_name, self.sim_config_name,
                                                self.test_mode, f"t_{self.training_id}")
                # Change model path
                self.model_path = os.path.join(os.getcwd(), "results",
                                               self.network_name, self.services_name, self.sim_config_name,
                                               self.test_mode, "model.zip")
        else:
            self.result_dir = os.path.join(os.getcwd(), "results",
                                           self.network_name, self.services_name, self.sim_config_name,
                                           self.training_id)
            self.tb_log_name = os.path.join(self.network_name, self.services_name, self.sim_config_name,
                                            self.training_id)

        os.makedirs(self.result_dir, exist_ok=True)
