import tkinter as tk
from threading import Timer
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory


class Combobox(tk.Frame):
    """
    A class representing modern looking combobox
    """

    def __init__(self, parent, values, default_value=None, command=None, image=None, theme="white"):
        """
        Constructor
        :param parent: the parent widget
        :param values: the possible value the combobox can be in
        :param default_value: the default value of the combobox
        :param command: the callback function to call when the combo-box's value has changed
        :param image: the image to display in the left of the combobox
        :param theme: the theme of the combobox
        """

        super().__init__(parent)

        self.command = command
        self.assets = AnalysisAssets.instance
        self.conf = AnalysisConfig.instance

        self.on_combobox = False
        self.on_list_of_values = False
        self.bind('<Leave>', self.on_leave_combobox)
        self.bind('<Enter>', self.on_enter_combobox)

        # Theme attributes
        self.theme = theme
        self.background_color = "white"
        if theme == "dark":
            self.background_color = self.conf.colors["dark_gray"]
        self.highlight_thickness = 1  # if theme == "white" else 0
        self.font_size = 14 if theme == "white" else 12
        self.inner_pad = 5 if self.theme == "white" else 0
        self.highlight = {}
        if self.theme == "dark":
            self.highlight = {"highlightthickness": 1, "highlightbackground": "gray"}

        self.config(background=self.background_color, **self.highlight)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        col_index = 0
        if image is not None:
            self.server_image = LabelFactory.create(self, image=image)
            self.server_image.grid(row=0, column=col_index, padx=(3, 0), pady=3, ipadx=1, ipady=1)
            self.columnconfigure(2, weight=1)
            col_index += 1

        self.values = values
        self.current_value = tk.StringVar(self, values[0] if default_value is None else default_value)
        self.current_value_label = LabelFactory.create(
            self, text=self.current_value, theme=theme, font_size=self.font_size
        )
        pad_y = 8 if theme == "white" else (4, 2)
        self.current_value_label.grid(row=0, column=col_index, pady=pad_y, padx=8, sticky="nsw")
        col_index += 1

        chevron = "black_chevron_down"
        if theme == "dark":
            chevron = "chevron_down"
        self.change_value_button = ButtonFactory.create(
            self, image=self.assets.get(chevron), command=self.display_or_hide_list_of_values, theme=theme
        )
        self.change_value_button.grid(row=0, column=col_index, sticky="nse")
        col_index += 1

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
        ipad_y = 5 if self.theme == "white" else 2

        # Create the list of values if it does not exist
        if self.list_values_widget is None:
            x, y, cx, cy = self.bbox()
            x = x + self.winfo_rootx() - 1
            y = y + cy + self.winfo_rooty() + 1
            self.list_values_widget = tk.Toplevel(self)
            self.list_values_widget.wm_overrideredirect(True)
            self.list_values_widget.config(background=self.background_color, **self.highlight)
            self.list_values_widget.wm_geometry("%dx%d+%d+%d" % (cx + 2, (cy + ipad_y * 2) * len(self.values), x, y))
            for value in self.values:
                if isinstance(value, str):
                    params = {"text": value} if isinstance(value, str) else {"image": value}
                    label = ButtonFactory.create(
                        self.list_values_widget, theme=self.theme, font_size=self.font_size,
                        command=lambda v=value: self.update_value(v), **params
                    )
                else:
                    label = ButtonFactory.create(
                        self.list_values_widget, theme="dark", font_size=self.font_size, **value
                    )
                    label.config(padx=2)
                label.config(anchor="w")
                label.pack(fill="x", expand=True, ipadx=self.inner_pad, ipady=ipad_y)
            self.list_values_widget.bind('<Leave>', self.on_leave_list_of_values)
            self.list_values_widget.bind('<Enter>', self.on_enter_list_of_values)
            return

        # Reposition the list of values
        x, y, cx, cy = self.bbox()
        x = x + self.winfo_rootx() - 1
        y = y + cy + self.winfo_rooty() + 1
        self.list_values_widget.wm_geometry("%dx%d+%d+%d" % (cx + 2, (cy + ipad_y * 2) * len(self.values), x, y))

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
            if self.command is not None:
                self.command()

    def lock(self):
        """
        Lock the value of the combobox
        """
        # Change background color
        self.config(background=self.conf.colors["light_text"], highlightthickness=1)
        self.current_value_label.config(background=self.conf.colors["light_text"])

        # Do nothing when button is clicked
        self.change_value_button.config(command=lambda x=self: x, background=self.conf.colors["light_text"])

    def get(self):
        """
        Getter
        :return: the current value of the combobox
        """
        return self.current_value.get()

    def set_values(self, values):
        """
        Set the combobox values
        :param values: the new values
        """
        self.list_values_widget = None
        self.values = values
        self.current_value.set(values[0])

