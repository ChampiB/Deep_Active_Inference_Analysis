import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class LabelFactory:
    """
    A class allowing the creation of labels of different types
    """

    conf = AnalysisConfig.instance

    @staticmethod
    def create(parent, text=None, image=None, theme="dark", font_size=None):
        """
        Create a label
        :param parent: the parent widget
        :param text: the label's text
        :param image: the label's image
        :param theme: the label's theme, i.e., "dark", "gray", "white" or "tooltip"
        :param font_size: the text font size
        :return: the created label
        """
        if theme == "dark":
            return LabelFactory.create_dark_label(parent, text, image, font_size)
        if theme == "gray":
            return LabelFactory.create_gray_label(parent, text, image, font_size)
        if theme == "white":
            return LabelFactory.create_white_label(parent, text, image, font_size)
        if theme == "tooltip":
            return LabelFactory.create_tooltip_label(parent, text, image, font_size)

    @staticmethod
    def create_dark_label(parent, text, image, font_size):
        """
        Create a dark label
        :param parent: the parent widget
        :param text: the label's text
        :param image: the label's image
        :param font_size: the text font size
        :return: the created label
        """
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if font_size is None:
            font_size = 14

        return tk.Label(
            parent,
            image=image,
            text=text,
            font=(LabelFactory.conf.font["name"], font_size, LabelFactory.conf.font["style"]),
            background=LabelFactory.conf.colors["dark_gray"],
            foreground=LabelFactory.conf.colors["light_text"],
            **parameters
        )

    @staticmethod
    def create_gray_label(parent, text, image, font_size):
        """
        Create a gray label
        :param parent: the parent widget
        :param text: the label's text
        :param image: the label's image
        :param font_size: the text font size
        :return: the created label
        """
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if font_size is None:
            font_size = 14

        return tk.Label(
            parent,
            image=image,
            text=text,
            font=(LabelFactory.conf.font["name"], font_size, LabelFactory.conf.font["style"]),
            background=LabelFactory.conf.colors["gray"],
            foreground=LabelFactory.conf.colors["light_text"],
            **parameters
        )

    @staticmethod
    def create_white_label(parent, text, image, font_size):
        """
        Create a white label
        :param parent: the parent widget
        :param text: the label's text
        :param image: the label's image
        :param font_size: the text font size
        :return: the created label
        """
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if font_size is None:
            font_size = 12

        return tk.Label(
            parent,
            image=image,
            textvariable=text,
            font=(LabelFactory.conf.font["name"], font_size, LabelFactory.conf.font["style"]),
            background="white",
            **parameters
        )

    @staticmethod
    def create_tooltip_label(parent, text, image, font_size):
        """
        Create a tooltip label
        :param parent: the parent widget
        :param text: the label's text
        :param image: the label's image
        :param font_size: the text font size
        :return: the created label
        """
        parameters = {}
        if text is not None and image is not None:
            parameters["compound"] = tk.LEFT
        if font_size is None:
            font_size = 10

        return tk.Label(
            parent,
            text=text,
            image=image,
            justify=tk.LEFT,
            background=LabelFactory.conf.colors["light_gray"],
            highlightthickness=1,
            font=(LabelFactory.conf.font["name"], font_size, LabelFactory.conf.font["style"]),
            foreground=LabelFactory.conf.colors["light_text"],
        )
