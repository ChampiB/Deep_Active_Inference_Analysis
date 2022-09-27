import json
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from gui.DataStorage import DataStorage
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
        self.conf = DataStorage.get("conf")
        self.window = DataStorage.get("window")

        # Change background color and configure AgentFrame
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(1, weight=120)
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
            self.canvas_frame.columnconfigure(i, weight=1, uniform="true")

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
        for i, text in enumerate(["Agent", "Environment", "Status[dd:hh:mm:ss]", "Host", "Hardware"]):
            label = LabelFactory.create(self.canvas_frame, text=text, theme="dark", font_size=14)
            label.grid(row=0, column=i, pady=5, padx=5, sticky="nsew")
        separator = ttk.Separator(self.canvas_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=5, sticky="nsew")

        # Create table's rows
        row_index = 2
        for job in jobs:
            # Load job json
            self.window.filesystem_mutex.acquire()
            with open(jobs_directory + job, "r") as job_file:
                job_json = json.load(job_file)
            self.window.filesystem_mutex.release()

            # Create one table row
            bg = self.conf.colors["dark_gray"] if row_index % 2 != 0 else self.conf.colors["gray"]
            row = tk.Frame(self.canvas_frame, bg=bg)
            for i in range(5):
                row.columnconfigure(i, weight=1, uniform="true")
            row.grid(row=row_index, column=0, columnspan=5, pady=5, sticky="nsew")

            # Update job if it is running on the server
            if "job_id" in job_json.keys():
                job_json = ServerSSH.refresh_job(job_json, self.project_page.project_name)

            # Create row's columns
            for i, key in enumerate(["agent", "env", "status", "host", "hardware"]):
                text = job_json[key].replace(".json", "")
                if key == "status" and text == "running":
                    if "execution_time" in job_json.keys():
                        text += "[" + job_json["execution_time"] + "]"
                    else:
                        start_time = datetime.strptime(job_json["start_time"], "%m/%d/%Y, %H:%M:%S")
                        execution_time = self.get_execution_time(start_time, datetime.now())
                        text += "[" + execution_time + "]"

                theme = "dark" if row_index % 2 != 0 else "gray"
                label = LabelFactory.create(row, text=text, theme=theme)
                label.grid(row=0, column=i, pady=5, sticky="nsew")
            row_index += 1
            self.scrollbar.bind_wheel(self, recursive=True)
            self.refresh()

    @staticmethod
    def get_execution_time(start_time, end_time):
        """
        Compute the execution time
        :param start_time: the starting time
        :param end_time: the ending time
        :return: the execution time as a string
        """
        execution_time = end_time - start_time
        duration_in_s = execution_time.total_seconds()
        days = divmod(duration_in_s, 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)
        seconds = divmod(minutes[1], 1)
        execution_time = f"{int(minutes[0]):02}:{int(seconds[0]):02}"
        if hours[0] != 0 or days[0] != 0:
            execution_time = f"{int(hours[0])}:02:{execution_time}"
        if days[0] != 0:
            execution_time = f"{int(days[0])}:{execution_time}"
        return execution_time

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
