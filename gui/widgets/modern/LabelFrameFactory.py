import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory


class LabelFrameFactory:
    """
    A class representing modern looking label frame
    """

    conf = AnalysisConfig.instance
    strategies = conf.get_all_classes(conf.agents_directory + "strategies/", "agents.strategies.")

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
    def create_action_selection_label_frame(parent, text, params):
        """
        Create an action selection label frame
        :param parent: the parent widget
        :param text: the text of the label frame
        :param params: a dictionary containing the 'scrollbar' and (optionally) the 'default_value'
        :return:
        """
        # Get the scrollbar
        scrollbar = params["scrollbar"]

        # Get default value and pad y
        default_value = params.get("default_value", "EpsilonGreedy")
        pad_y = 5 if default_value in ["EpsilonGreedy", "SoftmaxSampling"] else (5, 15)

        # Create action selection label frame
        text = "Action Selection" if text is None else text
        label_frame = LabelFrameFactory.create(parent, text=text)
        LabelFrameFactory.configure_columns(label_frame)
        scrollbar.bind_wheel(label_frame)

        strategy_label = LabelFactory.create(label_frame, text="Strategy:", theme="dark")
        strategy_label.grid(row=0, column=0, pady=pad_y, padx=5, sticky="nse")
        scrollbar.bind_wheel(strategy_label)

        strategy_combobox = Combobox(
            label_frame, values=list(LabelFrameFactory.strategies.keys()), default_value=default_value,
            command=lambda: LabelFrameFactory.display_action_selection_parameters(label_frame, scrollbar)
        )
        strategy_combobox.grid(row=0, column=1, pady=pad_y, padx=5, sticky="nsew")
        scrollbar.bind_wheel(strategy_combobox)
        LabelFrameFactory.display_action_selection_parameters(label_frame, scrollbar)
        return label_frame

    @staticmethod
    def display_action_selection_parameters(label_frame, scrollbar):
        """
        Display the action selection parameters
        :param label_frame: the (action selection) label frame
        :param scrollbar: the scrollbar
        """
        # Remove old selection parameters
        row = 0
        combobox = label_frame.grid_slaves(row, 1)[0]
        for slave in label_frame.grid_slaves():
            row = slave.grid_info()["row"]
            if row >= 1:
                slave.grid_remove()

        # Set small y padding
        label = label_frame.grid_slaves(row, 0)[0]
        label.grid(row=0, column=0, pady=5, sticky="nse")
        cb = label_frame.grid_slaves(row, 1)[0]
        cb.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")

        # Remove new selection parameters
        if combobox.get() == "EpsilonGreedy":
            # Add epsilon start value
            epsilon_start_label = LabelFactory.create(label_frame, text="Epsilon start value:", theme="dark")
            epsilon_start_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")
            scrollbar.bind_wheel(epsilon_start_label)

            epsilon_start_entry = Entry(label_frame, valid_input="float", help_message="0.9")
            epsilon_start_entry.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")
            scrollbar.bind_wheel(epsilon_start_entry)

            # Add epsilon end value
            epsilon_end_label = LabelFactory.create(label_frame, text="Epsilon end value:", theme="dark")
            epsilon_end_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")
            scrollbar.bind_wheel(epsilon_end_label)

            epsilon_end_entry = Entry(label_frame, valid_input="float", help_message="0.05")
            epsilon_end_entry.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
            scrollbar.bind_wheel(epsilon_end_entry)

            # Add epsilon decay value
            epsilon_decay_label = LabelFactory.create(label_frame, text="Epsilon decay:", theme="dark")
            epsilon_decay_label.grid(row=3, column=0, pady=(5, 15), padx=5, sticky="nse")
            scrollbar.bind_wheel(epsilon_decay_label)

            epsilon_decay_entry = Entry(label_frame, valid_input="int", help_message="1000")
            epsilon_decay_entry.grid(row=3, column=1, pady=(5, 15), padx=5, sticky="nsew")
            scrollbar.bind_wheel(epsilon_decay_entry)
        elif combobox.get() == "SoftmaxSampling":
            # Add the gain
            gain_param_label = LabelFactory.create(label_frame, text="Gain parameter:", theme="dark")
            gain_param_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")
            scrollbar.bind_wheel(gain_param_label)

            gain_param_entry = Entry(label_frame, valid_input="float", help_message="1.0")
            gain_param_entry.grid(row=1, column=1, pady=(5, 15), padx=5, sticky="nsew")
            scrollbar.bind_wheel(gain_param_entry)
        else:
            # Set large y padding
            label = label_frame.grid_slaves(row, 0)[0]
            label.grid(row=0, column=0, pady=(5, 15), sticky="nse")
            combobox = label_frame.grid_slaves(row, 1)[0]
            combobox.grid(row=0, column=1, pady=(5, 15), padx=5, sticky="nsew")

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
