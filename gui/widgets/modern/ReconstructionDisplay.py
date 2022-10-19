import os.path
import tkinter as tk
from PIL import Image, ImageTk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory


class ReconstructionDisplay(tk.Frame):
    """
    A widgets displaying the images reconstructed by the agents.
    """

    def __init__(self, parent, value=0, jobs_json=None, **kwargs):
        """
        Create the image reconstruction display
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
        self.images = []
        self.current_shift = 0
        self.n_images_per_row = -1
        self.empty = True

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
        # Clear reconstruction display
        self.empty = True
        self.update_idletasks()
        self.images.clear()
        for widget in self.winfo_children():
            widget.destroy()

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

    def display_job(self, directory, agent, env, row_id):
        """
        Display the requested job
        :param directory: the job directory
        :param agent: the agent directory
        :param env: the env directory
        :param row_id: the index of the row in which to display the job
        """
        # Create label frame to hold images
        text = f"Reconstruction of {agent} on {env.replace('ALE/', '')} after {int(self.value / 1000)}K iterations"
        lf = LabelFrameFactory.create(self, text=text)
        lf.grid(row=row_id, column=0, ipady=5, ipadx=5, padx=25, sticky="nsew")

        # Display observations and reconstructed images
        ratio = 4
        i = 0
        while i != self.n_images_per_row:
            try:
                image = Image.open(f"{directory}/obs-{i + self.current_shift}.png")
                if self.n_images_per_row == -1:
                    self.n_images_per_row = int(self.winfo_width() / (image.width * ratio)) - 1
                image = self.pre_process(image, ratio)
                label = LabelFactory.create(lf, image=image, theme="dark")
                self.images.append(image)
                label.config(highlightthickness=2, highlightbackground=self.conf.colors["blue"])
                label.grid(row=0, column=i % self.n_images_per_row + 1, pady=(15, 5), padx=5)

                r_image = Image.open(f"{directory}/reconstructed-obs-{i + self.current_shift}.png")
                r_image = self.pre_process(r_image, ratio)
                label = LabelFactory.create(lf, image=r_image, theme="dark")
                self.images.append(r_image)
                label.config(highlightthickness=2, highlightbackground=self.conf.colors["blue"])
                label.grid(row=1, column=i % self.n_images_per_row + 1, pady=5, padx=5)
                self.empty = False
            except FileNotFoundError as e:
                print(e)
            i += 1

        for j in range(self.n_images_per_row + 1):
            lf.columnconfigure(j, weight=1)

        _, h = lf.grid_size()
        for j in range(h):
            text = "Reconstructed images:" if j % 2 == 1 else "Ground truth:"
            label = LabelFactory.create(lf, text=text, theme="dark")
            label.grid(row=j, column=0, pady=5, padx=5)

        # Create the navigation buttons
        prev_btn = ButtonFactory.create(lf, text="Previous", command=self.decrease_index, theme="blue")
        prev_btn.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        next_btn = ButtonFactory.create(lf, text="Next", command=self.increase_index, theme="blue")
        next_btn.grid(row=2, column=self.n_images_per_row, sticky="nsew", padx=10, pady=5)

    def decrease_index(self):
        """
        Decrease the current index, defining which images to display
        """
        self.current_shift -= self.n_images_per_row
        if self.current_shift < 0:
            self.current_shift = 0
        self.update_display()

    def increase_index(self):
        """
        Increase the current index, defining which images to display
        """
        self.current_shift += self.n_images_per_row
        self.update_display()

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
