import os
import tkinter as tk

from gui.AnalysisConfig import AnalysisConfig


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

        # Store the configuration
        self.conf = AnalysisConfig.instance

        # Display window in full-screen mode
        self.attributes("-fullscreen", True)

        # Pressing the escape key closes the window
        self.bind('<Escape>', self.close)

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

        # List of all available pages' class and instance, as well as the currently displayed page
        self.pages_class = AnalysisWindow.get_all_pages_class()
        self.pages = {}
        self.current_page = None

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
        self.destroy()

    @staticmethod
    def get_all_pages_class():
        """
        Retrieve all the available pages
        :return: all the available pages
        """
        # Get pages directory
        path = os.path.dirname(os.path.abspath(__file__)) + "/../pages/"

        # For each file in the pages directory
        pages = {}
        for file in os.listdir(path):
            # Check that the file is a python file but not the init.py
            if not file.endswith('.py') or file == '__init__.py':
                continue

            # Get the class and module
            class_name = file[:-3]
            class_module = __import__("gui.pages." + class_name, fromlist=[class_name])

            # Get the pages' class
            module_dict = class_module.__dict__
            for obj in module_dict:
                if isinstance(module_dict[obj], type) and module_dict[obj].__module__ == class_module.__name__:
                    pages[class_name] = getattr(class_module, obj)
        return pages
