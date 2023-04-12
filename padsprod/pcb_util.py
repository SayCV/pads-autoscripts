
import datetime
import enum
import functools
import logging
import os
import re
from pathlib import Path as path
from string import Template
from typing import Dict, List, Tuple

import toml
import win32con
import win32gui as wg
from mputils import *

from .color_constants import colors
from .exceptions import PadsprodException
from .helper import PADSPROD_ROOT
from .pcb_constants import *

logger = logging.getLogger(__name__)

strPPcbUnit = {
    'Current': 0,
    'Database': 1,
    'Mils': 2,
    'Inch': 3,
    'Metric': 4,
}

strPPcbDrawingType = {
    'Drw2Dline': 0,
    'DrwBoard': 1,
    'DrwCopper': 3,
    'DrwCopperPour': 6,
    'DrwCopperHatch': 7,
    'DrwCopperThermal': 8,
    'DrwKeepout': 9,
}

layerPcbItem = [
    'Trace',      'Via',           'Pad',    'Copper',   'Line',      'Text',    'Error',
    'OutlineTop', 'OutlineBottom', 'RefDes', 'PartType', 'Attribute', 'Keepout', 'PinNumber'
]


class PPcbLayerColorType(enum.Enum):
    ppcbLayerColorTrace = 0

    ppcbLayerColorVia = 1

    ppcbLayerColorPad = 2

    ppcbLayerColorCopper = 3

    ppcbLayerColorLine = 4

    ppcbLayerColorText = 5

    ppcbLayerColorError = 6

    ppcbLayerColorOutlineTop = 7

    ppcbLayerColorOutlineBottom = 8

    ppcbLayerColorRefDes = 9

    ppcbLayerColorPartType = 10

    ppcbLayerColorAttribute = 11

    ppcbLayerColorKeepout = 12

    ppcbLayerColorPinNumber = 13


class PPcbDefaultPaletteColorList(enum.Enum):
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
        for idx, val in enumerate(PPcbDefaultPaletteColorList):
            if colors[color_name] == val.value:
                return idx
        return 0

    @staticmethod
    def get_value_by_idx(idx):
        for _idx, val in enumerate(PPcbDefaultPaletteColorList):
            if idx == _idx:
                return PPcbDefaultPaletteColorList(val).value
        return PPcbDefaultPaletteColorList.ID0.value


mcrPPcbCmdList = {
    "PPcbResetDefaultPaletteMacro": "Macro1.mcr",
    "PPcbExportPdfMacro": "Macro2.mcr",
    "PPcbPourMangerMacro": "Macro3.mcr",
    "PPcbExportHypMacro": "Macro4.mcr",
    "PPcbDraftingText": "Macro5.mcr",
    "PPcbDeleteSelected": "Macro6.mcr",
}


class Layer(object):
    def __init__(self, pcb, layer_id):
        self.pcb = pcb
        self.layer_id = layer_id

    @staticmethod
    def from_name(pcb, layer_name):
        return Layer(pcb, pcb.get_layer_id(layer_name))

    def get_color(self):
        return self.pcb.get_layer_color(self.layer_id)

    def get_name(self):
        return self.pcb.get_layer_name(self.layer_id)


class TextConfig(object):
    def __init__(self, text='', text_px=0.0, text_py=0.0, text_height=0.0, line_width=0.0, layer_name='', mirrored=False):
        self.text = text
        self.text_px = text_px
        self.text_py = text_py
        self.text_height = text_height
        self.line_width = line_width
        self.layer_name = layer_name
        self.mirrored = mirrored

    def set_text(self, text):
        self.text = text

    def set_text_point(self, px, py):
        self.text_px = px
        self.text_py = py

    def set_text_height(self, text_height):
        self.text_height = text_height,

    def set_line_width(self, line_width):
        self.line_width = line_width,

    def set_layer_name(self, layer_name):
        self.layer_name = layer_name,

    def set_mirrored(self, mirrored):
        self.mirrored = mirrored,


