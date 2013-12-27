import sys, Tkinter

from amitools.vamos.AmigaLibrary import AmigaLibrary
from lexec.ExecStruct import LibraryDef
from amitools.vamos.AccessStruct import AccessStruct

from amitools.vamos.CPU import *
from intuition.IntuitionStruct import *


class AutoRequestDialog(Tkinter.Frame):
  def __init__(self, master=None):
    Tkinter.Frame.__init__(self, master)
    
  def setup_widgets(self, body_text=None, pos_text=None, neg_text=None):
    self.body_frame = Tkinter.Frame(self)
    self.body_label = Tkinter.Label(self, text=body_text)
    self.body_label.grid()
    self.body_frame.grid(row=1, column=1, columnspan=2)
    if pos_text is not None:
      self.pos_button = Tkinter.Button(self, text=pos_text, command=self.quit)
      self.pos_button.grid(row=2, column=1)
    if neg_text is not None:
      self.neg_button = Tkinter.Button(self, text=neg_text, command=self.quit)
      self.neg_button.grid(row=2, column=2)
    self.grid()

    
class IntuitionLibrary(AmigaLibrary):
  name = "intuition.library"

  def __init__(self, version=39, profile=False):
    AmigaLibrary.__init__(self, self.name, version, LibraryDef, profile)

  def AutoRequest(self, lib, ctx):
    window_ptr = ctx.cpu.r_reg(REG_A0)
    body_ptr = ctx.cpu.r_reg(REG_A1)
    body = AccessStruct(ctx.mem,IntuiTextDef,struct_addr=body_ptr) if body_ptr else None
    v = body
    str_ptr = body.r_s("it_IText")
    body_text = ctx.mem.access.r_cstr(str_ptr)

    ptext_ptr = ctx.cpu.r_reg(REG_A2)
    ptext = AccessStruct(ctx.mem,IntuiTextDef,struct_addr=ptext_ptr) if ptext_ptr else None
    ptext_text = ctx.mem.access.r_cstr(ptext.r_s("it_IText")) if ptext is not None else None

    ntext_ptr = ctx.cpu.r_reg(REG_A3)
    ntext = AccessStruct(ctx.mem,IntuiTextDef,struct_addr=ntext_ptr) if ntext_ptr else None
    ntext_text = ctx.mem.access.r_cstr(ntext.r_s("it_IText")) if ntext is not None else None

    pflag = ctx.cpu.r_reg(REG_D0)
    nflag = ctx.cpu.r_reg(REG_D1)
    w = ctx.cpu.r_reg(REG_D2)
    h = ctx.cpu.r_reg(REG_D3)
    dialog = AutoRequestDialog()
    dialog.setup_widgets(body_text, ptext_text, ntext_text)
    dialog.master.title("System Request")
    dialog.mainloop()
    return 1
