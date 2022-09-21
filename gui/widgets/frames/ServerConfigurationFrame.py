import json
import os
import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory


class ServerConfigurationFrame(tk.Frame):
    """
    A class that allows the user to select existing server configuration or create new ones
    """

    def __init__(self, parent):
        """
        Constructor
        :param parent: the parent widget
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parent and assets
        self.parent = parent
        self.assets = AnalysisAssets.instance
        self.conf = AnalysisConfig.instance

        # Place the project renaming frame in the center od the screen
        self.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Place the project renaming frame in the center od the screen
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Change background color
        self.config(
            background=parent.conf.colors["gray"], highlightthickness=2,
            highlightcolor=parent.conf.colors["blue"], highlightbackground=parent.conf.colors["blue"]
        )

        # Add closing button
        self.closing_button = ButtonFactory.create(
            self, image=self.assets.get("close_button"), command=self.place_forget, theme="light"
        )
        self.closing_button.grid(row=0, column=2, pady=10, padx=10, sticky="ne")

        # Add the server name label
        self.server_name_label = LabelFactory.create(self, text="Server name:", theme="gray")
        self.server_name_label.grid(row=1, column=0, padx=(10, 0), pady=(5, 10), sticky="nsw")

        # Add the server name entry
        self.server_name_entry = Entry(self, help_message="server name")
        self.server_name_entry.grid(row=1, column=1, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="nsew")

        # Add the username label
        self.username_label = LabelFactory.create(self, text="Username:", theme="gray")
        self.username_label.grid(row=2, column=0, padx=(10, 0), pady=(5, 10), sticky="nsw")

        # Add the username entry
        self.username_entry = Entry(self, help_message="username")
        self.username_entry.grid(row=2, column=1, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="nsew")

        # Add the new project description label
        self.hostname_label = LabelFactory.create(self, text="Hostname:", theme="gray")
        self.hostname_label.grid(row=3, column=0, padx=(10, 0), pady=(5, 10), sticky="nsw")

        # Add the new project description entry
        self.hostname_entry = Entry(self, help_message="hostname")
        self.hostname_entry.config(width=40)
        self.hostname_entry.grid(row=3, column=1, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="nsew")

        # Add the update button
        self.update_button = ButtonFactory.create(
            self, text="Add", command=self.new_ssh_server, theme="blue"
        )
        self.update_button.grid(row=4, column=1, columnspan=2, pady=10, padx=(0, 10), ipady=10, sticky="nsew")

    def new_ssh_server(self):
        """
        Change the server configuration
        """
        # Check that the new project name and description is not empty
        self.username_entry.remove_help_message()
        self.hostname_entry.remove_help_message()
        username = self.username_entry.get()
        hostname = self.hostname_entry.get()
        server_name = self.server_name_entry.get()
        if username == "" or hostname == "" or server_name == "":
            self.place_forget()
            return

        # Add server configuration
        self.conf.servers[server_name] = {
            "username": username,
            "hostname": hostname
        }
        self.place_forget()
        self.parent.top_bar.update_servers()
