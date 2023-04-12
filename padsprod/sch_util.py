
import datetime
import enum
import functools
import logging
import os
import re
import traceback
from pathlib import Path as path
from string import Template
from typing import List

from mputils import *

from padsprod.helper import PADSPROD_ROOT

from .color_constants import colors
from .sch_constants import *

logger = logging.getLogger(__name__)

strPLogUnit = ['Current', 'Database', 'Mils', 'Inch', 'Metric', 'DrawArea']

objSchItem = [
    'Background', 'Selection', 'Connection', 'Bus',      'Line',        'Part',     'HierarchicalComp', 'Text',
    'TextBox',    'RefDes',    'RefDesBox',  'PartType', 'PartTypeBox', 'PartText', 'PartTextBox',      'PinNumber',
    'PinNumberBox', 'NetName', 'NetNameBox', 'Field', 'FieldBox'
]

plogAnnotationScopeUpdateEntireDesign = 0
plogAnnotationScopeUpdateSelection = 1
plogAnnotationActionResetReferenceToQuestionMark = 2
plogAnnotationActionIncrementalReferenceUpdate = 3
plogAnnotationTypeLeftRight = 4
plogAnnotationTypeTopBottom = 5

class PLogPdfColorSchemeSetting(enum.Enum):
    plogPdfColorOnBlackBackground = 0

    plogPdfColorOnWhiteBackground = 1

    plogPdfBlackOnWhiteBackground = 2


class PLogObjColorType(enum.Enum):
    plogDocumentColorBackground = 0

    plogDocumentColorSelection = 1

    plogDocumentColorConnection = 2

    plogDocumentColorBus = 3

    plogDocumentColorLine = 4

    plogDocumentColorPart = 5

    plogDocumentColorHierarchicalComp = 6

    plogDocumentColorText = 7

    plogDocumentColorTextBox = 8

    plogDocumentColorRefDes = 9

    plogDocumentColorRefDesBox = 10

    plogDocumentColorPartType = 11

    plogDocumentColorPartTypeBox = 12

    plogDocumentColorPartText = 13

    plogDocumentColorPartTextBox = 14

    plogDocumentColorPinNumber = 15

    plogDocumentColorPinNumberBox = 16

    plogDocumentColorNetName = 17

    plogDocumentColorNetNameBox = 18

    plogDocumentColorField = 19

    plogDocumentColorFieldBox = 20


class PLogDefaultPaletteColorList(enum.Enum):
    ID0 = colors['black']
    ID1 = colors['navy']
    ID2 = colors['green']
    ID3 = colors['teal']
    ID4 = colors['maroon']
    ID5 = colors['purple']
    ID6 = colors['olive']
    ID7 = colors['gray']
    ID8 = colors['silver']
    ID9 = colors['blue']
    ID10 = colors['green1']
    ID11 = colors['aqua']
    ID12 = colors['red']
    ID13 = colors['magenta']
    ID14 = colors['yellow']
    ID15 = colors['white']
    ID16 = colors['yellow5']
    ID17 = colors['teal1']
    ID18 = colors['springgreen4']
    ID19 = colors['deepskyblue']
    ID20 = colors['cadmiumorange1']
    ID21 = colors['warmgrey1']
    ID22 = colors['rawsienna1']
    ID23 = colors['deeppink2']
    ID24 = colors['lightgoldenrod4']
    ID25 = colors['teal2']
    ID26 = colors['forestgreen1']
    ID27 = colors['darkslategray1']
    ID28 = colors['indianred1']
    ID29 = colors['silver1']
    ID30 = colors['cadmiumyellow1']
    ID31 = colors['maroon1']

    @staticmethod
    def get_idx(color_name):
        for idx, val in enumerate(PLogDefaultPaletteColorList):
            if colors[color_name] == val.value:
                return idx
        return 0

    @staticmethod
    def get_value_by_idx(idx):
        for _idx, val in enumerate(PLogDefaultPaletteColorList):
            if idx == _idx:
                return PLogDefaultPaletteColorList(val).value
        return PLogDefaultPaletteColorList.ID0.value


mcrPLogCmdList = {
    "PLogResetDefaultPaletteMacro": "Macro1.mcr",
    "PLogExportPdfMacro": "Macro2.mcr",
}


