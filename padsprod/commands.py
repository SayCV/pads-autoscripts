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

from . import sch_util, pcb_util

logger = logging.getLogger(__name__)

def run_info(args):
    if args.input is None:
        logger.error("Please provide input file!")
        sys.exit(1)
    input = path(args.input).absolute()

    in_format = args.in_format
    if in_format is None:
        in_format = input.suffix.lstrip('.')
    if in_format is None:
        logger.error("No input format found")
        sys.exit(1)

    if in_format == 'sch':
        board_file = input
        set_visible = False
        sch = sch_util.SCH(board_file, set_visible)
        sch.info()
        sch.close()
    elif in_format == 'pcb':
        board_file = input
        set_visible = False
        pcb = pcb_util.PCB(board_file, set_visible)
        pcb.info()
        pcb.close()
    else:
        logger.info(f"Info Command Unimplemented! -- {in_format}")

def run_export(args):
    if args.input is None:
        logger.error("Please provide input file!")
        sys.exit(1)
    input = path(args.input).absolute()
    file_name = input.stem
    if not input.exists():
        logger.error("Input file non exist")
        sys.exit(1)

    in_format = args.in_format
    if in_format is None:
        in_format = input.suffix.lstrip('.')
    if in_format is None:
        logger.error("Input format not found")
        sys.exit(1)

    out_format = args.out_format
    if out_format is None:
        logger.error("Output format not found")
        sys.exit(1)

    output = args.output
    if output is None:
        output = path.joinpath(input.parent, file_name + '.' + out_format)

    if in_format == 'sch':
        logger.info(f"TODO! <- {in_format}")
        if out_format == 'pdf':
            sch_file = input
            visible = True
            sch = sch_util.SCH(sch_file, visible)
            #sch.run_macro_ppcb_reset_default_palette()
            #sch.run_macro_ppcb_export_pdf(output, 'Top')
            #sch.run_macro_ppcb_export_pdf(output, 'Bottom')
            sch.close(False)
        elif out_format == 'txt':
            sch_file = input
            visible = True
            sch = sch_util.SCH(sch_file, visible)
            sch.export_ascii(output)
            #sch.close()
        else:
            logger.error("Output format not support")
            sys.exit(1)
        logger.status(f"Export to {out_format} done.")
    elif in_format == 'pcb':
        if out_format == 'pdf':
            board_file = input
            visible = False
            pcb = pcb_util.PCB(board_file, visible)
            pcb.run_macro_ppcb_reset_default_palette()
            pcb.run_macro_ppcb_export_pdf(output, 'Top')
            pcb.run_macro_ppcb_export_pdf(output, 'Bottom')
            pcb.close()
        elif out_format == 'asc':
            board_file = input
            visible = False
            pcb = pcb_util.PCB(board_file, visible)
            pcb.export_ascii(output)
            pcb.close()
        else:
            logger.error("Output format not support")
            sys.exit(1)
        logger.status(f"Export to {out_format} done.")
    else:
        logger.info(f"Export Command Unimplemented! <- {in_format}")

def run_renamerefs(args):
    if args.input is None:
        logger.error("Please provide input file!")
        sys.exit(1)
    input = path(args.input).absolute()
    file_name = input.stem
    if not input.exists():
        logger.error("Input file non exist")
        sys.exit(1)

    in_format = args.in_format
    if in_format is None:
        in_format = input.suffix.lstrip('.')
    if in_format is None:
        logger.error("Input format not found")
        sys.exit(1)

    out_format = args.out_format if args.out_format else in_format

    output = args.output

    if in_format == 'sch':
        logger.info(f"TODO! <- {in_format}")

        sch_file = input
        visible = False
        sch = sch_util.SCH(sch_file, visible)
        sch.run_renamerefs()
        save = True
        if output:
            sch.save_as(output)
            save = False
        sch.close(save=save)
        logger.status(f"Renamerefs {out_format} done.")
    elif in_format == 'pcb':
        logger.status(f"Renamerefs {out_format} done.")
    else:
        logger.info(f"Renamerefs Command Unimplemented! <- {in_format}")