class PCB(object):
    def __init__(self, args, board_file, visible):
        macro_dir = path.joinpath(PADSPROD_ROOT, 'macros')
        if not path.exists(macro_dir):
            path.mkdir(macro_dir)

        logger.status(f'Opening: {board_file}')
        self.args = args
        self.board_file = board_file
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        self.app = self.mputils.PADSPCBApplication()
        self.app.Visible = True
        self.board = IPowerPCBDoc(self.app.OpenDocument(board_file))
        self.board.unit = strPPcbUnit['Mils']
        self.layers = self.board.Layers
        self.added_pwrsilk = False

        self.brd_size_width = 0.0
        self.brd_size_depth = 0.0
        self.brd_size_height = 0.0

        self.brd_view_size_width = 0.0
        self.brd_view_size_depth = 0.0
        self.brd_view_size_height = 0.0

        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'PADS Layout Version: {self.app.Version}')
        logger.status(f'PCB Name: {self.board.Name}')
        if self.board.Name == 'default.pcb' and not self.board.Name == board_file.name:
            logger.warning("No input file found")
            pass

        self.dic_hwnd_title = {}
        self.hwnd = self.found_this_hwnd()
        if self.hwnd:
            wg.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)
            logger.debug("Set Window MAXIMIZE done.")
            pass
        self.set_view_extents_to_board()
        self.view_top_left_mils, self.view_bot_right_mils = self.get_board_view_size()
        self.app.Visible = visible
        self.brd_view_size_height = self.get_pcb_thick()
        self.get_board_dim_size()

    def found_this_hwnd(self):
        wg.EnumWindows(self.get_all_hwnd, 0)

        pads_instance = None
        title = f"{self.board_file} - PADS Layout"
        # logger.debug(title)
        for _, v in enumerate(self.dic_hwnd_title.items()):
            if v[1] == '':
                continue
            # else:
            #    logger.debug(v[1])
            # v[1].__eq__(title)
            if 'PADS Layout' in v[1] and f"{self.board_file.name}" in v[1]:
                pads_instance = v[0]
                break
        if not pads_instance:
            logger.debug("Not found the hWnd.")
        return pads_instance

    def get_all_hwnd(self, hwnd, mouse):
        # list all window
        if (wg.IsWindow(hwnd)
            and wg.IsWindowEnabled(hwnd)
            ): # and wg.IsWindowVisible(hwnd)
            self.dic_hwnd_title.update({hwnd: wg.GetWindowText(hwnd)})

    def get_pcb_thick(self):

        metal_layers_count = 0
        diele_layers_count = 0
        pcb_thick = 0
        for idx, _layer in enumerate(self.layers):
            layer = IPowerPCBLayer(_layer)
            print(f' -> L{idx+1:02d}: {layer.Name}')
            if layer.type == ppcbLayerRouting or layer.type == ppcbLayerComponent:
                metal_layers_count += 1
                pcb_thick += layer.CopperThickness
            else:
                diele_layers_count += 1
            pcb_thick += layer.GetDielectricThickness(ppcbDielectricLayerAbove)
        print(
            f'Board layers: Total {self.layers.Count}, includes {metal_layers_count} metal, {diele_layers_count} dielectric')
        return (pcb_thick)

    def info(self):
        logger.info(
            f'This PCB file includes Components: {self.board.Components.Count}, Layers: {self.board.ElectricalLayerCount}')
        print('Board Stackup:')
        pcb_thick = self.brd_view_size_height

        _key = list(strPPcbUnit.keys())[
            list(strPPcbUnit.values()).index(self.board.unit)]
        print(
            f'Board Thickness: {pcb_thick:.2f} {_key}, {pcb_thick * 0.0254:.2f} mm')
        print(
            f'Board Origin Point: px={self.board.OriginX}, py={self.board.OriginY}')
        #old_unit = self.board.unit
        #self.board.unit = strPPcbUnit['Metric']
        #self.board.unit = old_unit

        print(
            f"Board View Size(W x D x H): {self.brd_view_size_width * 0.0254: .2f} mm x {self.brd_view_size_depth * 0.0254: .2f} mm x {self.brd_view_size_height * 0.0254: .2f} mm")

        print(
            f"Board Dim  Size(W x D x H): {self.brd_size_width * 0.0254: .2f} mm x {self.brd_size_depth * 0.0254: .2f} mm x {self.brd_size_height * 0.0254: .2f} mm")

        brd_dim_size = self.brd_size_width * 0.0254 * self.brd_size_depth * 0.0254
        brd_cal_size = self.brd_view_size_width * 0.0254 * self.brd_view_size_depth * 0.0254
        brd_real_size = self.board.BoardOutlineSurface * 0.0254 * 0.0254
        compare_str = '>' if brd_real_size > brd_cal_size else '<' if brd_real_size < brd_cal_size else '='
        print(
            f"Board view surface size: {brd_real_size: .2f} mm² {compare_str} calculated view size {brd_cal_size: .2f} mm²")

        print(
            f"Board dim  surface size: {brd_dim_size: .2f} mm²")

        pass

    def set_visible(self, visible):
        self.app.Visible = visible

    def set_plot_directory(self, plot_directory):
        self.plot_directory = plot_directory
        self.plot_options.SetOutputDirectory(plot_directory)

    def get_total_layer_count(self):
        return self.layers.Count

    def get_electrical_layer_count(self):
        return self.board.ElectricalLayerCount

    def set_layer_color_by_id(self, layer_id, colors):
        layer = self.get_layer_by_id(layer_id)
        for idx, item in enumerate(PPcbLayerColorType):
            layer.SetColor(idx, colors[idx])

    def set_layer_color_by_name(self, layer_name, colors):
        _, layer = self.get_layer_by_name(layer_name)
        for idx, item in enumerate(PPcbLayerColorType):
            layer.SetColor(idx, colors[idx])

    def _get_layer_color(self, layer):
        if not layer.type == ppcbLayerRouting and not layer.type == ppcbLayerComponent:
            pass
        color_name = []
        for idx, item in enumerate(PPcbLayerColorType):
            color_seq = layer.GetColor(idx)
            color = PPcbDefaultPaletteColorList.get_value_by_idx(color_seq)
            color_name.append(color.get_color_name())
        print(f"{'Layers':25} {'Trace':10} {'Via':10} {'Pad':10} {'Copper':10} {'Line':10} {'Text':10} {'Error':10}")
        print(
            f"{layer.Name:25} {color_name[0]:10} {color_name[1]:10} {color_name[2]:10} {color_name[3]:10} {color_name[4]:10} {color_name[5]:10} {color_name[6]:10}")

    def get_layer_color_by_id(self, layer_id):
        layer = self.get_layer_by_id(layer_id)
        self._get_layer_color(layer)

    def get_layer_color_by_name(self, layer_name):
        _, layer = self.get_layer_by_name(layer_name)
        self._get_layer_color(layer)

    def get_layer_by_id(self, layer_id):
        for idx, _layer in enumerate(self.layers):
            if idx + 1 == layer_id:
                layer = IPowerPCBLayer(_layer)
                return layer
        return None

    def get_layer_by_name(self, layer_name):
        for idx, _layer in enumerate(self.layers):
            if _layer.Name == layer_name:
                layer = IPowerPCBLayer(_layer)
                return (idx + 1, layer)
        return (None, None)

    def get_layer_name(self, layer_id):
        return self.get_layer_by_id(layer_id).Name

    def get_layer_id(self, layer_name):
        index, _ = self.get_layer_by_name(layer_name)
        return index

    def export_ascii(self, file):
        sections = -1 if ppcbASCIISectionAll > 0xffff else ppcbASCIISectionAll
        ver = ppcbASCIIVerCurrent
        expandAttrs = -1 if ppcbAttrAll > 0xffff else ppcbAttrAll
        self.board.ExportASCII(file, sections, ver, expandAttrs)

    def export_hyp(self, file):
        self.run_pour_manager()
        self.run_export_hyp(file)

    def run_export_hyp(self, file=None):
        hyp_file = file
        if hyp_file is None:
            hyp_file = path(self.app.FullName).with_suffix('.hyp')

        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbExportHypMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_4)
        d = {
            "hyp_file": hyp_file,
            "missing_height": 25,
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def run_pour_manager(self):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbPourMangerMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_3)
        d = {
            "flood_mode": 'Flood',
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def set_view_extents_to_board(self) -> IPowerPCBView:
        view = IPowerPCBView(self.board.ActiveView)
        view.SetExtentsToBoard()
        return view

    def get_board_view_size(self) -> Tuple[tuple, tuple]:
        view = self.set_view_extents_to_board()
        top_left = (view.TopLeftX, view.TopLeftY)
        bot_right = (view.BottomRightX, view.BottomRightY)

        self.brd_view_size_width = view.BottomRightX - view.TopLeftX
        self.brd_view_size_depth = view.TopLeftY - view.BottomRightY

        return (top_left, bot_right)

    def get_board_dim_size(self, remove_board_outside_keepouts=True):
        keepout_type_start = False
        type_count = 0
        keepout_type_count = 0
        drawing_dim = []

        logger.debug(f"Found Drawings: {len(self.board.Drawings)}")
        for _drawing in self.board.Drawings:
            type_count += 1
            drawing = IPowerPCBDrawing(_drawing)
            if drawing.DrawingType == ppcbDrwKeepout:
                keepout_type_count += 1
                keepout_type_start = True
                if_del = False
                if drawing.PositionX < self.view_top_left_mils[0] or drawing.PositionX > self.view_bot_right_mils[0]:
                    if_del = True
                elif drawing.PositionY < self.view_bot_right_mils[1] or drawing.PositionY > self.view_top_left_mils[1]:
                    if_del = True
                if if_del:
                    drawing.selected = if_del
                logger.debug(
                    f"Found Keepout {keepout_type_count} in {type_count}: {drawing.Name} selected = {if_del}")
            else:
                if drawing.DrawingType == ppcbDrwBoard:
                    logger.debug(f"Found BoardOutline in {type_count}: {drawing.Name}")
                elif drawing.DrawingType == ppcbDrw2Dline:
                    if drawing.Name.startswith('DIM'):
                        texts = drawing.Texts
                        text = texts[0].text
                        drawing_dim.append(text)
                    logger.debug(f"Found 2DLine in {type_count}: {drawing.Name}: {drawing.PositionX}, {drawing.PositionY}")
                if type_count > 100:
                    # save time
                    break
            pass
        logger.debug(f"This PCB file includes 2DLine for DIM: {drawing_dim}")
        def drawing_dim_sorted(a, b):
            a = self.get_size_in_mil(a)
            b = self.get_size_in_mil(b)
            if a > b:
                return -1
            else:
                return 1
        drawing_dim = sorted(drawing_dim, key=functools.cmp_to_key(drawing_dim_sorted))
        if len(drawing_dim) > 2:
            if self.brd_view_size_width > self.brd_view_size_depth:
                self.brd_size_width  = self.get_size_in_mil(drawing_dim[0])
                self.brd_size_depth  = self.get_size_in_mil(drawing_dim[1])
                self.brd_size_height = self.get_size_in_mil(drawing_dim[len(drawing_dim)-1])
            else:
                self.brd_size_width  = self.get_size_in_mil(drawing_dim[1])
                self.brd_size_depth  = self.get_size_in_mil(drawing_dim[0])
                self.brd_size_height = self.get_size_in_mil(drawing_dim[len(drawing_dim)-1])
        # delete selected obj
        if remove_board_outside_keepouts:
            self.run_macro_ppcb_delete_selected()

    def get_size_in_mil(self, size):
        pattern = re.compile(r'([\d.]+)([a-zA-Z])')
        matched = pattern.match(size)
        _size = 0
        if matched:
            _size = float(matched.group(1))
            _unit = matched.group(2)
            if _unit in 'mm':
                _size = _size / 0.0254
            elif _unit in 'inch':
                _size = _size / 25.4
        return _size

    def run_macro(self, macro_file):
        dirname = PADSPROD_ROOT
        file = path.joinpath(dirname, 'macros', macro_file)
        self.app.RunMacro(file, 'Macro1')

    def run_macro_ppcb_delete_selected(self):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbDeleteSelected']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_6)
        d = {}
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def run_macro_ppcb_reset_default_palette(self):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbResetDefaultPaletteMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_1)
        d = {}
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def _config_macro_ppcb_export_pdf(self, pdf, layer_number):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbExportPdfMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        silk_layer_number = ''
        assembly_layer_number = ''
        layer_name = self.get_layer_name(layer_number)
        if layer_name == 'Top':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-top-silk.pdf')
            pdc_name = PPCB_EXPORT_PDF_TOP_SILK_PDC
            silk_layer_number = self.get_layer_id('Silkscreen Top')
            assembly_layer_number = self.get_layer_id('Assembly Drawing Top')
        elif layer_name == 'Bottom':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-bot-silk.pdf')
            pdc_name = PPCB_EXPORT_PDF_BOT_SILK_PDC
            silk_layer_number = self.get_layer_id('Silkscreen Bottom')
            assembly_layer_number = self.get_layer_id(
                'Assembly Drawing Bottom')
        elif layer_name == 'Drill Drawing':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-drill-drawing.pdf')
            pdc_name = PPCB_EXPORT_PDF_DRAWING_PDC
        else:
            pdf = path.joinpath(pdf.parent, pdf.stem +
                                f'-L{layer_number:02}.pdf')
            pdc_name = PPCB_EXPORT_PDF_MID_LAYER_PDC

        # if layer_name.isnumeric():
        #    layer_number = int(layer_name)
        # else:
        #    layer_number = self.get_layer_id(layer_name)

        t = Template(MACRO_OPS_2)
        d = {
            "pdc_file": path.joinpath(dirname, 'macros', pdc_name + '.pdc'),
            "pdf_file": pdf,
            "enable_open_pdf": 'false',
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        pdc_file = path.joinpath(dirname, 'macros', pdc_name + '.pdc')
        pdc_tpl = path.joinpath(dirname, 'config', pdc_name + '.tpl')
        t = Template(path.read_text(pdc_tpl))
        d = {
            "layer": layer_number,
            "silk_layer": silk_layer_number,
            "assembly_layer": assembly_layer_number,
        }
        pdc_content = t.substitute(d)
        path.write_text(pdc_file, pdc_content)
        return macro_file

    def run_macro_ppcb_export_pdf(self, pdf, layer_number):
        layer_name = self.get_layer_name(layer_number)
        color_idxs = []
        for _, item in enumerate(PPcbLayerColorType):
            color_idx = PPcbDefaultPaletteColorList.get_idx('silver')
            if item == PPcbLayerColorType.ppcbLayerColorPad:
                color_idx = PPcbDefaultPaletteColorList.get_idx('silver')
            elif item == PPcbLayerColorType.ppcbLayerColorRefDes:
                color_idx = PPcbDefaultPaletteColorList.get_idx('white')
            elif item == PPcbLayerColorType.ppcbLayerColorText:
                if not self.args.disable_pwrsilk:
                    color_idx = PPcbDefaultPaletteColorList.get_idx('red')
            color_idxs.append(color_idx)

        logger.status(f'Export to pdf from {layer_name} layer.')
        self.set_layer_color_by_id(layer_number, color_idxs)

        if not self.args.disable_pwrsilk and not self.added_pwrsilk:
            # self.set_layer_color_by_id(layer_number, color_idxs)
            #layer = self.get_layer_by_name('Top')
            #layer.SetColor(PPcbLayerColorType.ppcbLayerColorText, PPcbDefaultPaletteColorList.get_idx('white'))
            self.add_silk_to_power_nets()
            self.added_pwrsilk = True
        # No affect
        # if layer_name == 'Top' and not self.args.disable_pwrsilk:
        #    self.board.ActiveLayer = self.get_layer_id('Silkscreen Top')
        # if layer_name == 'Bottom' and not self.args.disable_pwrsilk:
        #    self.board.ActiveLayer = self.get_layer_id('Silkscreen Bottom')

        macro_file = self._config_macro_ppcb_export_pdf(pdf, layer_number)
        self.run_macro(macro_file)

    def run_macro_ppcb_export_default_pdf(self, pdf):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbExportPdfMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        pdf = path.joinpath(pdf.parent, pdf.stem + '-pcb.pdf')
        # if layer_name.isnumeric():
        #    layer_number = int(layer_name)
        # else:
        #    layer_number = self.get_layer_id(layer_name)

        t = Template(MACRO_OPS_2_1)
        d = {
            "pdf_file": pdf,
            "enable_open_pdf": 'false',
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)
        self.run_macro(macro_file)
        logger.status(f'Export to pdf in default configuration.')

    def close(self, save=True):
        if save:
            self.board.SaveAsTemp(
                path(self.app.DefaultFilePath) / 'default.pcb')
        self.app.Quit()

    def get_power_nets(self) -> Tuple[Dict, List]:
        components_power_nets = {}
        #    'n/a': {'top': {
        #        'ttl': [],
        #        'res': [],
        #        'cap': [],
        #        'ind': [],
        #    }, 'bottom': {
        #        'ttl': [],
        #        'res': [],
        #        'cap': [],
        #        'ind': [],
        #    }, }

        _fields = path(self.board_file).stem.split('-')
        _file2 = '-'.join(_fields[:2]) if len(_fields) > 2 else None
        metadata_file_lookup = [
            path(self.board_file).with_suffix('.metadata.toml'),
            path(self.board_file).parent / f'{_file2}-metadata.toml',
            path(self.board_file).parent / 'metadata.toml',
        ]
        data = power_nets = key_comps = None
        for metadata_file in metadata_file_lookup:
            try:
                data = toml.load(metadata_file)
                power_nets = data.get('power_nets')
                key_comps = data.get('key_comps')
                logger.info(f"Try lookup {metadata_file} succeeded.")
                break
            except Exception as e:
                logger.debug(f"Try lookup {metadata_file} failed: {e.args[1]}")
                continue
        if not data or not power_nets:
            #raise PadsprodException(f"Metadata file corrupted raised at {path(__file__).name} line {sys._getframe().f_lineno}")
            return ({}, [])
        logger.debug(power_nets)

        for net in power_nets:
            net_humanize = net[0]
            if len(net) > 1:
                net_name = net[1]
            else:
                net_name = net[0]

            for _pcb_net in self.board.Nets:
                _pcb_net = IPowerPCBNet(_pcb_net)
                if net_name == _pcb_net.Name:
                    components_power_nets[net_humanize] = {}
                    power_net_components = {}
                    _pins = _pcb_net.Pins
                    for _pin in _pins:
                        _pin = IPowerPCBPin(_pin)
                        comp = IPowerPCBComp(_pin.Component)
                        # print(comp.PartTypeLogic)
                        if comp.LayerName in 'Top' or comp.LayerName in 'Bottom':
                            if not comp.LayerName.lower() in power_net_components:
                                power_net_components[comp.LayerName.lower()] = {
                                }
                            if not comp.PartTypeLogic.lower() in power_net_components[comp.LayerName.lower()]:
                                power_net_components[comp.LayerName.lower(
                                )][comp.PartTypeLogic.lower()] = []
                            power_net_components[comp.LayerName.lower(
                            )][comp.PartTypeLogic.lower()].append(comp)

                    type_alias_name = {'ttl': 'ICs', 'res': 'resistors',
                                       'cap': 'capacitors', 'ind': 'inductances', 'con': 'connectors'}
                    for layer in ['top', 'bottom']:
                        debug_string = f"Net({net_humanize:16}) in {layer[:3]} includes "
                        if not layer in power_net_components:
                            power_net_components[layer] = {}
                        for type in ['ttl', 'res', 'cap', 'ind', 'con']:
                            if not type in power_net_components[layer]:
                                power_net_components[layer][type] = []
                            debug_string += f"{len(power_net_components[layer][type]):3} {type_alias_name[type]},"
                        logger.debug(debug_string.rstrip(','))

                    def lucky_comp_sorted(a, b):
                        a = IPowerPCBComp(a)
                        b = IPowerPCBComp(b)

                        pattern = re.compile(r'[A-Za-z]+(\d+)')
                        matched = pattern.match(a.Decal)
                        # print(matched.groups())
                        a_fp = matched.group(1) if matched else 0
                        matched = pattern.match(b.Decal)
                        b_fp = matched.group(1) if matched else 0

                        if int(a_fp) < int(b_fp):
                            return 1  # b, a
                        else:
                            return -1

                    for layer in ['top', 'bottom']:
                        if False and len(power_net_components[layer]['con']) > 0:
                            cons = power_net_components[layer]['con'].copy()
                            _sorted_cons = sorted(
                                cons, key=functools.cmp_to_key(lucky_comp_sorted))
                            power_net_components[layer]['con'] = _sorted_cons
                            power_net_components[layer]['lucky'] = _sorted_cons[0]
                            pass
                        elif len(power_net_components[layer]['cap']) > 0:
                            caps = power_net_components[layer]['cap'].copy()
                            _sorted_caps = sorted(
                                caps, key=functools.cmp_to_key(lucky_comp_sorted))
                            power_net_components[layer]['cap'] = _sorted_caps
                            power_net_components[layer]['lucky'] = _sorted_caps[0]
                            pass
                        elif len(power_net_components[layer]['ind']) > 0:
                            inds = power_net_components[layer]['ind']
                            _sorted_inds = sorted(
                                inds, key=functools.cmp_to_key(lucky_comp_sorted))
                            power_net_components[layer]['ind'] = _sorted_inds
                            power_net_components[layer]['lucky'] = _sorted_inds[0]
                            pass
                        elif len(power_net_components[layer]['res']) > 0:
                            ress = power_net_components[layer]['res']
                            _sorted_ress = sorted(
                                ress, key=functools.cmp_to_key(lucky_comp_sorted))
                            power_net_components[layer]['res'] = _sorted_ress
                            power_net_components[layer]['lucky'] = _sorted_ress[0]
                            pass
                        else:
                            power_net_components[layer]['lucky'] = None
                        if power_net_components[layer]['lucky']:
                            logger.debug(
                                f"{layer} = {IPowerPCBComp(power_net_components[layer]['lucky']).Name}")
                    components_power_nets[net_humanize] = power_net_components
        return components_power_nets, key_comps

    def guess_power_nets(self, net_name):
        re_power_ex1 = r'([+-]*\d+[\.\d]*)V$'
        re_power_ex2 = r'([+-]*\d+)V(\d+)$'
        re_power_ex3 = r'VCC(\d+[\.+\d+])V'
        re_power_ex4 = r'[PN]*VCC(\d+)V([\d+])'
        re_power_ex5 = r'V(\d+[\.+\d+])[V]*'
        re_power_ex6 = r'[PN]*V(\d+)[V]*'
        vcc = None

        pattern = re.compile(re_power_ex1)
        matched = pattern.match(net_name)
        if matched:
            vcc = matched.group(1)
        else:
            #print(f'try re_power_ex2')
            pattern = re.compile(re_power_ex2)
            matched = pattern.match(net_name)
            if matched:
                vcc = f"{matched.group(1)}.{matched.group(2)}"
        if not matched:
            #print(f'try re_power_ex3')
            pattern = re.compile(re_power_ex3)
            matched = pattern.match(net_name)
            if matched:
                vcc = f"{matched.group(1)}.{matched.group(2)}"
        if not matched:
            #print(f'try re_power_ex4')
            pattern = re.compile(re_power_ex4)
            matched = pattern.match(net_name)
            if matched:
                vcc = f"{matched.group(1)}.{matched.group(2)}"
        if not matched:
            #print(f'try re_power_ex5')
            pattern = re.compile(re_power_ex5)
            matched = pattern.match(net_name)
            if matched:
                vcc = f"{matched.group(1)}.{matched.group(2)}"
        if not matched:
            #print(f'try re_power_ex6')
            pattern = re.compile(re_power_ex6)
            matched = pattern.match(net_name)
            if matched:
                vcc = matched.group(1)
        if not matched:
            #print('Not found.')
            vcc = None

        #_fields = matched.groupdict()
        return vcc

    def add_silk_to_power_nets(self):
        top_silks = []
        bot_silks = []
        nets, key_comps = self.get_power_nets()
        if nets:
            for idx, net in enumerate(nets):
                for layer in ['Top', 'Bottom']:
                    if nets[net][layer.lower()]['lucky']:
                        lucky_comp = IPowerPCBComp(
                            nets[net][layer.lower()]['lucky'])
                        text = str(idx + 1)
                        text_px = lucky_comp.CenterX
                        text_py = lucky_comp.CenterY
                        text_height = 160
                        line_width = 16
                        layer_name = 'Top' if layer == 'Top' else 'Bottom'
                        mirrored = False if layer == 'Top' else True
                        config = TextConfig(
                            text, text_px, text_py, text_height, line_width, layer_name, mirrored)
                        self.run_add_text(config)
                        silks_info = f"{lucky_comp.LayerName:16}, {text:2}, {lucky_comp.Name}"
                        if layer == 'Top':
                            top_silks.append(silks_info)
                        else:
                            bot_silks.append(silks_info)
                    else:
                        logger.info(
                            f"Not found {net} related components in {layer}")
            logger.info(f"Added silk to power nets done.")
        if key_comps:
            for idx, key_comp in enumerate(key_comps):
                lucky_comp = None
                key_comp_ref = key_comp[0]
                for _comp in self.board.Components:
                    if _comp.Name == key_comp_ref:
                        lucky_comp = IPowerPCBComp(_comp)
                        break
                if lucky_comp:
                    layer = self.get_layer_name(lucky_comp.layer)
                    text = str(len(nets) + idx + 1)
                    text_px = lucky_comp.CenterX
                    text_py = lucky_comp.CenterY
                    text_height = 160
                    line_width = 16
                    layer_name = 'Top' if layer == 'Top' else 'Bottom'
                    mirrored = False if layer == 'Top' else True
                    config = TextConfig(
                        text, text_px, text_py, text_height, line_width, layer_name, mirrored)
                    self.run_add_text(config)
                    silks_info = f"{lucky_comp.LayerName:16}, {text:2} -> {lucky_comp.Name}"
                    if layer == 'Top':
                        top_silks.append(silks_info)
                    else:
                        bot_silks.append(silks_info)
        logger.info(f"Added silk to key components done.")
        silks_file = path(self.board_file).with_suffix('.silks.txt')
        silks_file.write_text('\n'.join(top_silks) +
                              '\n\n' + '\n'.join(bot_silks))

    def run_add_text(self, config: TextConfig):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbDraftingText']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_5)
        d = {
            "text": config.text,
            "text_px": config.text_px,
            "text_py": config.text_py,
            "text_height": config.text_height,
            "line_width": config.line_width,
            "layer": config.layer_name,
            "mirrored": 'true' if config.mirrored else 'false',
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)