class SCH(object):
    def __init__(self, args, board_file, visible):
        macro_dir = path.joinpath(PADSPROD_ROOT, 'macros')
        if not path.exists(macro_dir):
            path.mkdir(macro_dir)

        logger.status(f'Opening: {board_file}')
        self.args = args
        self.board_file = board_file
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        self.app = self.mputils.PADSSCHApplication()
        self.app.Visible = visible
        self.board = IPowerLogicDoc(self.app.OpenDocument(board_file))
        self.sheets = self.board.Sheets
        self.multi_parts = []
        self.components_class = {}

        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'PADS Logic Version: {self.app.Version}')
        logger.status(f'SCH Name: {self.board.Name}')
        if self.board.Name == 'default.sch' and not self.board.Name == board_file.name:
            logger.warning("No input file found")
            pass

    def info(self):
        logger.info(f'This SCH file includes Components: {self.board.Components.Count}, Sheets: {self.sheets.Count}')
        for sht_idx, _sheet in enumerate(self.sheets):
            sheet = IPowerLogicSheet(_sheet)
            _name = bytes(sheet.Name, encoding='raw_unicode_escape')
            _name = _name.decode('gbk')
            logger.info(f'Page{sht_idx+1}: {_name}')

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

        #self.set_obj_color_by_name(page, color_idxs)
        macro_file = self._config_macro_plog_export_pdf(pdf, page)
        self.run_macro(macro_file)

        _name = bytes(sheet_name, encoding='raw_unicode_escape')
        _name = _name.decode('gbk')
        logger.status(f'Export to pdf from {_name} sheet.')

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

    def reset_components_ref_by_sheet(self, sheet: IPowerLogicSheet, components: List):
        sht_idx, _ = self.get_sheet_by_name(sheet.Name)
        for comp in components:
            plogComp = IPowerLogicComp(comp["obj"])
            new_ref = f"sht{sht_idx}" + comp["old_ref"]
            comp['tmp_ref'] = new_ref

            try:
                plogComp.Name = new_ref
            except BaseException as e:
                logging.error(e.args)
                logging.error(comp["old_ref"])
                traceback.print_exc()

        return components

    def resorted_components_ref_by_sheet(self, sheet: IPowerLogicSheet, components: List, sort_type = plogAnnotationTypeLeftRight):
        def my_sorted_left_right(a, b):
            if a["px"] - b["px"] > 1:
                return 1 # b, a
            elif a["px"] - b["px"] < 1:
                return -1 # a, b
            return 0  # a = b
        def my_sorted_top_bottom(a, b):
            if a["py"] - b["py"] < 1:
                return 1 # b, a
            elif a["py"] - b["py"] > 1:
                return -1 # a, b
            return 0  # a = b
        def custom_sorted(a, b):
            if sort_type == plogAnnotationTypeLeftRight:
                return my_sorted_left_right(a, b)
            return my_sorted_top_bottom(a, b)
        
        sht_idx, _ = self.get_sheet_by_name(sheet.Name)
        _sorted_comps = sorted(components, key=functools.cmp_to_key(my_sorted_left_right))
        _sorted_comps = sorted(components, key=functools.cmp_to_key(my_sorted_top_bottom))

        if False:
            old_ref_point_values = []
            new_ref_point_values = []
            for _comp in components:
                old_ref_point_values.append(f'{_comp["old_ref"]:6s} {_comp["px"]:10.2f} {_comp["py"]:10.2f}')
            for _comp in _sorted_comps:
                new_ref_point_values.append(f'{_comp["old_ref"]:6s} {_comp["px"]:10.2f} {_comp["py"]:10.2f}')
            point_file = path(self.board_file).with_suffix(f'.sch{sht_idx}-old-point.txt')
            point_file.write_text('\n'.join(old_ref_point_values), encoding='utf-8')
            point_file = path(self.board_file).with_suffix(f'.sch{sht_idx}-new-point.txt')
            point_file.write_text('\n'.join(new_ref_point_values), encoding='utf-8')

        for _, comp in enumerate(_sorted_comps):
            plogComp = IPowerLogicComp(comp["obj"])
            new_ref = comp["old_ref_list"][0] + str(self.components_class[comp["class"]]['current'])

            try:
                plogComp.Name = new_ref
            except BaseException as e:
                logging.error(e.args)
                logging.error(comp["old_ref"])
                traceback.print_exc()

            comp['new_ref'] = new_ref
            self.components_class[comp["class"]]["current"] = self.components_class[comp["class"]]["current"] + 1

        return components

    def run_renamerefs(self):
        
        # Reset components ref
        comp = []
        for idx, _sheet in enumerate(self.sheets):
            sheet = IPowerLogicSheet(_sheet)
            _comps = self.get_components_by_sheet(sheet)
            _comps = self.reset_components_ref_by_sheet(sheet, _comps)
            comp.append(_comps)

        # Rename components ref
        for idx, _sheet in enumerate(self.sheets):
            sheet = IPowerLogicSheet(_sheet)
            #_comps = self.get_components_by_sheet(sheet)
            _comps = comp[idx]
            _comps = self.resorted_components_ref_by_sheet(sheet, _comps)

        logger.info(f'Total components: {sum(len(idx) for idx in comp)}, Total components class: {len(self.components_class)}')

        rename_ref_map_values = []
        ref_point_values = []
        for sht in comp:
            for _comp in sht:
                rename_ref_map_values.append(f"{_comp['old_ref']} -> {_comp['new_ref']}")
                ref_point_values.append(f'{_comp["old_ref"]:6s} {_comp["new_ref"]:6s} {_comp["px"]:10.2f} {_comp["py"]:10.2f}')
            rename_ref_map_values.append("")
            ref_point_values.append("")
        map_file = path(self.board_file).with_suffix('.sch-refs-renamed-map.txt')
        map_file.write_text('\n'.join(rename_ref_map_values), encoding='utf-8')
        logger.info(f'The part map file saved as {map_file}.')
        if False:
            point_file = path(self.board_file).with_suffix('.sch-refs-renamed-point.txt')
            point_file.write_text('\n'.join(ref_point_values), encoding='utf-8')
            logger.info(f'The part point file saved as {point_file}.')
