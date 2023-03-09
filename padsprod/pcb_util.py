
import datetime
import logging
import os
import subprocess
import enum
from pathlib import Path as path
from string import Template

from mputils import *
from .pcb_constants import *
from .color_constants import colors

logger = logging.getLogger(__name__)

strPPcbUnit = ['Current', 'Database', 'Mils', 'Inch', 'Metric']

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

mcrPpcbCmdList = {
    "PpcbResetDefaultPaletteMacro" : "Macro1.mcr",
    "PpcbExportPdfMacro" : "Macro2.mcr",
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
    def __init__(self, board_file):
        self.name = os.path.splitext(os.path.basename(board_file))[0]
        self.mputils = mputils()
        self.app = self.mputils.PADSPCBApplication()
        self.app.Visible = True
        self.board = IPowerPCBDoc(self.app.OpenDocument(board_file))
        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        self.layers = self.board.Layers
        self.info()

    def info(self):
        logger.debug(f'PADS Layout Version: {self.app.Version}')
        logger.debug(f'PCB Name: {self.board.Name}')
        logger.debug(f'PCB Layers: {self.board.ElectricalLayerCount}')

        metal_layers_count = 0
        diele_layers_count = 0
        pcb_thick = 0
        for _layer in self.layers:
            layer = IPowerPCBLayer(_layer)
            logger.debug(f'Layer Name: {layer.Name}')
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
            pcb_thick * 1, strPPcbUnit[self.board.unit]))

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

    def export_pdf(self, layer_name):
        self.set_layer_color()

    def run_macro(self, macro_file):
        dirname = path(__file__).resolve().parent
        file = path.joinpath(dirname, 'macros', macro_file)
        self.app.RunMacro(file, 'Macro1')

    def run_macro_ppcb_reset_default_palette(self):
        dirname = path(__file__).resolve().parent
        origin = mcrPpcbCmdList['PpcbResetDefaultPaletteMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        t = Template(MACRO_OPS_1)
        d = { }
        macro_content = t.substitute(d)
        path.write_text(macro_file, macro_content)

        self.run_macro(macro_file)

    def _config_macro_ppcb_export_pdf(self, pdf, layer_name):
        dirname = path(__file__).resolve().parent
        origin = mcrPpcbCmdList['PpcbExportPdfMacro']
        macro_file = path.joinpath(dirname, 'macros', origin)

        if layer_name == 'Top':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-top-silk.pdf')
            pdc_name = PPCB_EXPORT_PDF_TOP_SILK_PDC
        elif layer_name == 'Bottom':
            pdf = path.joinpath(pdf.parent, pdf.stem + '-bot-silk.pdf')
            pdc_name = PPCB_EXPORT_PDF_BOT_SILK_PDC
 
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
            "layer": self.get_layer_id(layer_name),
        }
        pdc_content = t.substitute(d)
        path.write_text(pdc_file, pdc_content)
        return macro_file

    def run_macro_ppcb_export_pdf(self, pdf):
        color_idxs = []
        for _, item in enumerate(PPcbLayerColorType):
            color_idx = PPcbDefaultPaletteColorList.get_idx('silver')
            if item == PPcbLayerColorType.ppcbLayerColorRefDes:
                color_idx = PPcbDefaultPaletteColorList.get_idx('white')
            color_idxs.append(color_idx)

        self.set_layer_color_by_name('Top', color_idxs)
        macro_file = self._config_macro_ppcb_export_pdf(pdf, 'Top')
        self.run_macro(macro_file)

        self.set_layer_color_by_name('Bottom', color_idxs)
        macro_file = self._config_macro_ppcb_export_pdf(pdf, 'Bottom')
        self.run_macro(macro_file)

    def close(self):
        self.app.Quit()
