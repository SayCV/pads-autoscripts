"""

"""

import argparse
import binascii
import string
import sys
import os
import logging
from pathlib import Path as path

import colorama
import questionary

from . import pcb_util

logger = logging.getLogger(__name__)

def run_info(args):
    input = path(args.input).absolute()

    in_format = args.in_format
    if in_format is None:
        in_format = input.suffix.lstrip('.')
    if in_format is None:
        logger.error("No input format found")
        sys.exit(1)

    if in_format == 'sch':
        logger.info(f"Info Command Unimplemented! -- {in_format}")
    elif in_format == 'pcb':
        board_file = input
        set_visible = False
        pcb = pcb_util.PCB(board_file, set_visible)
        pcb.info()
        pcb.close()
    else:
        logger.info(f"Info Command Unimplemented! -- {in_format}")

def run_export(args):
    input = path(args.input).absolute()
    file_name = input.stem

    in_format = args.in_format
    if in_format is None:
        in_format = input.suffix.lstrip('.')
    if in_format is None:
        logger.error("No input format found")
        sys.exit(1)

    out_format = args.out_format
    if out_format is None:
        logger.error("No output format found")
        sys.exit(1)

    output = args.output
    if output is None:
        output = path.joinpath(input.parent, file_name + '.' + out_format)

    if in_format == 'sch':
        logger.info(f"Export Command Unimplemented! <- {in_format}")
    elif in_format == 'pcb':
        board_file = input
        set_visible = False
        pcb = pcb_util.PCB(board_file, set_visible)
        pcb.run_macro_ppcb_reset_default_palette()
        pcb.run_macro_ppcb_export_pdf(output)
        pcb.close()
        logger.status(f"Export to {out_format} Done.")
    else:
        logger.info(f"Export Command Unimplemented! <- {in_format}")
