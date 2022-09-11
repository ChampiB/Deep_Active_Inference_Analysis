import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.LabelFactory import LabelFactory


class ToolTip:
    """
    A class displaying a message when over a widget
    """

    def __init__(self, widget, text):
        """
        Constructor
        :param widget: the widget for which the help message must be displayed
        :param text: the help message to be displayed
        """
        self.config = AnalysisConfig.instance
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.text = text
        widget.bind('<Enter>', self.showtip)
        widget.bind('<Leave>', self.hidetip)

    def showtip(self, event=None):
        """
        Display text in tooltip window
        :param event: unused
        """
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 50
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = LabelFactory.create(tw, text=self.text, theme="tooltip")
        label.pack(ipadx=5, ipady=5)

    def hidetip(self, event=None):
        """
        Hide the help message
        :param event: unused
        """
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
