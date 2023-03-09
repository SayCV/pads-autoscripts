"""

"""

import argparse
import binascii
import string
import sys
import os
from pathlib import Path as path

import colorama
import questionary

from . import pcb_util

def run(args):
    dirname = path(__file__).resolve().parent.parent
    input = path.joinpath(dirname, args.input)
    file_name = input.stem
    #file_suffix = input.suffix

    if args.output is None:
        args.output = path.joinpath(input.parent, file_name + '.' + args.output_format)

    board_file = input
    pcb = pcb_util.PCB(board_file)
    pcb.get_layer_color_by_id(1)
    #pcb.get_layer_color_by_name("Bottom")
    pcb.run_macro_ppcb_reset_default_palette()
    pcb.run_macro_ppcb_export_pdf(args.output)
    #pcb.close()
    pass
