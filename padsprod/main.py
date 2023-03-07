#!/usr/bin/env python3

"""
### Main command line interface for padsprod.

Each `padsprod` command is mapped to a function which calls the correct
padsprod class function. This file also handles discovering and reading in TAB
files.
"""

import argparse
import atexit
import binascii
import functools
import glob
import logging
import os
import subprocess
import sys
import textwrap
import time
import urllib.parse

import argcomplete

from . import helpers
from ._version import __version__
from .exceptions import PadsprodException

################################################################################
# Setup and parse command line arguments
################################################################################


def command_info(args):
    print("padsprod version: {}".format(__version__))
    logging.status("Showing all support ops...")


def main():
    """
    Read in command line arguments and call the correct command function.
    """

    # Cleanup any title the program may set
    atexit.register(helpers.set_terminal_title, "")

    # Setup logging for displaying background information to the user.
    logging.basicConfig(
        style="{", format="[{levelname:<7}] {message}", level=logging.INFO
    )
    # Add a custom status level for logging what padsprod is doing.
    logging.addLevelName(25, "STATUS")
    logging.Logger.status = functools.partialmethod(logging.Logger.log, 25)
    logging.status = functools.partial(logging.log, 25)

    # Create a common parent parser for arguments shared by all subparsers. In
    # practice there are very few of these since padsprod supports a range of
    # operations.
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--debug", action="store_true", help="Print additional debugging information"
    )
    parent.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print padsprod version and exit",
    )

    # Get the list of arguments before any command
    before_command_args = parent.parse_known_args()

    # The top-level parser object
    parser = argparse.ArgumentParser(parents=[parent])

    # Parser for all output formatting related flags shared by multiple
    # commands.
    parent_format = argparse.ArgumentParser(add_help=False)
    parent_format.add_argument(
        "--output-format",
        help="Address where apps are located",
        choices=["terminal", "json"],
        default="terminal",
    )

    # Support multiple commands for this tool
    subparser = parser.add_subparsers(title="Commands", metavar="")

    # Command Groups
    #
    # Python argparse doesn't support grouping commands in subparsers as of
    # January 2021 :(. The best we can do now is order them logically.

    info = subparser.add_parser(
        "info",
        parents=[parent, parent_format],
        help="Verbose information about the connected board",
    )
    info.set_defaults(func=command_info)

    argcomplete.autocomplete(parser)
    args, unknown_args = parser.parse_known_args()

    # Warn about unknown arguments, suggest padsprod update.
    if len(unknown_args) > 0:
        logging.warning(
            "Unknown arguments passed. You may need to update padsprod.")
        for unknown_arg in unknown_args:
            logging.warning('Unknown argument "{}"'.format(unknown_arg))

    # Concat the args before the command with those that were specified
    # after the command. This is a workaround because for some reason python
    # won't parse a set of parent options before the "command" option
    # (or it is getting overwritten).
    for key, value in vars(before_command_args[0]).items():
        if getattr(args, key) != value:
            setattr(args, key, value)

    # Change logging level if `--debug` was supplied.
    if args.debug:
        logging.getLogger("").setLevel(logging.DEBUG)

    # Handle deprecated arguments.

    if hasattr(args, "func"):
        try:
            args.func(args)
        except PadsprodException as e:
            logging.error(e)
            sys.exit(1)
    else:
        logging.error("Missing Command.\n")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
