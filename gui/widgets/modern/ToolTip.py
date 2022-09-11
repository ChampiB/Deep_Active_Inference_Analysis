import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.LabelFactory import LabelFactory


class ToolTip:

    def __init__(self, widget, text):
        self.config = AnalysisConfig.instance
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.text = text
        widget.bind('<Enter>', self.enter)
        widget.bind('<Leave>', self.leave)

    def showtip(self):
        """
        Display text in tooltip window
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

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def enter(self, event):
        self.showtip()

    def leave(self, event):
        self.hidetip()
