class MCTS:
    """
    Class implementing the Monte-Carlo tree search algorithm.
    """

    def __init__(self, exp_const, n_samples):
        """
        Construct the MCTS algorithm
        :param exp_const: the exploration constant of the MCTS algorithm
        :param n_samples: the number of samples
        """
        self.exp_const = exp_const
        self.n_samples = n_samples

    def select_node(self, root):
        """
        Select the node to be expanded.
        :param root: the root of the tree.
        """
        current = root
        while len(current.children) != 0:
            current = max(current.children, key=lambda x: x.uct(self.exp_const))
        return current

    @staticmethod
    def expansion(node):
        """
        Expand the node passed as parameters
        :param node: the node to be expanded
        """
        nodes = []
        for action in range(0, node.n_actions):
            nodes.append(node.p_step(action))
        return nodes

    def evaluation(self, nodes):
        """
        Evaluate the input nodes
        :param nodes: the nodes to be evaluated
        """
        for node in nodes:
            node.cost = node.efe(self.n_samples)

    def propagation(self, nodes):
        """
        Propagate the cost in the tree and update the number of visits.
        :param nodes: the nodes that have been expanded.
        """
        best_child = min(nodes, key=lambda x: x.efe(self.n_samples))
        cost = best_child.cost
        current = best_child.parent
        while current is not None:
            current.cost += cost
            current.visits += 1
            current = current.parent
