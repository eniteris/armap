# TODO: Add license

import os
from collections.abc import Sequence

from .config_parser import ConfigParser
from .map_generator import MapGenerator
from .legends_parser import LegendParser
from .exceptions import *


class Run():
    """Helper class to use as main with 'run(*sys.argv[1:])'."""

    def __init__(self, argv: Sequence[str] | None = None) -> None:
        # TODO: wrap in try except
        # TODO: add config except clause
        self.config = ConfigParser()
        if argv:
            self.config.create_parser()
            self.config.parse_args(argv)

        if not self.config.map_input_folder:
            # TODO: change for raise legends folder exception
            # TODO: add legends folder except clause
            print("No map data folders present.")

        # TODO: add legends except clause
        self.legends = LegendParser(self.config).parse(self.config.map_input_folder)

        #self.debug_mode = self.config.debug

    def run(self) -> None:
        """TODO: add description"""
        map_tools = MapGenerator()
        df_map = None
        for color_name in self.config.selected_colors:
            if not self.palette_dict.get(color_name, None):
                # TODO: replace with exception
                print(f"{color_name} not found! Skipping color!")

            # TODO: wrap in try except
            df_map = map_tools.generate_map(self.legends, self.config, color_name)

            if self.debug_mode and df_map.any():
                map_tools.display(df_map)

        print("Done!")
