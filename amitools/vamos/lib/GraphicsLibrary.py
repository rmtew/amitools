import sys

from amitools.vamos.AmigaLibrary import AmigaLibrary
from lexec.ExecStruct import LibraryDef
from amitools.vamos.AccessStruct import AccessStruct

from amitools.vamos.CPU import *
from intuition.IntuitionStruct import *

class GraphicsLibrary(AmigaLibrary):
  name = "graphics.library"

  def __init__(self, version=39, profile=False):
    AmigaLibrary.__init__(self, self.name, version, LibraryDef, profile)
