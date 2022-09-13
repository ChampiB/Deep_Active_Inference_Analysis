import json
import os
import tkinter as tk

from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrame import LabelFrame


class CreationDQN(tk.Frame):
    """
    A Deep Q-Network creation form
    """

    def __init__(self, parent):
        """
        Constructor
        :param parent: the parent widget
        """
        super().__init__(parent)
        self.conf = AnalysisConfig.instance
        self.config(background=self.conf.colors["dark_gray"])
        self.parent = parent
        self.project_page = parent.master.master.master.master

        # Create network label frame
        self.networks = LabelFrame(self, text="Network")
        CreationDQN.configure_columns(self.networks)
        self.networks.grid(row=0, column=0, pady=15, sticky="nsew")

        self.policy_label = LabelFactory.create(self.networks, text="Policy:", theme="dark")
        self.policy_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.policies = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/PolicyNetworks.py", "agents.networks."
        )
        self.policy_combobox = Combobox(self.networks, values=list(self.policies.keys()))
        self.policy_combobox.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        # Create action selection label frame
        self.action_selection = LabelFrame(self, text="Action Selection")
        CreationDQN.configure_columns(self.action_selection)
        self.action_selection.grid(row=1, column=0, pady=15, sticky="nsew")

        self.strategy_label = LabelFactory.create(self.action_selection, text="Strategy:", theme="dark")
        self.strategy_label.grid(row=0, column=0, pady=(5, 15), padx=5, sticky="nse")

        self.strategies = self.conf.get_all_classes(
            self.conf.agents_directory + "strategies/", "agents.strategies."
        )
        self.strategy_combobox = Combobox(self.action_selection, values=list(self.strategies.keys()))
        self.strategy_combobox.grid(row=0, column=1, pady=(5, 15), padx=(5, 500), sticky="nsew")

        # Create the hyper-parameters label frame
        self.hyper_parameters = LabelFrame(self, text="Hyper-parameters")
        CreationDQN.configure_columns(self.hyper_parameters)
        self.hyper_parameters.grid(row=2, column=0, pady=15, sticky="nsew")

        self.discount_factor_label = LabelFactory.create(self.hyper_parameters, text="Discount factor:", theme="dark")
        self.discount_factor_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.discount_factor_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.discount_factor_entry.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.n_steps_between_synchro_label = LabelFactory.create(
            self.hyper_parameters, text="Number steps between synchronisation of :", theme="dark"
        )
        self.n_steps_between_synchro_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.n_steps_between_synchro_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.n_steps_between_synchro_entry.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.queue_capacity_label = LabelFactory.create(self.hyper_parameters, text="Queue capacity:", theme="dark")
        self.queue_capacity_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")

        self.queue_capacity_entry = Entry(self.hyper_parameters, valid_input="int", help_message="50000")
        self.queue_capacity_entry.grid(row=1, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.lr_label = LabelFactory.create(
            self.hyper_parameters, text="Policy learning rate:", theme="dark"
        )
        self.lr_label.grid(row=2, column=0, pady=(5, 15), padx=5, sticky="nse")

        self.lr_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.0001")
        self.lr_entry.grid(row=2, column=1, pady=(5, 15), padx=(5, 500), sticky="nsew")

        # Create the create button
        self.create_button = ButtonFactory.create(self, text="Create", theme="blue", command=self.create_dqn)
        self.create_button.grid(row=3, column=0, pady=15, ipady=5, ipadx=5, sticky="nse")

    @staticmethod
    def configure_columns(widget):
        """
        Configure the widget columns
        :param widget: the widget
        """
        widget.columnconfigure(0, weight=3, uniform="labelframe")
        widget.columnconfigure(1, weight=5, uniform="labelframe")

    def create_dqn(self):
        """
        Create the agent file on the file system
        """
        agents_directories = self.conf.projects_directory + self.project_page.project_name + "/agents/"
        file_name = self.parent.agent_name_entry.get() + ".json"

        # Check that the project does not exist
        if file_name in os.listdir(agents_directories):
            print(f"Agent '{file_name}' already exist.")
            return

        # Write the description of the new agent on the filesystem
        file = open(agents_directories + file_name, "a")
        policy = self.policies[self.policy_combobox.get()]
        strategy = self.strategies[self.strategy_combobox.get()]
        json.dump({
            "name": file_name,
            "module": "agents.impl",
            "class": "VAE",
            "policy": {
                "module": str(policy.__module__),
                "class": str(policy.__class__.__name__),
            },
            "strategy": {
                "module": str(strategy.__module__),
                "class": str(strategy.__class__.__name__),
            },
            "beta": self.discount_factor_entry.get(),
            "queue_capacity": self.queue_capacity_entry.get(),
            "vfe_lr": self.lr_entry.get()
        }, file)

        # Refresh project tree and display empty frame in the project page
        # TODO clear self
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")
