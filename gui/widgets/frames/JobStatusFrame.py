import json
import threading
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from hosts.impl.ServerSSH import ServerSSH


class JobStatusFrame(tk.Frame):
    """
    A class displaying the job status
    """

    def __init__(self, parent, **kwargs):
        """
        Constructor
        :param parent: parent widget
        :param kwargs: the remaining arguments
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters passed as input
        self.parent = parent
        self.project_page = parent.master.master.master
        self.conf = AnalysisConfig.instance

        # Change background color and configure AgentFrame
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=100)
        self.columnconfigure(2, weight=10)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=self.conf.colors["dark_gray"], highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="news")
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=3, sticky='nes')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')
        for i in range(5):
            self.canvas_frame.columnconfigure(i, weight=1)

        # Display the jobs
        threading.Thread(target=self.display_jobs).start()

        self.scrollbar.bind_wheel(self, recursive=True)
        self.agent_form = None
        self.canvas.bind('<Configure>', self.frame_width)

    def display_jobs(self):
        """
        Display existing jobs
        """
        # Get all jobs
        jobs_directory = self.conf.projects_directory + self.project_page.project_name + "/jobs/"
        jobs = self.conf.get_all_files(jobs_directory)

        # Create header
        for i, text in enumerate(["Agent", "Environment", "Status", "Host", "Hardware"]):
            label = LabelFactory.create(self.canvas_frame, text=text, theme="dark")
            label.grid(row=0, column=i, pady=5, padx=5, sticky="nsew")

        # Create rows
        row_index = 1
        for job in jobs:
            job_file = open(jobs_directory + job, "r")
            job_json = json.load(job_file)
            print(job_json)
            print(job_json.keys())
            if "job_id" in job_json.keys():
                ServerSSH.refresh_job(job_json)
            for i, key in enumerate(["agent", "env", "status", "host", "hardware"]):
                text = job_json[key]
                if key == "status" and text == "running":
                    text += "[" + job_json["execution_time"] + "]"
                label = LabelFactory.create(self.canvas_frame, text=text, theme="dark")
                label.grid(row=row_index, column=i, pady=5, padx=5, sticky="nsew")
            row_index += 1
            self.scrollbar.bind_wheel(self, recursive=True)
            self.refresh()

    def frame_width(self, event):
        """
        Configure the canvas frame width
        :param event: the event that triggered the call to this function
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_window, width=canvas_width)

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update agent form idle tasks to let tkinter calculate buttons sizes
        self.canvas_frame.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def stop(self):
        """
        Stop all tasks running in background
        """
        pass
