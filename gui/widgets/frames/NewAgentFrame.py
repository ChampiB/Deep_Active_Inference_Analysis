import os
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory


class NewAgentFrame(tk.Frame):
    """
    A class allowing to create a new agent
    """

    def __init__(self, parent):
        """
        Constructor
        :param parent: parent widget
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Get all the agent classes
        self.agent_classes = self.get_all_agents_class()
        self.agent_names = list(self.agent_classes.keys())

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)

        # Ask the user to create an agent
        self.new_agent_label = LabelFactory.create(self, text="Create a new agent...", font_size=22, theme="dark")
        self.new_agent_label.grid(row=0, column=1, sticky="news", pady=50)

        # Create the general setting box
        self.general_settings = tk.LabelFrame(
            self, text="General",
            background=self.conf.colors["dark_gray"], highlightbackground=self.conf.colors["gray"],
            foreground=self.conf.colors["light_text"], font=(self.conf.font["name"], 14, self.conf.font["style"])
        )
        self.general_settings.grid(row=1, column=1, ipady=4, sticky="news")
        self.general_settings.columnconfigure(0, weight=1)
        self.general_settings.columnconfigure(1, weight=1)
        self.general_settings.columnconfigure(2, weight=1)
        self.general_settings.columnconfigure(3, weight=2)

        self.agent_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.agent_name_label.grid(row=1, column=1, pady=5, padx=5, sticky="nse")

        self.agent_name_entry = Entry(self.general_settings)
        self.agent_name_entry.grid(row=1, column=2, pady=5, padx=5, sticky="nsew")

        self.agent_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.agent_template_label.grid(row=2, column=1, pady=5, padx=5, sticky="nse")

        self.agent_template_combo_box = Combobox(self.general_settings, self.agent_names, self.change_agent_template)
        self.agent_template_combo_box.grid(row=2, column=2, pady=5, padx=5, sticky="nsew")
        self.change_agent_template()

    def change_agent_template(self, event=None):
        """
        Change the agent template
        :param event: unused
        """
        # TODO
        print(f"change_agent_template({self.agent_template_combo_box.get()})")

    def get_all_agents_class(self):
        """
        Retrieve all the available agents
        :return: all the available agents
        """
        # For each file in the agents directory
        agents = {}
        for file in os.listdir(self.conf.agents_directory + "impl/"):
            # Check that the file is a python file but not the init.py
            if not file.endswith('.py') or file == '__init__.py':
                continue

            # Get the class and module
            class_name = file[:-3]
            class_module = __import__("agents.impl." + class_name, fromlist=[class_name])

            # Get the agents' class
            module_dict = class_module.__dict__
            for obj in module_dict:
                if isinstance(module_dict[obj], type) and module_dict[obj].__module__ == class_module.__name__:
                    agents[class_name] = getattr(class_module, obj)
        return agents

    def refresh(self):
        """
        Refresh the new agent frame
        """
        pass
