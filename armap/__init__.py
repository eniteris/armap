# TODO: Add license

__all__ = [
    "run_armap",
]

import sys
from collections.abc import Sequence

__version__ = "0.1.0"

# pylint: disable=import-outside-toplevel


def run_armap(argv: Sequence[str] | None = None) -> None:
    """Run armap cli.
    
    :param argv: arguments from command line call.
    """

    from .cli import Run as ArmapRun

    try:
        ArmapRun(argv or sys.argv[1:]).run()
    except KeyboardInterrupt:
        sys.exit(1)
