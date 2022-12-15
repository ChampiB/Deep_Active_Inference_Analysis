import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.ToolTip import ToolTip


class LabelFrameFactory:
    """
    A class representing modern looking label frame
    """

    conf = AnalysisConfig.instance
    strategies = conf.get_all_classes(conf.agents_directory + "strategies/", "agents.strategies.")
    encoders = conf.get_all_classes(conf.agents_directory + "networks/EncoderNetworks.py", "agents.networks.")
    decoders = conf.get_all_classes(conf.agents_directory + "networks/DecoderNetworks.py", "agents.networks.")
    transitions = conf.get_all_classes(conf.agents_directory + "networks/TransitionNetworks.py", "agents.networks.")
    critics = conf.get_all_classes(conf.agents_directory + "networks/CriticNetworks.py", "agents.networks.")
    policies = conf.get_all_classes(conf.agents_directory + "networks/PolicyNetworks.py", "agents.networks.")

    @staticmethod
    def create(parent, text=None, theme="default", params=None):
        """
        Create a label
        :param parent: the parent widget
        :param text: the label's text
        :param theme: the label's theme, i.e., "dark", "gray", "white" or "tooltip"
        :param params: additional parameters
        :return: the created label
        """
        if theme == "default":
            return LabelFrameFactory.create_default_label_frame(parent, text)
        if theme == "action_selection":
            return LabelFrameFactory.create_action_selection_label_frame(parent, text, params)
        if theme == "networks":
            return LabelFrameFactory.create_networks_label_frame(parent, text, params)
        if theme == "hyper_parameters":
            return LabelFrameFactory.create_hyper_parameters_label_frame(parent, text, params)
        raise NotImplementedError(f"LabelFrameFactory.create does not support theme: '{theme}'.")

    @staticmethod
    def create_default_label_frame(parent, text):
        """
        Create a default label frame
        :param parent: the parent widget
        :param text: the text of the label frame
        """
        return tk.LabelFrame(
            parent,
            text=text,
            background=LabelFrameFactory.conf.colors["dark_gray"],
            highlightbackground=LabelFrameFactory.conf.colors["gray"],
            foreground=LabelFrameFactory.conf.colors["light_text"],
            font=(LabelFrameFactory.conf.font["name"], 14, LabelFrameFactory.conf.font["style"])
        )

    @staticmethod
    def create_hyper_parameters_label_frame(parent, text, params):
        """
        Create a hyper parameters label frame
        :param parent: the parent widget
        :param text: the text of the label frame
        :param params: a dictionary containing the default values
        :return:
        """
        # Get the default values
        default_values = {
            "Discount factor:": ("entry", "discount_factor", "float"),
            "Number of steps between synchronisation:": ("entry", "n_steps_between_synchro", "int"),
            "Queue capacity:": ("entry", "queue_capacity", "int"),
            "Q-network's learning rate:": ("entry", "q_network_lr", "float"),
            "Beta:": ("entry", "beta", "float"),
            "Variational free energy learning rate:": ("entry", "vfe_lr", "float"),
            "Critic's learning rate:": ("entry", "critic_lr", "float"),
            "Number of latent dimensions:": ("entry", "n_states", "int"),
            "Critic's objective:": ("combobox", "critic_objective", ["Reward", "Expected Free Energy"]),
            "Exploration constant": ("entry", "exp_const", "float"),
            "Maximum number of planning iterations": ("entry", "max_planning_steps", "int"),
            "Number of samples for EFE estimation": ("entry", "n_samples", "int"),
        }

        # Create networks label frame
        text = "Hyper-parameters" if text is None else text
        label_frame = LabelFrameFactory.create(parent, text=text)
        LabelFrameFactory.configure_columns(label_frame)

        # Create the label frame content
        widgets = {}
        row_index = 0
        widget = None
        label = None
        for text, (widget_class, key, valid_input) in default_values.items():
            # If no default value, then does not display the label and combobox
            default_value = params.get(key, None)
            if default_value is None:
                continue

            # Display the label
            label = LabelFactory.create(label_frame, text=text, theme="dark")
            label.grid(row=row_index, column=0, pady=5, padx=5, sticky="nse")

            # Display the combobox
            if widget_class == "entry":
                widget = Entry(label_frame, valid_input=valid_input, help_message=default_value)
            elif widget_class == "combobox":
                widget = Combobox(label_frame, values=valid_input, default_value=default_value)
            widget.grid(row=row_index, column=1, pady=5, padx=5, sticky="nsew")
            widgets[key] = widget

            # Add tooltips
            if key == "n_steps_between_synchro":
                ToolTip(label, "The synchronization is between the weights of the target and Q-network")

            row_index += 1

        # Reposition label and combobox
        label.grid(row=row_index - 1, column=0, pady=(5, 15), padx=5, sticky="nse")
        widget.grid(row=row_index - 1, column=1, pady=(5, 15), padx=5, sticky="nsew")
        return label_frame, widgets

    @staticmethod
    def create_networks_label_frame(parent, text, params):
        """
        Create a networks label frame
        :param parent: the parent widget
        :param text: the text of the label frame
        :param params: a dictionary containing the default values
        :return:
        """
        # Get the default values
        default_values = {
            "Encoder:": ("encoder", LabelFrameFactory.encoders),
            "Decoder:": ("decoder", LabelFrameFactory.decoders),
            "Transition:": ("transition", LabelFrameFactory.transitions),
            "Critic:": ("critic", LabelFrameFactory.critics),
            "Q-network:": ("policy", LabelFrameFactory.policies)
        }

        # Create networks label frame
        text = "Networks" if text is None else text
        label_frame = LabelFrameFactory.create(parent, text=text)
        LabelFrameFactory.configure_columns(label_frame)

        # Create the label frame content
        row_index = 0
        widgets = {}
        combobox = None
        for text, (key, values) in default_values.items():
            # If no default value, then does not display the label and combobox
            default_value = params.get(key, None)
            if default_value is None:
                continue

            # Display the label
            label = LabelFactory.create(label_frame, text=text, theme="dark")
            label.grid(row=row_index, column=0, pady=5, padx=5, sticky="nse")

            # Display the combobox
            combobox = Combobox(label_frame, values=list(values.keys()), default_value=default_value)
            widgets[key] = (combobox, values)
            combobox.grid(row=row_index, column=1, pady=5, padx=5, sticky="nsew")
            row_index += 1
        combobox.grid(row=row_index - 1, column=1, pady=(5, 15), padx=5, sticky="nsew")
        return label_frame, widgets

    @staticmethod
    def create_action_selection_label_frame(parent, text, params):
        """
        Create an action selection label frame
        :param parent: the parent widget
        :param text: the text of the label frame
        :param params: a dictionary containing the default values
        :return:
        """
        # Get default value and pad y
        strategy = params.get("strategy", {"class": "RandomActions"})
        pad_y = 5 if strategy["class"] in ["EpsilonGreedy", "SoftmaxSampling"] else (5, 15)

        # Create action selection label frame
        text = "Action Selection" if text is None else text
        label_frame = LabelFrameFactory.create(parent, text=text)
        LabelFrameFactory.configure_columns(label_frame)

        strategy_label = LabelFactory.create(label_frame, text="Strategy:", theme="dark")
        strategy_label.grid(row=0, column=0, pady=pad_y, padx=5, sticky="nse")

        strategies = params.get("strategies", None)
        if strategies is None:
            strategies = list(LabelFrameFactory.strategies.keys())
        strategy_combobox = Combobox(
            label_frame, values=strategies, default_value=strategy["class"],
            command=lambda: LabelFrameFactory.display_action_selection_parameters(label_frame, strategy)
        )
        strategy_combobox.grid(row=0, column=1, pady=pad_y, padx=5, sticky="nsew")
        LabelFrameFactory.display_action_selection_parameters(label_frame, strategy)
        return label_frame

    @staticmethod
    def display_action_selection_parameters(label_frame, strategy):
        """
        Display the action selection parameters
        :param label_frame: the (action selection) label frame
        :param strategy: the action selection strategy
        """
        # Remove old selection parameters
        for slave in label_frame.grid_slaves():
            if slave.grid_info()["row"] >= 1:
                slave.grid_remove()

        # Set small y padding
        label = label_frame.grid_slaves(0, 0)[0]
        label.grid(row=0, column=0, pady=5, sticky="nse")
        combobox = label_frame.grid_slaves(0, 1)[0]
        combobox.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")

        # Remove new selection parameters
        if combobox.get() == "EpsilonGreedy":
            # Add epsilon start value
            epsilon_start_label = LabelFactory.create(label_frame, text="Epsilon start value:", theme="dark")
            epsilon_start_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")

            default_val = strategy.get("epsilon_start", "0.9")
            epsilon_start_entry = Entry(label_frame, valid_input="float", help_message=default_val)
            epsilon_start_entry.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")

            # Add epsilon end value
            epsilon_end_label = LabelFactory.create(label_frame, text="Epsilon end value:", theme="dark")
            epsilon_end_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")

            default_val = strategy.get("epsilon_end", "0.05")
            epsilon_end_entry = Entry(label_frame, valid_input="float", help_message=default_val)
            epsilon_end_entry.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")

            # Add epsilon decay value
            epsilon_decay_label = LabelFactory.create(label_frame, text="Epsilon decay:", theme="dark")
            epsilon_decay_label.grid(row=3, column=0, pady=(5, 15), padx=5, sticky="nse")

            default_val = strategy.get("epsilon_decay", "1000")
            epsilon_decay_entry = Entry(label_frame, valid_input="int", help_message=default_val)
            epsilon_decay_entry.grid(row=3, column=1, pady=(5, 15), padx=5, sticky="nsew")
        elif combobox.get() == "SoftmaxSampling":
            # Add the gain
            gain_param_label = LabelFactory.create(label_frame, text="Gain parameter:", theme="dark")
            gain_param_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

            default_val = strategy.get("gain", "1")
            gain_param_entry = Entry(label_frame, valid_input="float", help_message=default_val)
            gain_param_entry.grid(row=1, column=1, pady=(5, 15), padx=5, sticky="nsew")
        else:
            # Set large y padding
            label = label_frame.grid_slaves(0, 0)[0]
            label.grid(row=0, column=0, pady=(5, 15), sticky="nse")
            combobox = label_frame.grid_slaves(0, 1)[0]
            combobox.grid(row=0, column=1, pady=(5, 15), padx=5, sticky="nsew")

        # Update agent form idle tasks to let tkinter calculate buttons sizes
        agent_form = label_frame.master
        agent_form.update_idletasks()
        canvas = agent_form.master.master.master.canvas
        canvas.config(scrollregion=canvas.bbox("all"))

    @staticmethod
    def configure_columns(widget):
        """
        Configure the widget columns
        :param widget: the widget
        """
        widget.columnconfigure(0, weight=4, uniform="labelframe")
        widget.columnconfigure(1, weight=4, uniform="labelframe")
        widget.columnconfigure(2, weight=1, uniform="labelframe")

    @staticmethod
    def get_strategy(label_frame):
        """
        Getter
        :param label_frame: the action selection label frame
        :return: a dictionary describing the action selection strategy
        """
        strategy_name = label_frame.grid_slaves(row=0, column=1)[0].get()
        strategy = LabelFrameFactory.strategies[strategy_name]

        strategy_params = {}
        if strategy_name == "EpsilonGreedy":
            strategy_params["epsilon_start"] = label_frame.grid_slaves(row=1, column=1)[0].get()
            strategy_params["epsilon_end"] = label_frame.grid_slaves(row=2, column=1)[0].get()
            strategy_params["epsilon_decay"] = label_frame.grid_slaves(row=3, column=1)[0].get()
        if strategy_name == "SoftmaxSampling":
            strategy_params["gain"] = label_frame.grid_slaves(row=1, column=1)[0].get()

        return {
            "module": str(strategy.__module__),
            "class": str(strategy.__name__),
        } | strategy_params
