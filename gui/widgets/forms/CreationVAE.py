import os
import json
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrame import LabelFrame


class CreationVAE(tk.Frame):
    """
    A Variational Auto-Encoder creation form
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
        self.networks = LabelFrame(self, text="Networks")
        CreationVAE.configure_columns(self.networks)
        self.networks.grid(row=0, column=0, pady=15, sticky="nsew")

        self.encoder_label = LabelFactory.create(self.networks, text="Encoder:", theme="dark")
        self.encoder_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.encoders = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/EncoderNetworks.py", "agents.networks."
        )
        self.encoder_combobox = Combobox(self.networks, values=list(self.encoders.keys()))
        self.encoder_combobox.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.decoder_label = LabelFactory.create(self.networks, text="Decoder:", theme="dark")
        self.decoder_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

        self.decoders = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/DecoderNetworks.py", "agents.networks."
        )
        self.decoder_combobox = Combobox(self.networks, values=list(self.decoders.keys()))
        self.decoder_combobox.grid(row=1, column=1, pady=(5, 15), padx=(5, 500), sticky="nsew")

        # Create action selection label frame
        self.action_selection = LabelFrame(self, text="Action Selection")
        CreationVAE.configure_columns(self.action_selection)
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
        CreationVAE.configure_columns(self.hyper_parameters)
        self.hyper_parameters.grid(row=2, column=0, pady=15, sticky="nsew")

        self.beta_label = LabelFactory.create(self.hyper_parameters, text="Beta:", theme="dark")
        self.beta_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.beta_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.beta_entry.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.queue_capacity_label = LabelFactory.create(self.hyper_parameters, text="Queue capacity:", theme="dark")
        self.queue_capacity_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")

        self.queue_capacity_entry = Entry(self.hyper_parameters, valid_input="int", help_message="50000")
        self.queue_capacity_entry.grid(row=1, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.vfe_lr_label = LabelFactory.create(
            self.hyper_parameters, text="Variational free energy learning rate:", theme="dark"
        )
        self.vfe_lr_label.grid(row=2, column=0, pady=(5, 15), padx=5, sticky="nse")

        self.vfe_lr_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.0001")
        self.vfe_lr_entry.grid(row=2, column=1, pady=(5, 15), padx=(5, 500), sticky="nsew")

        # Create the create button
        self.create_button = ButtonFactory.create(self, text="Create", theme="blue", command=self.create_vae)
        self.create_button.grid(row=3, column=0, pady=15, ipady=5, ipadx=5, sticky="nse")

    @staticmethod
    def configure_columns(widget):
        """
        Configure the widget columns
        :param widget: the widget
        """
        widget.columnconfigure(0, weight=3, uniform="labelframe")
        widget.columnconfigure(1, weight=5, uniform="labelframe")

    def create_vae(self):
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
        encoder = self.encoders[self.encoder_combobox.get()]
        decoder = self.decoders[self.decoder_combobox.get()]
        strategy = self.strategies[self.strategy_combobox.get()]
        json.dump({
            "name": file_name,
            "module": "agents.impl",
            "class": "VAE",
            "encoder": {
                "module": str(encoder.__module__),
                "class": str(encoder.__class__.__name__),
            },
            "decoder": {
                "module": str(decoder.__module__),
                "class": str(decoder.__class__.__name__),
            },
            "strategy": {
                "module": str(strategy.__module__),
                "class": str(strategy.__class__.__name__),
            },
            "beta": self.beta_entry.get(),
            "queue_capacity": self.queue_capacity_entry.get(),
            "vfe_lr": self.vfe_lr_entry.get()
        }, file)

        # Refresh project tree and display empty frame in the project page
        # TODO clear self
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")
