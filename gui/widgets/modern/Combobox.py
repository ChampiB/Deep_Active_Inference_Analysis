import tkinter as tk
from threading import Timer
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory


class Combobox(tk.Frame):
    """
    A scrollbar is gridded as a sibling of what it's scrolling.
    """

    def __init__(self, parent, values, command):
        """
        Constructor
        :param parent: the parent widget
        :param values: the possible value the combobox can be in
        :param command: the callback function to call when the combo-box's value has changed
        """

        super().__init__(parent)

        self.command = command
        self.assets = AnalysisAssets.instance
        self.conf = AnalysisConfig.instance

        self.on_combobox = False
        self.on_list_of_values = False
        self.bind('<Leave>', self.on_leave_combobox)
        self.bind('<Enter>', self.on_enter_combobox)

        self.config(background="white", highlightthickness=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.values = values
        self.current_value = tk.StringVar(self, values[0])
        self.current_value_label = LabelFactory.create(self, text=self.current_value, theme="white")
        self.current_value_label.grid(row=0, column=0, pady=8, padx=8, sticky="nsw")

        self.change_value_button = ButtonFactory.create(
            self, image=self.assets.get("black_chevron_down"), command=self.display_or_hide_list_of_values,
            theme="white"
        )
        self.change_value_button.grid(row=0, column=1, sticky="nse")

        self.list_values_widget = None

    def on_leave_list_of_values(self, event):
        """
        Keep track of when the mouse leave the list of value
        :param event: unused
        """
        self.on_list_of_values = False
        Timer(0.2, self.hide_list_of_value_if_needed).start()

    def on_enter_list_of_values(self, event):
        """
        Keep track of when the mouse enter the list of value
        :param event: unused
        """
        self.on_list_of_values = True
        Timer(0.2, self.hide_list_of_value_if_needed).start()

    def on_leave_combobox(self, event):
        """
        Keep track of when the mouse leave the combobox
        :param event: unused
        """
        self.on_combobox = False
        Timer(0.2, self.hide_list_of_value_if_needed).start()

    def on_enter_combobox(self, event):
        """
        Keep track of when the mouse enter the combobox
        :param event: unused
        """
        self.on_combobox = True
        Timer(0.2, self.hide_list_of_value_if_needed).start()

    def hide_list_of_value_if_needed(self):
        """
        Hide the list of value when the mouse is not over it anymore
        """
        if not self.on_combobox and not self.on_list_of_values and self.list_values_widget is not None:
            self.list_values_widget.withdraw()

    def display_or_hide_list_of_values(self):
        """
        Hide the list of values if currently displayed, and display the list of values if currently hidden
        """
        # Create the list of values if it does not exist
        if self.list_values_widget is None:
            x, y, cx, cy = self.bbox()
            x = x + self.winfo_rootx() - 1
            y = y + cy + self.winfo_rooty() + 1
            self.list_values_widget = tk.Toplevel(self)
            self.list_values_widget.wm_overrideredirect(True)
            self.list_values_widget.wm_geometry("%dx%d+%d+%d" % (cx + 2, cy * len(self.values), x, y))
            for value in self.values:
                label = ButtonFactory.create(
                    self.list_values_widget, theme="white", text=value, command=lambda v=value: self.update_value(v)
                )
                label.pack(fill="x", expand=True, ipadx=5, ipady=5)
            self.list_values_widget.bind('<Leave>', self.on_leave_list_of_values)
            self.list_values_widget.bind('<Enter>', self.on_enter_list_of_values)
            return

        # Display or hide list of values
        if self.list_values_widget.winfo_viewable():
            self.list_values_widget.withdraw()
        else:
            self.list_values_widget.deiconify()

    def update_value(self, value):
        """
        Update the current value of the combobox
        :param value: the new value
        """
        if self.list_values_widget is None:
            return
        self.list_values_widget.withdraw()
        if self.current_value.get() != value:
            self.current_value.set(value)
            self.command()

    def get(self):
        """
        Getter
        :return: the current value of the combobox
        """
        return self.current_value.get()
