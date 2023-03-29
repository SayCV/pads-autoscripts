
import datetime
import logging
import os
import subprocess
import enum
from pathlib import Path as path
from string import Template

from mputils import *
from padsprod.helpers import PADSPROD_ROOT
from .pcb_constants import *
from .color_constants import colors

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
    ID0 = colors['black'];            ID1 = colors['navy'];        ID2 = colors['green'];           ID3 = colors['teal'];
    ID4 = colors['maroon'];           ID5 = colors['purple'];      ID6 = colors['olive'];           ID7 = colors['gray'];
    ID8 = colors['silver'];           ID9 = colors['blue'];        ID10 = colors['green1'];         ID11 = colors['aqua'];
    ID12 = colors['red'];             ID13 = colors['magenta'];    ID14 = colors['yellow'];         ID15 = colors['white'];
    ID16 = colors['yellow5'];         ID17 = colors['teal1'];      ID18 = colors['springgreen4'];   ID19 = colors['deepskyblue'];
    ID20 = colors['cadmiumorange1'];  ID21 = colors['warmgrey1'];  ID22 = colors['rawsienna1'];     ID23 = colors['deeppink2'];
    ID24 = colors['lightgoldenrod4']; ID25 = colors['teal2'];      ID26 = colors['forestgreen1'];   ID27 = colors['darkslategray1'];
    ID28 = colors['indianred1'];      ID29 = colors['silver1'];    ID30 = colors['cadmiumyellow1']; ID31 = colors['maroon1']

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
    "PPcbResetDefaultPaletteMacro" : "Macro1.mcr",
    "PPcbExportPdfMacro" : "Macro2.mcr",
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


class PCB(object):
    def __init__(self, args, board_file, visible):
        macro_dir = path.joinpath(PADSPROD_ROOT, 'macros')
        if not path.exists(macro_dir):
            path.mkdir(macro_dir)
        
        logger.status(f'Opening: {board_file}')
        self.args = args
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        self.app = self.mputils.PADSPCBApplication()
        self.app.Visible = visible
        self.board = IPowerPCBDoc(self.app.OpenDocument(board_file))
        self.layers = self.board.Layers
        
        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'PADS Layout Version: {self.app.Version}')
        logger.status(f'PCB Name: {self.board.Name}')
        if self.board.Name == 'default.pcb' and not self.board.Name == board_file.name:
            logger.warning("No input file found")
            pass

    def info(self):
        logger.info(f'This PCB file includes Components: {self.board.Components.Count}, Layers: {self.board.ElectricalLayerCount}')
        print('Board Stackup:')

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
        _key = list(strPPcbUnit.keys())[list(strPPcbUnit.values()).index(self.board.unit)]
        print(f'Board Thickness: {pcb_thick:.2f} {_key}')
        print(f'Board Origin Point: px={self.board.OriginX}, py={self.board.OriginY}')
        old_unit = self.board.unit
        self.board.unit = strPPcbUnit['Metric']
        dBoardSize = self.board.BoardOutlineSurface
        print(f"Board Size: {dBoardSize: .2f} mm²")
        self.board.unit = old_unit

    def set_visible(self, visible):
        self.app.Visible = visible

    def set_plot_directory(self, plot_directory):
        self.plot_directory = plot_directory
        self.plot_options.SetOutputDirectory(plot_directory)

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
        print(f"{layer.Name:25} {color_name[0]:10} {color_name[1]:10} {color_name[2]:10} {color_name[3]:10} {color_name[4]:10} {color_name[5]:10} {color_name[6]:10}")

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

    def run_macro(self, macro_file):
        dirname = PADSPROD_ROOT
        file = path.joinpath(dirname, 'macros', macro_file)
        self.app.RunMacro(file, 'Macro1')

    def run_macro_ppcb_reset_default_palette(self):
        dirname = PADSPROD_ROOT
        origin = mcrPPcbCmdList['PPcbResetDefaultPaletteMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_1)
        d = { }
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
            assembly_layer_number = self.get_layer_id('Assembly Drawing Bottom')
        elif layer_name == 'Drill Drawing':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-drill-drawing.pdf')
            pdc_name = PPCB_EXPORT_PDF_DRAWING_PDC
        else:
            pdf = path.joinpath(pdf.parent, pdf.stem + f'-mid{layer_number}.pdf')
            pdc_name = PPCB_EXPORT_PDF_MID_LAYER_PDC
        
        #if layer_name.isnumeric():
        #    layer_number = int(layer_name)
        #else:
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
            color_idxs.append(color_idx)

        logger.status(f'Export to pdf from {layer_name} layer.')
        self.set_layer_color_by_id(layer_number, color_idxs)
        macro_file = self._config_macro_ppcb_export_pdf(pdf, layer_number)
        self.run_macro(macro_file)

    def close(self, save=True):
        if save:
            self.board.SaveTemp()
        self.app.Quit()
