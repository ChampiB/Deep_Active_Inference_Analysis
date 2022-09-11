import abc


class AgentInterface(abc.ABC):

    def __init__(self, name):
        self.name = name
        self.template


    def get_template(self):
        return self.template
