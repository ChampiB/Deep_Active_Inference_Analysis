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


class CreationCHMM(tk.Frame):
    """
    A Critical Hidden Markov Model creation form
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
        self.networks = LabelFrameFactory.create(self, text="Networks")
        CreationCHMM.configure_columns(self.networks)
        self.networks.grid(row=0, column=0, padx=5, pady=15, sticky="nsew")
        scrollbar.bind_wheel(self.networks)

        self.encoder_label = LabelFactory.create(self.networks, text="Encoder:", theme="dark")
        self.encoder_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.encoder_label)

        self.encoders = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/EncoderNetworks.py", "agents.networks."
        )
        self.encoder_combobox = Combobox(self.networks, values=list(self.encoders.keys()), default_value="Conv64")
        self.encoder_combobox.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.encoder_combobox)

        self.decoder_label = LabelFactory.create(self.networks, text="Decoder:", theme="dark")
        self.decoder_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.decoder_label)

        self.decoders = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/DecoderNetworks.py", "agents.networks."
        )
        self.decoder_combobox = Combobox(self.networks, values=list(self.decoders.keys()), default_value="Conv64")
        self.decoder_combobox.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.decoder_combobox)

        self.transition_label = LabelFactory.create(self.networks, text="Transition:", theme="dark")
        self.transition_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.transition_label)

        self.transitions = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/TransitionNetworks.py", "agents.networks."
        )
        self.transition_combobox = Combobox(self.networks, values=list(self.transitions.keys()))
        self.transition_combobox.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.transition_combobox)

        self.critic_label = LabelFactory.create(self.networks, text="Critic:", theme="dark")
        self.critic_label.grid(row=3, column=0, pady=(5, 15), padx=5, sticky="nse")
        scrollbar.bind_wheel(self.critic_label)

        self.critics = self.conf.get_all_classes(
            self.conf.agents_directory + "networks/CriticNetworks.py", "agents.networks."
        )
        self.critic_combobox = Combobox(self.networks, values=list(self.critics.keys()))
        self.critic_combobox.grid(row=3, column=1, pady=(5, 15), padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.critic_combobox)

        # Create action selection label frame
        self.action_selection = LabelFrameFactory.create(
            self, theme="action_selection", params={"scrollbar": scrollbar}
        )
        self.action_selection.grid(row=1, column=0, padx=5, pady=15, sticky="nsew")

        # Create the hyper-parameters label frame
        self.hyper_parameters = LabelFrameFactory.create(self, text="Hyper-parameters")
        CreationCHMM.configure_columns(self.hyper_parameters)
        self.hyper_parameters.grid(row=2, column=0, padx=5, pady=15, sticky="nsew")
        scrollbar.bind_wheel(self.hyper_parameters)

        self.beta_label = LabelFactory.create(self.hyper_parameters, text="Beta:", theme="dark")
        self.beta_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.beta_label)

        self.beta_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.beta_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.beta_entry)

        self.queue_capacity_label = LabelFactory.create(self.hyper_parameters, text="Queue capacity:", theme="dark")
        self.queue_capacity_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.queue_capacity_label)

        self.queue_capacity_entry = Entry(self.hyper_parameters, valid_input="int", help_message="50000")
        self.queue_capacity_entry.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.queue_capacity_entry)

        self.lr_label = LabelFactory.create(
            self.hyper_parameters, text="Variational free energy learning rate:", theme="dark"
        )
        self.lr_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.lr_label)

        self.lr_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.0001")
        self.lr_entry.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.lr_entry)

        self.critic_lr_label = LabelFactory.create(
            self.hyper_parameters, text="Critic's learning rate:", theme="dark"
        )
        self.critic_lr_label.grid(row=3, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.critic_lr_label)

        self.critic_lr_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.0001")
        self.critic_lr_entry.grid(row=3, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.critic_lr_entry)

        self.discount_factor_label = LabelFactory.create(
            self.hyper_parameters, text="Discount factor:", theme="dark"
        )
        self.discount_factor_label.grid(row=4, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.discount_factor_label)

        self.discount_factor_entry = Entry(self.hyper_parameters, valid_input="float", help_message="0.9")
        self.discount_factor_entry.grid(row=4, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.discount_factor_entry)

        self.n_steps_between_synchro_label = LabelFactory.create(
            self.hyper_parameters, text="Number of steps between synchronisation:", theme="dark"
        )
        self.n_steps_between_synchro_tooltip = ToolTip(
            self.n_steps_between_synchro_label,
            "The synchronization is between the weights of the target and critic network"
        )
        self.n_steps_between_synchro_label.grid(row=5, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.n_steps_between_synchro_label)

        self.n_steps_between_synchro_entry = Entry(self.hyper_parameters, valid_input="float", help_message="1.0")
        self.n_steps_between_synchro_entry.grid(row=5, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.n_steps_between_synchro_entry)

        self.critic_objective_label = LabelFactory.create(
            self.hyper_parameters, text="Critic's objective:", theme="dark"
        )
        self.critic_objective_label.grid(row=6, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.critic_objective_label)

        self.critic_objective_combobox = Combobox(self.hyper_parameters, values=["Reward", "Expected Free Energy"])
        self.critic_objective_combobox.grid(row=6, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.critic_objective_combobox)

        self.n_latent_dim_label = LabelFactory.create(
            self.hyper_parameters, text="Number of latent dimensions:", theme="dark"
        )
        self.n_latent_dim_label.grid(row=7, column=0, pady=(5, 15), padx=5, sticky="nse")
        scrollbar.bind_wheel(self.n_latent_dim_label)

        self.n_latent_dim_entry = Entry(self.hyper_parameters, valid_input="int", help_message="10")
        self.n_latent_dim_entry.grid(row=7, column=1, pady=(5, 15), padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.n_latent_dim_entry)

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
        encoder = self.encoders[self.encoder_combobox.get()]
        decoder = self.decoders[self.decoder_combobox.get()]
        transition = self.transitions[self.transition_combobox.get()]
        critic = self.critics[self.critic_combobox.get()]
        strategy = LabelFrameFactory.get_strategy(self.action_selection)
        json.dump({
            "name": self.parent.agent_name_entry.get(),
            "module": "agents.impl.CHMM",
            "class": "CHMM",
            "encoder": {
                "module": str(encoder.__module__),
                "class": str(encoder.__name__),
            },
            "decoder": {
                "module": str(decoder.__module__),
                "class": str(decoder.__name__),
            },
            "transition": {
                "module": str(transition.__module__),
                "class": str(transition.__name__),
            },
            "critic": {
                "module": str(critic.__module__),
                "class": str(critic.__name__),
            },
            "strategy": strategy,
            "discount_factor": self.discount_factor_entry.get(),
            "beta": self.beta_entry.get(),
            "queue_capacity": self.queue_capacity_entry.get(),
            "n_steps_between_synchro": self.n_steps_between_synchro_entry.get(),
            "vfe_lr": self.lr_entry.get(),
            "critic_lr": self.critic_lr_entry.get(),
            "critic_objective": self.critic_objective_combobox.get(),
            "n_states": self.n_latent_dim_entry.get()
        }, file, indent=2)

        # Refresh project tree and display empty frame in the project page
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")