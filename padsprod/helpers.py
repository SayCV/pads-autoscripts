"""
Various helper functions that padsprod uses. Mostly for interacting with
users in a nice way.
"""

import argparse
import binascii
import string
import sys
from pathlib import Path as path

import colorama
import questionary


PADSPROD_ROOT = path(__file__).resolve().parent

def set_terminal_title(title):
    if sys.stdout.isatty():
        sys.stdout.write(colorama.ansi.set_title(title))
        sys.stdout.flush()
