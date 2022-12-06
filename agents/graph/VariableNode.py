from agents.graph.Node import Node


class VariableNode(Node):
    """
    Class representing a variable node in the factor graph.
    """

    def __init__(self, name):
        """
        Construct a node of the factor graph.
        :param name: the node name.
        """
        super().__init__(name, {})

    def compute_message(self, dest_name, use_default_val=True):
        """
        Compute the message toward the destination node
        :param dest_name: the name of the destination node
        :param use_default_val: whether to replace None values by ones
        :return: the message to the destination node
        """
        out_msg = None
        for name, message in self.in_messages.items():
            if dest_name == name:
                continue
            out_msg = message if out_msg is None else out_msg * message
        max_elem = out_msg.max()
        if out_msg is None:
            return None
        elif max_elem == 0:
            return out_msg
        else:
            return out_msg / out_msg.max()
