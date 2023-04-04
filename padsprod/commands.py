"""

"""

import logging
import sys
from pathlib import Path as path

from . import hyp_util, pcb_util, sch_util
from .exceptions import PadsprodException

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
        try:
            sch = sch_util.SCH(args, board_file, set_visible)
            sch.info()
        except PadsprodException as e:
            logger.error(e)
        sch.close()
    elif in_format == 'pcb':
        board_file = input
        set_visible = False
        try:
            pcb = pcb_util.PCB(args, board_file, set_visible)
            pcb.info()
        except PadsprodException as e:
            logger.error(e)
        pcb.close()
    elif in_format == 'hyp' or in_format == 'pjh':
        board_file = input
        set_visible = False
        try:
            hyp =hyp_util.HYP(args, board_file, set_visible)
            hyp.save_components_nets()
        except PadsprodException as e:
            logger.error(e)
        hyp.close()
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
        logger.info(f"Running...")
        if out_format == 'pdf':
            sch_file = input
            visible = False
            try:
                if (args.start_page is not None and args.end_page is not None and args.start_page > args.end_page):
                    logger.error(f"Provided start page({args.start_page}) over than the end page({args.end_page})!")
                    sch.close()
                    return

                sch = sch_util.SCH(args, sch_file, visible)
                if args.start_page is not None and args.start_page > sch.get_total_sheet_count():
                    logger.warning(f"Provided start page({args.start_page}) over than the sch real sheet count({sch.get_total_sheet_count()})!")
                    args.start_page = sch.get_total_sheet_count()
                    #sch.close()
                    #return
                elif args.end_page is not None and args.end_page > sch.get_total_sheet_count():
                    logger.warning(f"Provided end page({args.end_page}) over than the sch real sheet count({sch.get_total_sheet_count()})!")
                    args.end_page = sch.get_total_sheet_count()
                    #sch.close()
                    #return
                elif args.page > sch.get_total_sheet_count():
                    logger.error(f"Provided sheet number({args.page}) over than the sch real sheet count({sch.get_total_sheet_count()})!")
                    sch.close()
                    return
                start_page = args.start_page
                end_page = args.end_page
                if args.start_page:
                    if args.end_page is None:
                        end_page = sch.get_total_sheet_count()
                if args.end_page:
                    if args.start_page is None:
                        start_page = 1

                sch.run_macro_plog_reset_default_palette()

                if start_page and end_page:
                    for page in range(start_page, end_page + 1):
                        sch.run_macro_plog_export_pdf(output, page)
                else:
                    sch.run_macro_plog_export_pdf(output, args.page)
            except PadsprodException as e:
                logger.error(e)
            sch.close()
        elif out_format == 'txt':
            sch_file = input
            visible = False
            try:
                sch = sch_util.SCH(args, sch_file, visible)
                sch.export_ascii(output)
            except PadsprodException as e:
                logger.error(e)
            sch.close()
        else:
            logger.error("Output format not support")
            sys.exit(1)
        logger.status(f"Export to {out_format} done.")
    elif in_format == 'pcb':
        if out_format == 'pdf':
            board_file = input
            visible = False
            try:
                pcb = pcb_util.PCB(args, board_file, visible)
                if args.layer > pcb.get_total_layer_count():
                    logger.error(f"Provided layer number({args.layer}) over than the pcb real layer count({pcb.get_total_layer_count()})!")
                    pcb.close()
                    return

                pcb.run_macro_ppcb_reset_default_palette()
                #pcb.run_macro_ppcb_export_pdf(output, 'Top')
                #pcb.run_macro_ppcb_export_pdf(output, 'Bottom')
                if args.layer == 0:
                    for idx in range(1, pcb.get_electrical_layer_count() + 1):
                        pcb.run_macro_ppcb_export_pdf(output, idx)
                    drawing_layer_id = pcb.get_layer_id('Drill Drawing')
                    pcb.run_macro_ppcb_export_pdf(output, drawing_layer_id)
                else:
                    pcb.run_macro_ppcb_export_pdf(output, args.layer)
            except PadsprodException as e:
                logger.error(e)
            pcb.close()
        elif out_format == 'asc':
            board_file = input
            visible = False
            try:
                pcb = pcb_util.PCB(args, board_file, visible)
                pcb.export_ascii(output)
            except PadsprodException as e:
                logger.error(e)
            pcb.close()
        elif out_format == 'hyp':
            board_file = input
            visible = False
            try:
                pcb = pcb_util.PCB(args, board_file, visible)
                pcb.export_hyp(output)
            except PadsprodException as e:
                logger.error(e)
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
        logger.info(f"Running...")

        sch_file = input
        visible = False
        try:
            sch = sch_util.SCH(args, sch_file, visible)
            sch.run_renamerefs()
            if output is None:
                output = input.with_suffix('.refs-renamed.sch')
            sch.save_as(path(output).absolute())
        except PadsprodException as e:
            logger.error(e)
        sch.close(False)
        logger.status(f"Renamerefs {out_format} done.")
    elif in_format == 'pcb':
        logger.status(f"Renamerefs {out_format} done.")
    else:
        logger.info(f"Renamerefs Command Unimplemented! <- {in_format}")

def run_simu(args):
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

    if in_format == 'hyp' or in_format == 'pjh':
        board_file = input
        set_visible = False
        try:
            hyp = hyp_util.HYP(args, board_file, set_visible)
            hyp.save_components_nets()
        except PadsprodException as e:
            logger.error(e)
        hyp.close()
    else:
        logger.info(f"Simu Command Unimplemented! -- {in_format}")
