
import datetime
import logging
import os
import subprocess

from mputils import *
from .color_constants import colors

logger = logging.getLogger(__name__)

strPPcbUnit = ['Current', 'Database', 'Mils', 'Inch', 'Metric']

layerPcbItem = [
    'Trace',      'Via',           'Pad',    'Copper',   'Line',      'Text',    'Error',
    'OutlineTop', 'OutlineBottom', 'RefDes', 'PartType', 'Attribute', 'Keepout', 'PinNumber'
]

pcbPresetColorList = [
    colors['black'],           colors['navy'],    colors['green'],          colors['teal'],
    colors['maroon'],          colors['purple'],  colors['olive'],          colors['gray'],
    colors['silver'],          colors['blue'],    colors['green'],          colors['aqua'],
    colors['red'],             colors['magenta'], colors['yellow'],         colors['white'],
    colors['yellow5'],         colors['teal1'],   colors['springgreen4'],   colors['deepskyblue'],
    colors['cadmiumorange1'],  colors['silver'],  colors['rawsienna1'],     colors['deeppink2'],
    colors['lightgoldenrod4'], colors['teal2'],   colors['forestgreen1'],   colors['darkslategray1'],
    colors['indianred1'],      colors['silver1'], colors['cadmiumyellow1'], colors['maroon1']
]


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

    def set_layer_color(self, layer_id):
        logger.debug(self.board.FullName)

    def _get_layer_color(self, layer):
        if not layer.type == ppcbLayerRouting and not layer.type == ppcbLayerComponent:
            pass
        color_name = []
        for idx, item in enumerate(layerPcbItem):
            color_seq = layer.GetColor(idx)
            color = pcbPresetColorList[color_seq]
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

    def close(self):
        self.app.Quit()
