import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class Scrollbar(tk.Canvas):
    """
    A scrollbar is gridded as a sibling of what it's scrolling.
    """

    def __init__(self, parent, orient='vertical', hideable=True, **kwargs):
        """
        Create the
        :param parent: the parent widget
        :param orient: the orientation of the scrollbar, i.e., vertical or horizontal
        :param hideable: whether the scrollbar can be hide when not required
        :param kwargs: additional (key-value) parameters
        """

        self.command = kwargs.pop('command', None)
        super().__init__(parent, **kwargs)

        self.conf = AnalysisConfig.instance

        self.orient = orient
        self.hideable = hideable

        self.new_start_y = 0
        self.new_start_x = 0
        self.first_y = 0
        self.first_x = 0

        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0

        self.last_y = 0
        self.last_x = 0
        self.y_move_on_click = 0
        self.x_move_on_click = 0

        self.slider_color = self.conf.colors["scrollbar"]
        self.trough_color = self.conf.colors["dark_gray"]

        self.config(bg=self.trough_color, bd=0, highlightthickness=0, width=15)

        # coordinates are irrelevant; they will be recomputed in the 'set' method
        self.create_rectangle(
            0, 0, 1, 1,
            fill=self.slider_color,
            width=0,
            tags=('slider',)
        )
        self.bind('<ButtonPress-1>', self.move_on_click)
        self.bind('<ButtonPress-1>', self.start_scroll, add='+')
        self.bind('<B1-Motion>', self.move_on_scroll)
        self.bind('<ButtonRelease-1>', self.end_scroll)

        self.bind_wheel(self)

    def bind_wheel(self, widget, recursive=False):
        """
        Allow scrolling when on top of the widget
        :param widget: the widget
        :param recursive: whether the ability to scroll should be added to all descendant of the widgets
        """
        # with Windows OS
        widget.bind("<MouseWheel>", self.scroll_on_wheel)
        # with Linux OS
        widget.bind("<Button-5>", self.scroll_on_wheel)
        widget.bind("<Button-4>", self.scroll_on_wheel)

        # Bin all descendant of the widget
        if recursive:
            for child in widget.winfo_children():
                self.bind_wheel(child, recursive=True)

    def set(self, lo, hi):
        """
        Resize & reposition the slider
        :param lo: current position of the slide (top edge of the slider)
        :param hi: current position of the slide (bottom edge of the slider)
        """
        lo = float(lo)
        hi = float(hi)

        if self.hideable is True:
            if lo <= 0.0 and hi >= 1.0:
                self.grid_remove()
                return
            self.grid()

        height = self.winfo_height()
        width = 15
        if self.orient == 'vertical':
            self.x0 = 2
            self.y0 = max(int(height * lo), 0)
            self.x1 = width - 2
            self.y1 = min(int(height * hi), height)
        elif self.orient == 'horizontal':
            self.x0 = max(int(width * lo), 0)
            self.y0 = 2
            self.x1 = min(int(width * hi), width)
            self.y1 = height
        else:
            raise NotImplementedError("The orient parameter should be vertical or horizontal.")

        self.coords('slider', self.x0, self.y0, self.x1, self.y1)

    def move_on_click(self, event):
        """
        Move the slider on click
        :param event: the event that triggered the call to the function
        """
        if self.orient == 'vertical':
            # don't scroll on click if mouse pointer is w/in slider
            y = event.y / self.winfo_height()
            if event.y < self.y0 or event.y > self.y1:
                self.command('moveto', y)
            # get starting position of a scrolling event
            else:
                self.first_y = event.y
        elif self.orient == 'horizontal':
            # do nothing if mouse pointer is w/in slider
            x = event.x / self.winfo_width()
            if event.x < self.x0 or event.x > self.x1:
                self.command('moveto', x)
            # get starting position of a scrolling event
            else:
                self.first_x = event.x

    def start_scroll(self, event):
        """
        Start the scrolling
        :param event: the event that triggered the call to this function
        """
        if self.orient == 'vertical':
            self.last_y = event.y
            self.y_move_on_click = int(event.y - self.coords('slider')[1])
        elif self.orient == 'horizontal':
            self.last_x = event.x
            self.x_move_on_click = int(event.x - self.coords('slider')[0])

    def end_scroll(self, event):
        """
        Stop the scrolling
        :param event: the event that triggered the call to this function
        """
        if self.orient == 'vertical':
            self.new_start_y = event.y
        elif self.orient == 'horizontal':
            self.new_start_x = event.x

    def move_on_scroll(self, event):
        """
        Move the slider on scroll
        :param event: the event that triggered the call to this function
        """
        jerkiness = 3

        if self.orient == 'vertical':
            if abs(event.y - self.last_y) < jerkiness:
                return
            # scroll the scrolled widget in proportion to mouse motion
            #   compute whether scrolling up or down
            delta = 1 if event.y > self.last_y else -1
            #   remember this location for the next time this is called
            self.last_y = event.y
            #   do the scroll
            self.command('scroll', delta, 'units')
            # fix slider to mouse pointer
            mouse_pos = event.y - self.first_y
            if self.new_start_y != 0:
                mouse_pos = event.y - self.y_move_on_click
            self.command('moveto', mouse_pos / self.winfo_height())
        elif self.orient == 'horizontal':
            if abs(event.x - self.last_x) < jerkiness:
                return
            # scroll the scrolled widget in proportion to mouse motion compute whether scrolling left or right
            delta = 1 if event.x > self.last_x else -1
            # remember this location for the next time this is called
            self.last_x = event.x
            # do the scroll
            self.command('scroll', delta, 'units')
            # fix slider to mouse pointer
            mouse_pos = event.x - self.first_x
            if self.new_start_x != 0:
                mouse_pos = event.x - self.x_move_on_click
            self.command('moveto', mouse_pos / self.winfo_width())

    def is_hidden(self):
        """
        Check whether the scrollbar is hidden or not
        :return: True if the scrollbar is hidden, false otherwise
        """
        return self.grid_info() == {}

    def scroll_on_wheel(self, event):
        """
        Scrolling when mouse wheel is used
        :param event: the event that triggered the call to this function
        """
        if self.is_hidden():
            return

        delta = 0
        if event.num == 5 or event.delta == -120:
            delta = 1
        if event.num == 4 or event.delta == 120:
            delta = -1
        self.command('scroll', delta, 'units')
