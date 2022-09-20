import json
import os
from PIL import Image, ImageTk
import numpy as np
import tkinter as tk
from json import JSONDecodeError
import threading
import time
from environments.EnvironmentFactory import EnvironmentFactory
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory
from gui.widgets.modern.Scrollbar import Scrollbar
import pygame


class EnvironmentFrame(tk.Frame):
    """
    A class allowing to create a new environment
    """

    tkinter_to_pygame = {
        24: pygame.K_q,
        25: pygame.K_w,
        26: pygame.K_e,
        27: pygame.K_r,
        28: pygame.K_t,
        29: pygame.K_y,
        30: pygame.K_u,
        31: pygame.K_i,
        32: pygame.K_o,
        33: pygame.K_p,
        38: pygame.K_a,
        39: pygame.K_s,
        40: pygame.K_d,
        41: pygame.K_f,
        42: pygame.K_g,
        43: pygame.K_h,
        44: pygame.K_j,
        45: pygame.K_k,
        46: pygame.K_l,
        52: pygame.K_z,
        53: pygame.K_x,
        54: pygame.K_c,
        55: pygame.K_v,
        56: pygame.K_b,
        57: pygame.K_n,
        58: pygame.K_m,
    }

    def __init__(self, parent, file=None):
        """
        Constructor
        :param parent: parent widget
        :param file: the environment file that must be displayed or None if a new environment must be created
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters passed as input
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Load environment from file
        try:
            project_name = parent.master.master.master.project_name
            file_name = self.conf.projects_directory + f"{project_name}/environments/{file}"
            file = open(file_name, "r")
            self.env = json.load(file)
            self.file = file_name
        except (JSONDecodeError, FileNotFoundError):
            self.env = None
            self.file = None

        self.default_env_name = "<environment name here>" if self.env is None else self.env["name"]

        # Get all the agent classes
        self.env_creation_forms = self.conf.get_all_classes(self.conf.env_forms_directory, "gui.widgets.env_forms.")
        self.env_names = [form.replace("Form", "") for form in self.env_creation_forms.keys()]

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=100)
        self.columnconfigure(2, weight=10)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=self.conf.colors["dark_gray"])
        self.canvas.grid(row=0, column=1, sticky="news")
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=3, sticky='nes')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')

        # Ask the user to create an agent
        text = "Create a new environment..." if self.env is None else f"Update environment: {self.env['name']}."
        self.new_env_label = LabelFactory.create(self.canvas_frame, text=text, font_size=22, theme="dark")
        self.new_env_label.grid(row=0, column=0, sticky="news", pady=50)

        # Create the general setting box
        self.general_settings = LabelFrameFactory.create(self.canvas_frame, text="General")
        self.general_settings.columnconfigure(0, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(1, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(2, weight=1, uniform="labelframe")
        self.general_settings.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

        self.env_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.env_name_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.env_name_entry = Entry(self.general_settings, help_message=self.default_env_name)
        self.env_name_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")

        self.environment_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.environment_template_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

        text = "SpritesEnvironment" if self.env is None else self.env["class"]
        self.env_template_combo_box = Combobox(
            self.general_settings, self.env_names, command=self.change_env_form, default_value=text
        )
        if file is not None:
            self.env_template_combo_box.lock()
        self.env_template_combo_box.grid(row=1, column=1, pady=(5, 10), padx=5, sticky="nsew")

        self.scrollbar.bind_wheel(self, recursive=True)
        self.env_form = None
        self.change_env_form()
        self.canvas.bind('<Configure>', self.frame_width)

        # Attributes used to play the environment
        self.last_key_pressed = None
        self.image_label = None
        self.reward_label = None
        self.image_env_state = None
        self.stop_env = False

        self.reward = 0
        self.image_main_thread = None

    def stop(self):
        """
        Stop all background tasks
        """
        self.stop_env = True

    def frame_width(self, event):
        """
        Configure the canvas frame width
        :param event: the event that triggered the call to this function
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_window, width=canvas_width)

    def change_env_form(self, event=None):
        """
        Change the agent template
        :param event: unused
        """
        class_name = "Form" + self.env_template_combo_box.get()
        if self.env_form is not None:
            self.env_form.grid_remove()
        self.env_form = self.env_creation_forms[class_name](self.canvas_frame, self.env, self.file)
        self.env_form.grid(row=2, column=0, pady=5, padx=5, sticky="new")
        self.scrollbar.bind_wheel(self.env_form, recursive=True)
        self.refresh()

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update environment form
        self.env_form.refresh()

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.env_form.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def can_update_be_performed(environments_directories, source_file, target_file, env_must_be_created):
        """
        Check whether the update can be applied or not
        :param environments_directories: the directory containing all the environments
        :param source_file: the source file
        :param target_file: the target file
        :param env_must_be_created: True, if an environment must be created, False if it must be updated
        :return: whether the update can be applied or not
        """
        # Get source and target base name
        target_base_name = os.path.basename(target_file)
        source_base_name = os.path.basename(source_file)

        # To create an environment, the target should not exist
        if env_must_be_created and target_base_name in os.listdir(environments_directories):
            print(f"Environment '{source_base_name}' already exist, new environment can't be created.")
            return False

        # To update an environment, the source should exist, but the target should not
        if not env_must_be_created:
            if source_base_name not in os.listdir(environments_directories):
                print(f"Environment source file '{source_base_name}' does not exist, cannot rename environment.")
                return False
            if source_base_name != target_base_name and target_base_name in os.listdir(environments_directories):
                print(f"Environment target file '{target_base_name}' already exist, cannot rename environment.")
                return False
            print(f"Environment '{source_base_name}' will be remove.")
            os.remove(source_file)
        return True

    def play(self, env):
        """
        Allow the user to play the environment
        :param env: the environment
        """
        # Remove old widgets
        self.canvas.delete("all")

        # Create the label used to display the environment's observations
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=15)
        self.canvas_frame.rowconfigure(2, weight=1)
        self.image_label = LabelFactory.create(self.canvas_frame, theme="dark")
        self.image_label.grid(row=1, column=1)
        self.reward_label = LabelFactory.create(
            self.canvas_frame, theme="dark", text=f"Loading the '{env['name']}' environment..."
        )
        self.reward_label.grid(row=2, column=1)
        x = self.canvas.winfo_width() / 2
        y = self.canvas.winfo_height() / 2
        self.canvas_frame_window = self.canvas.create_window(x, y, window=self.canvas_frame, anchor=tk.CENTER)

        # Keep track of last key pressed
        self.focus_force()
        self.bind('<KeyPress>', self.track_last_key)
        self.bind('<KeyRelease>', self.track_last_key_release)
        self.bind("<<RequireLoadImage>>", self.update_frame)

        # Play environment in background
        threading.Thread(target=self.play_env_in_background, args=(env,)).start()

    def update_frame(self, event=None):
        """
        Update the display of the image and reward
        :param event: the event that triggered the call to this function
        """
        self.image_env_state = ImageTk.PhotoImage(self.image_main_thread)
        self.image_label.config(image=self.image_env_state)
        self.canvas.update_idletasks()
        self.reward_label.config(text=f"Reward: {self.reward}")

    def play_env_in_background(self, env):
        """
        Allow the user to play the environment by launching a thread in background
        :param env: the environment to run
        """

        # Load environment
        env = EnvironmentFactory.create(env)
        keys_to_actions = env.get_keys_to_action()
        keys_to_actions = self.pre_process(keys_to_actions)

        # Retrieve the initial observation from the environment.
        obs = env.reset()

        # Let the user play the environment
        max_size = min(self.canvas.winfo_width(), self.canvas.winfo_height()) - 200
        while not self.stop_env:
            # Display environment state
            obs = obs.astype(np.uint8)
            w, h, _ = obs.shape
            ratio = max_size / max(w, h)
            img = Image.fromarray(obs).resize((int(w * ratio), int(h * ratio)), Image.NEAREST)
            self.image_main_thread = img
            self.event_generate("<<RequireLoadImage>>")

            # Select an action.
            time.sleep(0.2)
            if self.last_key_pressed is None or self.last_key_pressed not in keys_to_actions.keys():
                action = keys_to_actions[None]
            else:
                action = keys_to_actions[self.last_key_pressed]

            # Execute the action in the environment.
            obs, self.reward, done, _ = env.step(action)

            # Reset the environment if trial is over
            if done:
                obs = env.reset()

    def track_last_key(self, event):
        """
        Keep track of last keep pressed
        :param event: the event that triggered the call to this function
        """
        if event.keycode not in EnvironmentFrame.tkinter_to_pygame.keys():
            return
        self.last_key_pressed = EnvironmentFrame.tkinter_to_pygame[event.keycode]

    def track_last_key_release(self, event):
        """
        Keep track of last keep pressed
        :param event: the event that triggered the call to this function
        """
        if event.keycode not in EnvironmentFrame.tkinter_to_pygame.keys():
            return
        if self.last_key_pressed == EnvironmentFrame.tkinter_to_pygame[event.keycode]:
            self.last_key_pressed = None

    @staticmethod
    def pre_process(keys_to_actions):
        """
        Pre-process the keys to actions mapping
        :param keys_to_actions: the keys to actions mapping
        :return: the pre-processed keys to actions mapping
        """
        tmp = {}
        for keys, value in keys_to_actions.items():
            if isinstance(keys, tuple):
                for key in keys:
                    if key is None:
                        tmp[None] = value
                    else:
                        tmp[key] = value
            else:
                tmp[keys] = value
        return tmp

