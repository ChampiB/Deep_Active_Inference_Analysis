import os
import threading
import time
import tkinter as tk
import PIL
from PIL import Image, ImageTk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory


class PolicyDisplay(tk.Frame):
    """
    A widgets displaying agents' policies.
    """

    def __init__(self, parent, value=0, jobs_json=None, **kwargs):
        """
        Create the policy display
        :param parent: the parent widget
        :param value: the training iteration for which policies must be displayed
        :param jobs_json: the json describing the jobs whose policies must be displayed
        :param kwargs: additional (key-value) parameters
        """
        self.conf = AnalysisConfig.instance
        super().__init__(parent, bg=self.conf.colors["dark_gray"], highlightthickness=0, **kwargs)

        self.columnconfigure(0, weight=1)

        self.value = value
        self.jobs_json = {} if jobs_json is None else jobs_json
        self.images = {}
        self.labels = {}
        self.lfs = {}
        self.empty = True
        self.current_index = 0
        self.thread_running = False
        self.bind("<<RequireLoadImage>>", self.update_policies)

    def set_value(self, value):
        """
        Set the value of the policy and refresh the display
        :param value: the new value
        """
        self.value = value
        self.update_display()

    def set_jobs(self, jobs_json):
        """
        Set the value of the policy and refresh the display
        :param jobs_json: the new value
        """
        self.jobs_json = jobs_json
        self.update_display()

    def update_display(self):
        """
        Update the reconstructed images display.
        """
        # Update policy display size
        self.empty = True
        self.update_idletasks()

        # Display all jobs
        for row_id, job_json in enumerate(self.jobs_json):
            if job_json is None:
                continue
            env = job_json['env'].replace('_', '/').replace('.json', '')
            agent = job_json['agent'].replace('.json', '')

            # Check that the directory exist
            directory = f"{self.conf.logging_directory}/{env}/{agent}/{int(self.value * 100 / 50000)}/"
            # TODO remove * 100 / 50000
            if not os.path.exists(directory):
                continue
            self.display_job(directory, agent, env, row_id)
        if self.empty:
            self.grid_remove()
        else:
            self.grid()

        # Play policy in background
        if not self.thread_running:
            self.thread_running = True
            threading.Thread(target=self.play_policies_in_background).start()

    def play_policies_in_background(self):
        """
        Play agent policies in background
        """
        while self.thread_running:
            for row_id, job_json in enumerate(self.jobs_json):
                if job_json is None:
                    continue
                env = job_json['env'].replace('_', '/').replace('.json', '')
                agent = job_json['agent'].replace('.json', '')

                # Check that the directory exist
                directory = f"{self.conf.logging_directory}/{env}/{agent}/{int(self.value * 100 / 50000)}/"
                try:
                    image = Image.open(f"{directory}/real-obs-{self.current_index}.png")
                    self.images[f"{agent}&{env}"] = image
                    self.current_index += 1
                except FileNotFoundError as e:
                    self.current_index = 0
                    print(e)

            # Update images
            self.event_generate("<<RequireLoadImage>>")
            time.sleep(0.2)

    def update_policies(self, event=None):
        """
        Display the policies
        :param event: the event that triggered the call to this function
        """
        for key in self.labels.keys():
            if type(self.images[key]) != PIL.ImageTk.PhotoImage:
                ratio = self.winfo_width() / (self.images[key].width * 5)
                self.images[key] = self.pre_process(self.images[key], ratio)
            self.labels[key].config(image=self.images[key])
            self.update_idletasks()

    def display_job(self, directory, agent, env, row_id=-1):
        """
        Display the requested job
        :param directory: the job directory
        :param agent: the agent directory
        :param env: the env directory
        :param row_id: the index of the row in which to display the job
        """
        # Display policy of the agent
        try:
            image = Image.open(f"{directory}/real-obs-{self.current_index}.png")
            ratio = self.winfo_width() / (image.width * 5)
            image = self.pre_process(image, ratio)
            key = f"{agent}&{env}"
            if key not in self.labels.keys():
                text = f"Policy of {agent} on {env.replace('ALE/', '')} after {int(self.value / 1000)}K iterations"
                self.lfs[key] = LabelFrameFactory.create(self, text=text)
                self.lfs[key].grid(row=row_id, column=0, ipady=5, ipadx=5, padx=25, sticky="nsew")
                self.lfs[key].columnconfigure(0, weight=1)
                self.labels[key] = LabelFactory.create(self.lfs[key], image=image, theme="dark")
                self.images[key] = image
                self.labels[key].grid(row=0, column=0, pady=(15, 5), padx=5, sticky="nsew")
            else:
                self.images[f"{agent}&{env}"] = image
                if row_id != -1:
                    self.labels[f"{agent}&{env}"].config(image=image)
            self.empty = False
            self.current_index += 1
        except FileNotFoundError as e:
            self.current_index = 0
            print(e)

    @staticmethod
    def pre_process(image, ratio):
        """
        Resize the image and turn it into a PhotoImage
        :param image: the image to resize
        :param ratio: the ratio by which the image size should be multiplied
        :return: the created PhotoImage
        """
        image = image.resize((int(image.width * ratio), int(image.height * ratio)), Image.NEAREST)
        return ImageTk.PhotoImage(image)

    def stop(self):
        """
        Stop active thread
        """
        self.thread_running = False
