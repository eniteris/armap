# TODO: Add license

from collections.abc import Sequence

from .config_parser import ConfigParser
from .config import Configuration
from .map_generator import MapGenerator
from .legends_parser import LegendParser

class Run():
    """Helper class to use as main with 'run(*sys.argv[1:])'."""

    def __init__(self, argv: Sequence[str] | None = None) -> None:
        # TODO: wrap in try except
        # TODO: add config except clause
        # self.config = Configuration()
        self.config = ConfigParser()
        if argv:
            self.config.create_parser()
            self.config.parse_args(argv)

        if not self.config.map_input_folder:
            # TODO: change for raise legends folder exception
            # TODO: add legends folder except clause
            # TODO: validate if folder contain minimum requirements
            print("Folders for map data not found.")

        # TODO: add legends except clause
        self.legends = LegendParser(self.config)
        self.legends.parse(self.config.map_input_folder)

        self.debug_mode = self.config.debug_mode

    def run(self) -> None:
        """TODO: add description"""
        map_tools = MapGenerator(self.config, self.legends, self.legends.maps["el"])
        for color_name in self.config.selected_colors:
            if not self.config.palette_dict.get(color_name, None):
                # TODO: replace with exception
                print(f"{color_name} not found! Skipping color!")

            t1 = None
            if self.config.interactive and map_tools.canvas.any():
                import threading
                t1 = threading.Thread(target=map_tools.display_thread)
                t1.start()

            # TODO: wrap in try except
            map_tools.generate_map(color_name)

            if t1:
                t1.join()

        print("Done!")
