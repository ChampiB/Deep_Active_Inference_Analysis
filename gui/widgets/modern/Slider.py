import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class Slider(tk.Canvas):
    """
    A slider allowing the selection of discrete values.
    """

    def __init__(self, parent, observer_widgets, values=None, **kwargs):
        """
        Create the slider
        :param parent: the parent widget
        :param observer_widgets: the widgets to be notified when the slider changes value
        :param kwargs: additional (key-value) parameters
        """
        if values is None:
            values = [50000 * i for i in range(21)]

        self.conf = AnalysisConfig.instance
        super().__init__(parent, bg=self.conf.colors["dark_gray"], highlightthickness=0, **kwargs)

        self.observer_widgets = observer_widgets

        self.values = values
        self.current_value = values[0]

        self.update_value = False
        self.width = 0
        self.height = 0
        self.bind("<Configure>", self.on_resize)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<B1-Motion>", self.on_motion)

    def on_resize(self, event):
        """
        Resize the slider
        :param event: the event that triggered the call to this function
        """
        width = float(event.width)
        self.width = width
        height = float(event.height)
        self.height = height
        self.delete("all")
        self.create_line(
            100, height / 2 + 10, width - 100, height / 2 + 10,
            fill=self.conf.colors["light_text"],
            width=4
        )
        shift = (width - 200) / (len(self.values) - 1)
        for i, value in enumerate(self.values):
            self.create_line(
                100 + shift * i, height / 2 + 5, 100 + shift * i, height / 2 + 15,
                fill=self.conf.colors["light_text"], width=4
            )
            self.create_text(
                100 + shift * i, height / 2 - 10, text=f"{int(value / 1000)}K", fill=self.conf.colors["light_text"]
            )
        self.draw_cursor()

    def get(self):
        """
        Getter
        :return: the current value selected by the slider
        """
        return self.current_value

    def on_click(self, event):
        """
        Allow the value to be updated
        :param event: the event that triggered the call to this function
        """
        self.update_value = True

    def on_release(self, event):
        """
        Fix the slider's value
        :param event: the event that triggered the call to this function
        """
        self.update_value = False

    def on_motion(self, event):
        """
        Update the slider's value
        :param event: the event that triggered the call to this function
        """
        if self.update_value is True:
            shift = (self.width - 200) / (len(self.values) - 1)
            new_value = min(self.values, key=lambda x: abs(100 + shift * self.values.index(x) - float(event.x)))
            if self.current_value != new_value:
                for w in self.observer_widgets:
                    w.set_value(new_value)
                self.current_value = new_value
                self.draw_cursor()

    def draw_cursor(self):
        """
        Draw the cursor displaying the current value
        """
        self.delete("current_value")
        shift = (self.width - 200) / (len(self.values) - 1)
        x = 100 + shift * self.values.index(self.current_value)
        self.create_rectangle(
            x - 5, self.height / 2 + 5, x + 5, self.height / 2 + 15,
            outline=self.conf.colors["blue"],
            fill=self.conf.colors["dark_blue"],
            width=2,
            tags="current_value"
        )
