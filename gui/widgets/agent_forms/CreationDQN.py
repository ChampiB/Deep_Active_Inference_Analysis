import json
import os
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory
from gui.widgets.modern.ToolTip import ToolTip


class CreationDQN(tk.Frame):
    """
    A Deep Q-Network creation form
    """

    def __init__(self, parent, scrollbar):
        """
        Constructor
        :param parent: the parent widget
        :param scrollbar: the scrollbar widget allowing to scroll the creation form
        """
        super().__init__(parent)
        self.conf = AnalysisConfig.instance
        self.config(background=self.conf.colors["dark_gray"])
        self.parent = parent.master.master
        self.project_page = self.parent.master.master.master.master

        # Create network label frame
        self.networks = LabelFrameFactory.create(self, text="Network")
        CreationDQN.configure_columns(self.networks)
        self.networks.grid(row=0, column=0, pady=15, sticky="nsew")
        scrollbar.bind_wheel(self.networks)

        self.policy_label = LabelFactory.create(self.networks, text="Q-network:", theme="dark")
        self.policy_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.policy_label)

        self.policies = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/PolicyNetworks.py", "agents.networks."
        )
        self.policy_combobox = Combobox(self.networks, values=list(self.policies.keys()), default_value="Conv64")
        self.policy_combobox.grid(row=0, column=1, pady=(5, 15), padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.policy_combobox)

        # Create action selection label frame
        self.action_selection = LabelFrameFactory.create(
            self, theme="action_selection", params={"scrollbar": scrollbar}
        )
        self.action_selection.grid(row=1, column=0, pady=15, sticky="nsew")

        # Create the hyper-parameters label frame
        self.hyper_parameters = LabelFrameFactory.create(self, text="Hyper-parameters")
        CreationDQN.configure_columns(self.hyper_parameters)
        self.hyper_parameters.grid(row=2, column=0, pady=15, sticky="nsew")
        scrollbar.bind_wheel(self.hyper_parameters)

        self.discount_factor_label = LabelFactory.create(self.hyper_parameters, text="Discount factor:", theme="dark")
        self.discount_factor_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.discount_factor_label)

        self.discount_factor_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.9")
        self.discount_factor_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.discount_factor_entry)

        self.n_steps_between_synchro_label = LabelFactory.create(
            self.hyper_parameters, text="Number of steps between synchronisation:", theme="dark"
        )
        self.n_steps_between_synchro_tooltip = ToolTip(
            self.n_steps_between_synchro_label, "The synchronization is between the weights of the target and Q-network"
        )
        self.n_steps_between_synchro_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.n_steps_between_synchro_label)

        self.n_steps_between_synchro_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.n_steps_between_synchro_entry.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.n_steps_between_synchro_entry)

        self.queue_capacity_label = LabelFactory.create(self.hyper_parameters, text="Queue capacity:", theme="dark")
        self.queue_capacity_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.queue_capacity_label)

        self.queue_capacity_entry = Entry(self.hyper_parameters, valid_input="int", help_message="50000")
        self.queue_capacity_entry.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.queue_capacity_entry)

        self.lr_label = LabelFactory.create(
            self.hyper_parameters, text="Q-network's learning rate:", theme="dark"
        )
        self.lr_label.grid(row=3, column=0, pady=(5, 15), padx=5, sticky="nse")
        scrollbar.bind_wheel(self.lr_label)

        self.lr_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.0001")
        self.lr_entry.grid(row=3, column=1, pady=(5, 15), padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.lr_entry)

        # Create the create button
        self.create_button = ButtonFactory.create(self, text="Create", theme="blue", command=self.create_dqn)
        self.create_button.grid(row=3, column=0, pady=15, ipady=5, ipadx=5, sticky="nse")
        scrollbar.bind_wheel(self.create_button)

    @staticmethod
    def configure_columns(widget):
        """
        Configure the widget columns
        :param widget: the widget
        """
        widget.columnconfigure(0, weight=4, uniform="labelframe")
        widget.columnconfigure(1, weight=4, uniform="labelframe")
        widget.columnconfigure(2, weight=1, uniform="labelframe")

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
        strategy = LabelFrameFactory.get_strategy(self.action_selection)

        json.dump({
            "name": self.parent.agent_name_entry.get(),
            "module": "agents.impl.DQN",
            "class": "DQN",
            "policy": {
                "module": str(policy.__module__),
                "class": str(policy.__name__),
            },
            "strategy": strategy,
            "discount_factor": self.discount_factor_entry.get(),
            "n_steps_between_synchro": self.n_steps_between_synchro_entry.get(),
            "queue_capacity": self.queue_capacity_entry.get(),
            "policy_lr": self.lr_entry.get()
        }, file, indent=2)

        # Refresh project tree and display empty frame in the project page
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")
