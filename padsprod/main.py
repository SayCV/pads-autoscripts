#!/usr/bin/env python3

"""
### Main command line interface for padsprod.

Each `padsprod` command is mapped to a function which calls the correct
padsprod class function. 
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
from . import commands
from ._version import __version__
from .exceptions import PadsprodException

logger = logging.getLogger(__name__)

################################################################################
# Setup and parse command line arguments
################################################################################


def command_export(args):
    print("padsprod version: {}".format(__version__))
    logger.debug("called args: " + str(args))
    commands.run_export(args)

def command_renamerefs(args):
    print("padsprod version: {}".format(__version__))
    logger.debug("called args: " + str(args))
    commands.run_renamerefs(args)

def command_info(args):
    print("padsprod version: {}".format(__version__))
    commands.run_info(args)

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
    parent.add_argument(
        "-i", "--input",
        dest='input',
        help="Open file path",
        default=None,
    )
    parent.add_argument(
        "-o", "--output",
        dest='output',
        help="Save file path",
        default=None,
    )

    # Get the list of arguments before any command
    before_command_args = parent.parse_known_args()

    # The top-level parser object
    parser = argparse.ArgumentParser(parents=[parent])

    # Parser for all sch related commands
    parent_sch = argparse.ArgumentParser(add_help=False)
    parent_sch.add_argument(
        "--page",
        default=0,
        type=int,
        help="The sch sheet page.",
    )
    parent_sch.add_argument(
        "--enable-hyperlinks-attr",
        action="store_true",
        help="Create hyperlinks that will display part attributes.",
    )
    parent_sch.add_argument(
        "--enable-hyperlinks-nets",
        action="store_true",
        help="Create hyperlinks that will pan through nets.",
    )
    parent_sch.add_argument(
        "--pdf-color-scheme",
        type=int,
        #metavar='[0, 1, 2]',
        help="The color scheme setting.",
        choices=[0, 1, 2],
        default=2,
    )

    # Parser for all pcb related commands
    parent_pcb = argparse.ArgumentParser(add_help=False)
    parent_pcb.add_argument(
        "--layer",
        default=0,
        type=int,
        help="The pcb layer.",
    )

    # Parser for all output formatting related flags shared by multiple
    # commands.
    parent_format = argparse.ArgumentParser(add_help=False)
    parent_format.add_argument(
        "-f", "-r",
        "--from", "--read",
        dest='in_format',
        metavar='FORMAT',
        help="sch|pcb",
        choices=["sch", "pcb"],
        default=None,
    )
    parent_format.add_argument(
        "-t", "-w",
        "--to", "--write",
        dest='out_format',
        metavar='FORMAT',
        help="sch|pcb|asc|txt|pdf",
        choices=["sch", "pcb", "asc", "txt", "pdf"],
        default=None,
    )

    # Support multiple commands for this tool
    subparser = parser.add_subparsers(title="Commands", metavar="")

    # Command Groups
    #
    # Python argparse doesn't support grouping commands in subparsers as of
    # January 2021 :(. The best we can do now is order them logically.

    export = subparser.add_parser(
        "export",
        parents=[parent, parent_sch, parent_pcb, parent_format],
        help="Export from the provided sch and pcb file",
    )
    export.set_defaults(func=command_export)

    renamerefs = subparser.add_parser(
        "renamerefs",
        parents=[parent, parent_sch, parent_pcb, parent_format],
        help="Rename references of the provided sch and pcb file",
    )
    renamerefs.set_defaults(func=command_renamerefs)

    info = subparser.add_parser(
        "info",
        parents=[parent, parent_sch, parent_pcb, parent_format],
        help="Verbose information about the provided sch and pcb file",
    )
    info.set_defaults(func=command_info)

    argcomplete.autocomplete(parser)
    args, unknown_args = parser.parse_known_args()

    # Warn about unknown arguments, suggest padsprod update.
    if len(unknown_args) > 0:
        logger.warning(
            "Unknown arguments passed. You may need to update padsprod.")
        for unknown_arg in unknown_args:
            logger.warning('Unknown argument "{}"'.format(unknown_arg))

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
            logger.error(e)
            sys.exit(1)
    else:
        logger.error("Missing Command.\n")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
