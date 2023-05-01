# TODO: Add license

import argparse
import pathlib
import os
from collections.abc import Sequence

from .utils import read_toml, hex_to_rgb

DESCRIPTION = "Automated map maker from Dwarf Fortress maps"
DEFAULT_COLORS_FOLDER = "resources/color-palettes/"
DEFAULT_FONT = "resources/DF-Curses-8x12.ttf"
DEFAULT_MAPS_PATH = "df-maps/"
DEFAULT_OUTPUT_PATH = "output/"
DEFAULT_CONFIG_FOLDER = "resources/configurations"
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_FOLDER, "default.toml")

class ConfigParser():
    """Provide the configurations to generate a DF map.
    
    Configuration will always load the default and then overwrite it.

    Presedence will be:
    default file > custom file (if any) > cli arguments (if any)
    """

    def __init__(self) -> None:
        """Init all needed configurations from default configuration file"""
        self.parser = None
        self.color_folder = DEFAULT_COLORS_FOLDER
        self.map_input_folder = DEFAULT_MAPS_PATH

        self.parse_file(DEFAULT_CONFIG_FILE)

        #if self._config.colors == "all":
        #    self.selected_colors = list(palette_dict.keys())
        #else:
        #    self.selected_colors = list(self._config.colors)

    def create_parser(self) -> None:
        """Create the argument parser and add the arguments."""
        parser = argparse.ArgumentParser(
            prog="ARMap",
            description=DESCRIPTION,
        )

        # Global parameters
        parser.add_argument("-d", "--debug", action="store_true",
                            default=False, help="enable debug mode")
        parser.add_argument("-e", "--interactive", action="store_true",
                            default=False, help="enable interactive mode")

        # Creations parameters
        parser.add_argument("-n", "--new", choices=["color", "parameters"],
                            help="")
        parser.add_argument("-l", "--list-colors", action="store_true",
                            default=False, help="")

        # Map creation parameters
        parser.add_argument("-p", "--parameters", action="store",
                            type=open, help="")
        parser.add_argument("-c", "--colors", nargs="*", default="all",
                            help="list of color palettes, enter 'all' if you \
                            want to use all palettes, default is all available")
        parser.add_argument("-f", "--font", action="store", )
        parser.add_argument("-v", "--vegetation", choices=["default", "green"],
                            default="default", help="")
        parser.add_argument("-g", "--grid", action="store_true",
                        default=False, help="Draw grid")
        parser.add_argument("-t", "--territory", action="store_true",
                        default=False, help="Draw territory")
        parser.add_argument("-b", "--brook", action="store_true",
                        default=False, help="Draw brook")
        parser.add_argument("-s", "--structure", action="store_true",
                        default=False, help="Draw structure")
        parser.add_argument("-r", "--road", action="store_true",
                    default=False, help="Draw road")
        parser.add_argument("-i", "--input", action="store",
                        type=pathlib.Path, help="")
        parser.add_argument("-o", "--output", action="store",
                        type=open, help="")

        self.parser = parser

    def parse_file(self, file: str) -> None:
        """Parse a file to generate default configurations"""
        if not (config_dict := read_toml(file)):
            # TODO: Replace with specific exception
            raise Exception()
        for k, v in config_dict.items():
            if isinstance(v, str) and len(v) == 7 and v[0] == "#":
                v = hex_to_rgb(v)
            setattr(self, k, v)

    def parse_args(self, argv: Sequence[str]) -> None:
        """Parse the argument variables from cli to overwrite defaults."""
        if self.parser:
            args = self.parser.parse_args(argv)
        else:
            # TODO: replace with specific exception
            raise Exception()

        # Overwrite defaults with a custom configuration file if present
        if dict(args._get_kwargs()).get("config_file", None):
            self.parse_file(args.config_file)

        for k, v in dict(args._get_kwargs()).items():
            if isinstance(v, str) and len(v) == 7 and v[0] == "#":
                v = hex_to_rgb(v)
            setattr(self, k, v)

        setattr(self, "palette_dict", self.read_palettes(self.color_folder))

    def convert_color(self, color):
        """TODO: add description"""
        color_values = {}
        for k, v in color.items():
            value = hex_to_rgb(v)
            color_values.update({int(k): value})
        return color_values

    def read_palettes(self, folder) -> dict:
        """Read the colors from a folder.

        :param folder (str): The path to the folder containing the color palettes.
        :return dict: A dictionary with the color palettes and their values.
        """
        palettes = {}
        color_palettes = os.listdir(folder)
        for color in color_palettes:
            file_name = os.path.join(folder, color)
            if color_config := read_toml(file_name):
                palettes[color_config["name"]] = self.convert_color(color_config["colors"])

        return palettes
