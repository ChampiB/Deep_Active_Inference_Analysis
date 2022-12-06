from agents.graph.Node import Node
from agents.inference.Operators import Operators
import torch
import numpy as np


class FactorNode(Node):
    """
    Class representing a factor node in the factor graph.
    """

    def __init__(self, name, neighbours, params):
        """
        Construct a factor node.
        :param name: the node's name.
        :param neighbours: the list of neighbours' name.
        :param params: the parameters of the factor graph.
        """
        super().__init__(name, neighbours)
        self.params = params

    def compute_message(self, dest_name, use_default_val=False):
        """
        Compute the message toward the destination node
        :param dest_name: the name of the destination node
        :param use_default_val: whether to replace None values by ones
        :return: the message to the destination node
        """
        out_msg = self.params
        if out_msg is None:
            raise Exception("In FactorNode::compute_message, {}.param is None.".format(self.name))

        for name in reversed(self.neighbours):
            if dest_name == name:
                continue
            i = self.neighbours.index(name)

            # Get message value
            if type(self.in_messages[name]) == np.ndarray:
                self.in_messages[name] = torch.from_numpy(self.in_messages[name])
            message = self.in_messages[name]
            if use_default_val and message is None:
                self.in_messages[name] = torch.ones(out_msg.shape[i])
                message = self.in_messages[name]

            # Average the output message across the i-th dimension
            out_msg = Operators.average(out_msg, message, [i])
        max_elem = out_msg.max()
        if out_msg is None:
            return None
        elif max_elem == 0:
            return out_msg
        else:
            return out_msg / out_msg.max()
