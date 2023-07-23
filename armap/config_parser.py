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
        self.debug_mode: bool = False
        self.interactive: bool = False
        self.wait: float = 0.3
        self.site_check: bool = False
        self.territory_check: bool = False
        self.structure_check: bool = False
        self.process_road: bool = False
        self.brook: bool = False
        self.grid_draw: bool = False
        self.world_label_check = False
        self.other_labels_check = False
        self.min_pop: int = 1000
        self.min_cities: int = 5
        self.required_cities: list = []
        self.parser = None
        self.map_input_folder = DEFAULT_MAPS_PATH
        self.color_folder = DEFAULT_COLORS_FOLDER
        self.palette_dict = self.read_palettes(self.color_folder)
        self.selected_colors = "all"
        self.vegetation_type = "Green"
        self.vegetation_green = 0.8
        self.vegetation_alpha = 1

        # TODO: increase the defaults here

        self.parse_file(DEFAULT_CONFIG_FILE)

        if self.selected_colors == "all":
            self.selected_colors = list(self.palette_dict.keys())
        else:
            self.selected_colors = list(self.selected_colors)

    def create_parser(self) -> None:
        """Create the argument parser and add the arguments."""
        parser = argparse.ArgumentParser(
            prog="ARMap",
            description=DESCRIPTION,
        )

        # TODO: Review args

        # Global parameters
        parser.add_argument(
            "-d", "--debug",
            action="store_true",
            default=False,
            type=bool,
            help="enable debug mode"
        )
        parser.add_argument(
            "-e", "--interactive",
            action="store_true",
            default=False,
            type=bool,
            help="enable interactive mode"
        )

        # Creations parameters
        parser.add_argument(
            "-n", "--new",
            action="store",
            choices=["color", "parameters"],
            type=str,
            help="assistant to create new color or parameters file"
        )
        parser.add_argument(
            "-l", "--list",
            action="store",
            choices=["color", "parameters"],
            type=str,
            help="list available colors"
        )

        # Map creation parameters
        parser.add_argument(
            "-p", "--parameters",
            action="store",
            type=str,
            help="parameters file"
        )
        parser.add_argument(
            "-c", "--colors",
            action="store",
            nargs="*",
            default="all",
            type=list,
            help="list of color palettes, enter 'all' if you \
            want to use all palettes, default is all available"
        )
        parser.add_argument(
            "-i", "--input",
            action="store",
            type=str,
            help=""
        )
        parser.add_argument(
            "-o", "--output",
            action="store",
            type=str,
            help=""
        )

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

        setattr(self, "palette_dict", self.read_palettes(self.color_folder))

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

    def convert_color(
            self, colors: dict[str, str]
        ) -> dict[int, tuple[int, int, int]]:
        """TODO: add description"""
        color_values = {}
        for k, v in colors.items():
            value = hex_to_rgb(v)
            color_values[int(k)] = value
        return color_values

    def read_palettes(
            self, folder: str
        ) -> dict[str, dict[int, tuple[int, int, int]]]:
        """Read the colors from a folder.

        :param folder (str): The path to the folder containing the color palettes.
        :return dict: A dictionary with the color palettes and their values.
        """
        palettes = {}
        color_files = os.listdir(folder)
        for f in color_files:
            file_name = os.path.join(folder, f)
            if color := read_toml(file_name):
                palettes[color["name"]] = self.convert_color(color["colors"])

        return palettes
