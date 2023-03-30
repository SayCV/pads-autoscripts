
import datetime
import enum
import functools
import logging
import os
import re
import subprocess
from pathlib import Path as path
from string import Template
import traceback
from typing import List

from mputils import *

from padsprod.helpers import PADSPROD_ROOT

from .color_constants import colors
from .sch_constants import *

logger = logging.getLogger(__name__)

class HYP(object):
    def __init__(self, args, board_file, visible):
        macro_dir = path.joinpath(PADSPROD_ROOT, 'macros')
        if not path.exists(macro_dir):
            path.mkdir(macro_dir)

        logger.status(f'Opening: {board_file}')
        self.args = args
        self.board_file = board_file
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        # 
        self.app = self.mputils.HLApplication()
        self.board = IHLBoard(self.app.OpenFile(board_file))
        self.app.Visible = visible
        self.Nets = self.board.Nets
        self.multi_parts = []
        self.components_class = {}

        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'HyperLynx Version: {self.app.Version}')
        logger.status(f'HYP Name: {self.board.FileName}')
        if self.board.FileName == 'default.sch' and not self.board.FileName == board_file.name:
            logger.warning("No input file found")
            pass

    def info(self):
        logger.info(f'This HYP file includes Components: {self.board.Components.Count}, Nets: {self.Nets.Count}')

    def set_visible(self, visible):
        self.app.Visible = visible

    def get_total_sheet_count(self):
        return self.sheets.Count

    def get_sheet_by_id(self, sheet_id):
        for idx, _sheet in enumerate(self.sheets):
            if idx + 1 == sheet_id:
                sheet = IPowerLogicSheet(_sheet)
                return sheet
        return None

    def get_sheet_name(self, sheet_id):
        return self.get_sheet_by_id(sheet_id).Name

    def get_sheet_by_name(self, sheet_name):
        for idx, _sheet in enumerate(self.sheets):
            if _sheet.Name == sheet_name:
                sheet = IPowerLogicSheet(_sheet)
                return (idx + 1, sheet)
        return (None, None)

    def export_ascii(self, file):
        ver = plogASCIIVerCurrent
        self.board.ExportASCII(file, ver)

    def run_macro(self, macro_file):
        dirname = PADSPROD_ROOT
        file = path.joinpath(dirname, 'macros', macro_file)
        self.app.RunMacro(file, 'Macro1')

    def run_macro_plog_reset_default_palette(self):
        dirname = PADSPROD_ROOT
        origin = mcrPLogCmdList['PLogResetDefaultPaletteMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_1)
        d = {}
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def _config_macro_plog_export_pdf(self, pdf, page):
        dirname = PADSPROD_ROOT
        origin = mcrPLogCmdList['PLogExportPdfMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        _MACRO_OPS = MACRO_OPS_2
        page_idx = page - 1
        if page == 0:
            pdf = path.joinpath(pdf.parent, pdf.stem + '-sch.pdf')
            page_idx = 0
        else:
            pdf = path.joinpath(pdf.parent, pdf.stem + f'-sch-p{page:02}.pdf')
            _MACRO_OPS = MACRO_OPS_3

        t = Template(_MACRO_OPS)
        d = {
            "pdf_file": pdf,
            "enable_open_pdf": 'false',
            "enable_hyperlinks_attr": self.args.enable_hyperlinks_attr,
            "enable_hyperlinks_nets": self.args.enable_hyperlinks_nets,
            "color_scheme_setting": self.args.pdf_color_scheme,
            "page_idx": page_idx,
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        return macro_file

    def run_macro_plog_export_pdf(self, pdf, page):
        if page == 0:
            sheet_name = 'all'
        else:
            sheet_name = self.get_sheet_name(page)

        color_idxs = []
        for _, item in enumerate(PLogObjColorType):
            color_idx = PLogDefaultPaletteColorList.get_idx('silver')
            # if item == PLogObjColorType.ppcbLayerColorPad:
            #    color_idx = PLogDefaultPaletteColorList.get_idx('silver')
            # elif item == PLogObjColorType.ppcbLayerColorRefDes:
            #    color_idx = PLogDefaultPaletteColorList.get_idx('white')
            color_idxs.append(color_idx)

        logger.status(f'Export to pdf from {sheet_name} sheet.')
        #self.set_obj_color_by_name(page, color_idxs)
        macro_file = self._config_macro_plog_export_pdf(pdf, page)
        self.run_macro(macro_file)

    def save_as(self, file):
        self.board.SaveAs(file)

    def close(self, save=True):
        if save:
            self.board.SaveAsTemp(path(self.app.DefaultFilePath) / 'default.sch')
        self.app.Quit()

    def get_components_by_sheet(self, sheet: IPowerLogicSheet):
        components = []
        for Comp in sheet.Components:
            comp = IPowerLogicComp(Comp)
            ref_list = re.compile(u'([a-zA-Z]*)(\d+)').findall(comp.Name)
            gates = comp.Gates
            gate = gates[0]
            
            component = {}
            component['obj'] = comp
            component['px'] = gate.PositionX
            component['py'] = gate.PositionY
            component['old_ref_list'] = ref_list[0]
            component['old_ref'] = comp.Name
            component['tmp_ref'] = None
            component['new_ref'] = None
            component['class'] = ref_list[0][0]
            component['pages_name'] = [sheet.Name]

            if component['class'] in self.components_class:
                self.components_class[component['class']]['count'] = self.components_class[component['class']]['count'] + 1
            else:
                _component_class = {}
                _component_class["count"] = 1
                _component_class["current"] = 1
                self.components_class[component['class']] = _component_class

            # One component split to multi part
            found_part = False
            if gates.Count > 1:
                logger.warning(
                    f'Detected more than one gate `{gates.Count} of `{comp.Name}` in {sheet.Name} at {__file__} line {sys._getframe().f_lineno}')
                for _multi_part in self.multi_parts:
                    if _multi_part["tmp_ref"].upper() == comp.Name:
                        found_part = True
                        _multi_part["pages_name"].append(sheet.Name)
                        break
                if not found_part:
                    self.multi_parts.append(component)
            if found_part:
                logger.warning(f"It's had collected and ignoring other multi parts: {comp.Name} in {sheet.Name}!")
                continue

            components.append(component)
        return components
