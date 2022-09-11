import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class ButtonFactory:

    conf = AnalysisConfig.instance

    @staticmethod
    def create(parent, image=None, text=None, theme="dark", command=None, font_size=None):
        if theme == "dark":
            return ButtonFactory.create_dark_button(parent, image, text, command, font_size)
        if theme == "light":
            return ButtonFactory.create_light_button(parent, image, text, command, font_size)
        if theme == "blue":
            return ButtonFactory.create_blue_button(parent, image, text, command, font_size)
        if theme == "invisible_dark":
            return ButtonFactory.create_invisible_dark_button(parent, image, text, command, font_size)
        if theme == "red":
            return ButtonFactory.create_red_button(parent, image, text, command, font_size)
        if theme == "white":
            return ButtonFactory.create_white_button(parent, image, text, command, font_size)

    @staticmethod
    def create_blue_button(parent, image, text, command, font_size):
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.TOP
        if font_size is None:
            font_size = 14

        return tk.Button(
            parent,
            image=image,
            text=text,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            command=command,
            foreground=ButtonFactory.conf.colors["dark_text"],
            activeforeground=ButtonFactory.conf.colors["dark_text"],
            background=ButtonFactory.conf.colors["blue"],
            activebackground=ButtonFactory.conf.colors["dark_blue"],
            **parameters
        )

    @staticmethod
    def create_dark_button(parent, image, text, command, font_size):
        if font_size is None:
            font_size = 10

        return tk.Button(
            parent,
            image=image,
            text=text,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            command=command,
            background=ButtonFactory.conf.colors["dark_gray"],
            activebackground=ButtonFactory.conf.colors["gray"],
            foreground=ButtonFactory.conf.colors["light_text"],
            activeforeground=ButtonFactory.conf.colors["light_text"]
        )

    @staticmethod
    def create_invisible_dark_button(parent, image, text, command, font_size):
        if font_size is None:
            font_size = 10

        return tk.Button(
            parent,
            image=image,
            text=text,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            command=command,
            background=ButtonFactory.conf.colors["dark_gray"],
            activebackground=ButtonFactory.conf.colors["dark_gray"],
            foreground=ButtonFactory.conf.colors["light_text"],
            activeforeground=ButtonFactory.conf.colors["light_text"]
        )

    @staticmethod
    def create_red_button(parent, image, text, command, font_size):
        if font_size is None:
            font_size = 14

        return tk.Button(
            parent,
            image=image,
            text=text,
            command=command,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            foreground=ButtonFactory.conf.colors["dark_text"],
            activeforeground=ButtonFactory.conf.colors["dark_text"],
            background=ButtonFactory.conf.colors["red"],
            activebackground=ButtonFactory.conf.colors["dark_red"]
        )

    @staticmethod
    def create_light_button(parent, image, text, command, font_size):
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if font_size is None:
            font_size = 10

        return tk.Button(
            parent,
            image=image,
            text=text,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            command=command,
            background=ButtonFactory.conf.colors["gray"],
            activebackground=ButtonFactory.conf.colors["light_gray"],
            foreground=ButtonFactory.conf.colors["light_text"],
            activeforeground=ButtonFactory.conf.colors["light_text"],
            **parameters
        )

    @staticmethod
    def create_white_button(parent, image, text, command, font_size):
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if text is not None and image is None:
            parameters["anchor"] = "w"
        if font_size is None:
            font_size = 12

        return tk.Button(
            parent,
            image=image,
            text=text,
            highlightthickness=0,
            borderwidth=0,
            font=(ButtonFactory.conf.font["name"], font_size, ButtonFactory.conf.font["style"]),
            command=command,
            background="white",
            activebackground=ButtonFactory.conf.colors["light_text"],
            foreground="black",
            activeforeground="black",
            **parameters
        )
