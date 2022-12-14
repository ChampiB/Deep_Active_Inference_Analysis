from threading import Lock
import tkinter as tk

from gui.AnalysisAssets import AnalysisAssets
from gui.DataStorage import DataStorage
from gui.jobs.JobPool import JobPool


class AnalysisWindow(tk.Tk):
    """
    A class representing the main window of the analysis tool
    """

    def __init__(self):
        """
        Construct the analysis window
        """
        # Call parent constructor
        super().__init__()

        # Set window's title and icon
        self.title(string='Analysis Tool')
        self.wm_iconphoto(False, AnalysisAssets.get("analysis_button", subsample=1))

        # Store the configuration
        self.conf = DataStorage.get("conf")

        # Display window in full-screen mode
        self.attributes("-fullscreen", True)

        # Pressing the escape key closes the window
        self.bind('<Escape>', self.close)

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

        # List of all available pages' class and instance, as well as the currently displayed page
        self.pages_class = self.conf.get_all_classes(self.conf.pages_directory, "gui.pages.")
        self.pages = {}
        self.current_page = None

        # Local training attributes
        self.pool = JobPool()
        self.filesystem_mutex = Lock()

    def show_page(self, page_name, parameters=None):
        """
        Show the page corresponding to the name passed as parameters
        :param page_name: the name of the page to display
        :param parameters: the page parameters
        """
        # Construct the frame if it does not already exist
        if page_name not in self.pages.keys():
            if parameters is None:
                parameters = {}
            self.pages[page_name] = self.pages_class[page_name](parent=self)

        # Hide the currently displayed page
        if self.current_page is not None:
            self.current_page.pack_forget()

        # Display the requested page
        self.current_page = self.pages[page_name]
        self.current_page.pack(side="top", fill="both", expand=True)
        if parameters is None:
            self.current_page.refresh()
        else:
            self.current_page.refresh(**parameters)
        self.current_page.tkraise()

    def close(self, event=None):
        """
        Close the window
        :param event: the event that triggered the call to the function (not used)
        """
        # Stop all tasks
        self.pool.stop()

        # Destroy the window
        self.destroy()

