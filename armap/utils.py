# TODO: Add license

from typing import Any
import tomli

def read_toml(file) -> dict[str, Any] | None:
    """Read a TOML file"""
    try:
        toml_dict = tomli.load(open(file, "rb"))
    except tomli.TOMLDecodeError as e:
        print(f"Invalid TOML:\n{ e }")
        toml_dict = None
    except FileNotFoundError as e:
        print(f"File not found:\n{ e }")
        toml_dict = None
    except Exception as e:
        print(f"Unexpected exception:\n{ e }")
        toml_dict = None
    return toml_dict


def hex_to_rgb(hex_color : str) -> tuple[int]:
    """Convert a color in hex format to a rbg tuple."""
    return tuple(int(hex_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color : tuple[int]) -> str:
    """Convert a rgb tuple to a hex color representation"""
    return '#%02x%02x%02x' % rgb_color
