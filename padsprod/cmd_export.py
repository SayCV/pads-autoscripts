"""

"""

import argparse
import binascii
import string
import sys

import colorama
import questionary

from . import pcb_util

def run(args):
    board_file = args.file
    pcb = pcb_util.PCB(board_file)
    pcb.get_layer_color_by_id(1)
    pcb.get_layer_color_by_name("Bottom")
    pcb.close()
    pass
