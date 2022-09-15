import json
import os
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory


class CreationHMM(tk.Frame):
    """
    A Hidden Markov Model creation form
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
        self.networks, self.networks_values = LabelFrameFactory.create(self, theme="networks", params={
            "scrollbar": scrollbar,
            "encoder": "Conv64",
            "decoder": "Conv64",
            "transition": "LinearRelu3x100"
        })
        self.networks.grid(row=0, column=0, padx=5, pady=15, sticky="nsew")

        # Create action selection label frame
        self.action_selection = LabelFrameFactory.create(
            self, theme="action_selection", params={
                "scrollbar": scrollbar,
                "default_value": "RandomActions"
            }
        )
        self.action_selection.grid(row=1, column=0, pady=15, sticky="nsew")

        # Create the hyper-parameters label frame
        self.hyper_parameters, self.hyper_parameters_values = LabelFrameFactory.create(
            self, theme="hyper_parameters",
            params={
                "scrollbar": scrollbar,
                "beta": "1.0",
                "queue_capacity": "50000",
                "vfe_lr": "0.0001",
                "n_states": "10"
            }
        )
        self.hyper_parameters.grid(row=2, column=0, pady=15, sticky="nsew")

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
        networks = {key: values[value.get()] for key, (value, values) in self.networks_values.items()}
        networks = {
            key: {"module": str(value.__module__), "class": str(value.__name__)} for key, value in networks.items()
        }
        strategy = LabelFrameFactory.get_strategy(self.action_selection)
        hp_values = {key: value.get() for key, value in self.hyper_parameters_values.items()}
        json.dump({
            "name": self.parent.agent_name_entry.get(),
            "module": "agents.impl.HMM",
            "class": "HMM",
            **networks,
            "strategy": strategy,
            **hp_values
        }, file, indent=2)

        # Refresh project tree and display empty frame in the project page
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")
