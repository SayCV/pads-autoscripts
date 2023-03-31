
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
        if self.app.OpenFile(board_file):
            self.app.Visible = visible
        else:
            logger.error(f"Unable to open specified file: {board_file}")
            self.app.Exit()
            return
        self.design = IHLDesign(self.app.Design)
        self.boards = IHLCollection(self.design.Boards)
        self.nets = IHLCollection(self.design.Nets)
        self.multi_parts = []
        self.components_class = {}

        self.app.StatusBarText = 'Running in python: ' + \
            str(datetime.datetime.now())
        logger.status(f"{self.app.StatusBarText}")
        logger.status(f'HyperLynx Version: {None}')
        logger.status(f'HYP Name: {self.app.FileName}')
        if self.app.FileName == 'default.hyp' and not self.app.FileName == board_file.name:
            logger.warning("No input file found")
            pass

    def info(self):
        logger.info(f'This HYP file includes Components: {self.design.Components.Count}, Nets: {self.design.Nets.Count}')

    def set_visible(self, visible):
        self.app.Visible = visible
