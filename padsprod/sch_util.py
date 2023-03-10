
import datetime
import logging
import os
import subprocess
import enum
from pathlib import Path as path
from string import Template

from mputils import *
from padsprod.helpers import PADSPROD_ROOT
from .sch_constants import *
from .color_constants import colors

logger = logging.getLogger(__name__)

strPLogUnit = ['Current', 'Database', 'Mils', 'Inch', 'Metric', 'DrawArea']

objSchItem = [
    'Background', 'Selection', 'Connection', 'Bus',      'Line',        'Part',     'HierarchicalComp', 'Text', 
    'TextBox',    'RefDes',    'RefDesBox',  'PartType', 'PartTypeBox', 'PartText', 'PartTextBox',      'PinNumber', 
    'PinNumberBox', 'NetName', 'NetNameBox', 'Field', 'FieldBox'
]

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
    "PLogResetDefaultPaletteMacro" : "Macro1.mcr",
    "PLogExportPdfMacro" : "Macro2.mcr",
}


class SCH(object):
    def __init__(self, board_file, visible):
        macro_dir = path.joinpath(PADSPROD_ROOT, 'macros')
        if not path.exists(macro_dir):
            path.mkdir(macro_dir)
        
        logger.status(f'Opening: {board_file}')
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        self.app = self.mputils.PADSSCHApplication()
        self.app.Visible = visible
        self.board = IPowerLogicDoc(self.app.OpenDocument(board_file))
        self.sheets = self.board.Sheets
        
        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'PADS Logic Version: {self.app.Version}')
        logger.status(f'SCH Name: {self.board.Name}')
        if self.board.Name == 'default.sch' and not self.board.Name == board_file.name:
            logger.warning("No input file found")
            pass

    def info(self):
        logger.info(f'SCH Sheets: {self.board.Sheets.Count}')

        metal_layers_count = 0
        diele_layers_count = 0
        pcb_thick = 0
        for _layer in self.layers:
            layer = IPowerPCBLayer(_layer)
            logger.info(f'Layer Name: {layer.Name}')
            if layer.type == ppcbLayerRouting or layer.type == ppcbLayerComponent:
                metal_layers_count += 1
                pcb_thick += layer.CopperThickness
            else:
                diele_layers_count += 1
            pcb_thick += layer.GetDielectricThickness(ppcbDielectricLayerAbove)
        print('Stackup:')
        print(
            f'Number of layers = {self.layers.Count}, including {metal_layers_count} metal, {diele_layers_count} dielectric')
        print('Thickness = {0:.2f}{1}'.format(
            pcb_thick * 1, strPLogUnit[self.board.unit]))

    def set_visible(self, visible):
        self.app.Visible = visible

    def set_plot_directory(self, plot_directory):
        self.plot_directory = plot_directory
        self.plot_options.SetOutputDirectory(plot_directory)

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
        ver = plogASCIIVerCurrent
        self.board.ExportASCII(file, ver)

    def run_macro(self, macro_file):
        dirname = PADSPROD_ROOT
        file = path.joinpath(dirname, 'macros', macro_file)
        self.app.RunMacro(file, 'Macro1')

    def run_macro_ppcb_reset_default_palette(self):
        dirname = PADSPROD_ROOT
        origin = mcrPLogCmdList['PLogResetDefaultPaletteMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_1)
        d = { }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def _config_macro_plog_export_pdf(self, pdf, page):
        dirname = PADSPROD_ROOT
        origin = mcrPLogCmdList['PLogExportPdfMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        if page == 0:
            pdf = path.joinpath(pdf.parent, pdf.stem + '-sch.pdf')
        else:
            pdf = path.joinpath(pdf.parent, pdf.stem + f'-sch{page}.pdf')

        t = Template(MACRO_OPS_2)
        d = {
            "pdf_file": pdf,
            "enable_open_pdf": 'false',
            "enable_hyperlinks_attr": 'false',
            "enable_hyperlinks_nets": 'false',
            "color_scheme_setting": PLogPdfColorSchemeSetting.plogPdfBlackOnWhiteBackground,
        }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        return macro_file

    def run_macro_ppcb_export_pdf(self, pdf, page):
        color_idxs = []
        for _, item in enumerate(PLogObjColorType):
            color_idx = PLogDefaultPaletteColorList.get_idx('silver')
            #if item == PLogObjColorType.ppcbLayerColorPad:
            #    color_idx = PLogDefaultPaletteColorList.get_idx('silver')
            #elif item == PLogObjColorType.ppcbLayerColorRefDes:
            #    color_idx = PLogDefaultPaletteColorList.get_idx('white')
            color_idxs.append(color_idx)

        logger.status(f'Export to pdf from {page} sheet.')
        #self.set_obj_color_by_name(page, color_idxs)
        macro_file = self._config_macro_ppcb_export_pdf(pdf, page)
        self.run_macro(macro_file)

    def close(self, save=True):
        if save:
            self.board.SaveAsTemp('default.sch')
        self.app.Quit()
