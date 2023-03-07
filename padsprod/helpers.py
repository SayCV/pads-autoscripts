"""
Various helper functions that tockloader uses. Mostly for interacting with
users in a nice way.
"""

import argparse
import binascii
import string
import sys

import colorama
import questionary


def set_terminal_title(title):
    if sys.stdout.isatty():
        sys.stdout.write(colorama.ansi.set_title(title))
        sys.stdout.flush()
