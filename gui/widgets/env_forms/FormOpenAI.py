import json
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.frames.EnvironmentFrame import EnvironmentFrame
from gui.widgets.modern.ButtonFactory import ButtonFactory


class FormOpenAI(tk.Frame):
    """
    A creation form for an open AI gym environment
    """

    # Store list of all atari games
    all_atari_games = [
        "ALE/VideoPinball-v5",
        "ALE/Boxing-v5",
        "ALE/Breakout-v5",
        "ALE/StarGunner-v5",
        "ALE/Robotank-v5",
        "ALE/Atlantis-v5",
        "ALE/CrazyClimber-v5",
        "ALE/Gopher-v5",
        "ALE/DemonAttack-v5",
        "ALE/NameThisGame-v5",
        "ALE/Krull-v5",
        "ALE/Assault-v5",
        "ALE/RoadRunner-v5",
        "ALE/Kangaroo-v5",
        "ALE/Jamesbond-v5",
        "ALE/Tennis-v5",
        "ALE/Pong-v5",
        "ALE/SpaceInvaders-v5",
        "ALE/BeamRider-v5",
        "ALE/Tutankham-v5",
        "ALE/KungFuMaster-v5",
        "ALE/Freeway-v5",
        "ALE/TimePilot-v5",
        "ALE/Enduro-v5",
        "ALE/FishingDerby-v5",
        "ALE/UpNDown-v5",
        "ALE/IceHockey-v5",
        "ALE/Qbert-v5",
        "ALE/Hero-v5",
        "ALE/Asterix-v5",
        "ALE/BattleZone-v5",
        "ALE/WizardOfWor-v5",
        "ALE/ChopperCommand-v5",
        "ALE/Centipede-v5",
        "ALE/BankHeist-v5",
        "ALE/Riverraid-v5",
        "ALE/Zaxxon-v5",
        "ALE/Amidar-v5",
        "ALE/Alien-v5",
        "ALE/Venture-v5",
        "ALE/Seaquest-v5",
        "ALE/DoubleDunk-v5",
        "ALE/Bowling-v5",
        "ALE/MsPacman-v5",
        "ALE/Asteroids-v5",
        "ALE/Frostbite-v5",
        "ALE/Gravitar-v5",
        "ALE/PrivateEye-v5",
        "ALE/MontezumaRevenge-v5"
    ]

    def __init__(self, parent, env, file):
        """
        Constructor
        :param parent: the parent widget
        :param env: the environment that must be displayed or None if a new environment must be created
        :param file: the file of the environment that must be displayed or None if a new environment must be created
        """
        super().__init__(parent)
        self.conf = AnalysisConfig.instance
        self.config(background=self.conf.colors["dark_gray"])
        self.parent = parent.master.master
        self.project_page = self.parent.master.master.master.master
        self.env = env
        self.source_file = file

        # Configure columns weights
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Create the create button
        text = "Create" if env is None else "Update"
        self.create_button = ButtonFactory.create(
            self, text=text, theme="blue", command=self.create_or_update_open_ai_env
        )
        self.create_button.grid(row=0, column=2, pady=15, ipady=5, sticky="nsew")

        # Create the play button
        if env is not None:
            self.play_button = ButtonFactory.create(self, text="Play", theme="blue", command=self.play)
            self.play_button.grid(row=0, column=1, pady=15, padx=5, ipady=5, ipadx=5, sticky="nsew")

    def play(self):
        """
        Play the environment
        """
        env = self.create_or_update_open_ai_env()
        self.parent.play(env)

    def create_or_update_open_ai_env(self):
        """
        Create the environment file on the file system
        """
        # Get environments requested by users
        env_name = self.parent.env_name_entry.get()
        envs = [env_name] if env_name.lower() != "all atari games" else FormOpenAI.all_atari_games

        # Get environment directory
        envs_directories = self.conf.projects_directory + self.project_page.project_name + "/environments/"
        env_dic = None
        for env in envs:

            # Get the environment file name
            file_name = env.replace("/", "_") + ".json"

            # Check that the environment is valid
            if not env.startswith("ALE/"):
                env = f"ALE/{env}"
            if env not in FormOpenAI.all_atari_games:
                print(f"Environment '{env}' is not a valid Atari game.")
                continue

            # Check if the project exist or not
            target_file = envs_directories + file_name
            source_file = target_file if self.source_file is None else self.source_file
            env_creation = self.source_file is None
            if not EnvironmentFrame.can_update_be_performed(envs_directories, source_file, target_file, env_creation):
                continue

            # Write the description of the new agent on the filesystem
            file = open(target_file, "a")
            env_dic = {
                "name": env,
                "module": "environments.impl.OpenAI",
                "class": "OpenAI"
            }
            json.dump(env_dic, file, indent=2)

        # Refresh project tree and display empty frame in the project page
        self.project_page.project_tree.refresh(self.project_page.project_name)
        return env_dic

    def refresh(self):
        """
        Refresh the OpenAI form
        """
        text = "Create" if self.env is None else "Update"
        self.create_button.config(text=text)
