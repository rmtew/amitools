import re, struct, sys

from amitools.vamos.AmigaLibrary import *
from lexec.ExecStruct import *
from amitools.vamos.Log import log_exec
from amitools.vamos.Exceptions import *
from amitools.vamos.AccessMemory import AccessMemory
from amitools.vamos.AccessStruct import AccessStruct
from amitools.vamos.Trampoline import Trampoline

class ExecLibrary(AmigaLibrary):
  name = "exec.library"

  def __init__(self, lib_mgr, alloc, version=39, profile=False):
    AmigaLibrary.__init__(self, self.name, version, ExecLibraryDef, profile)
    log_exec.info("open exec.library V%d", self.version)
    self.lib_mgr = lib_mgr
    self.alloc = alloc
    
  def setup_lib(self, lib, ctx):
    AmigaLibrary.setup_lib(self, lib, ctx)
    # setup exec memory
    lib.access.w_s("LibNode.lib_Version", self.version)

  def set_this_task(self, lib, process):
    lib.access.w_s("ThisTask",process.this_task.addr)
    self.stk_lower = process.stack_base
    self.stk_upper = process.stack_end
    
  # ----- System -----
  
  def Disable(self, lib, ctx):
    log_exec.info("Disable")
  def Enable(self, lib, ctx):
    log_exec.info("Enable")
  def Forbid(self, lib, ctx):
    log_exec.info("Forbid")
  def Permit(self, lib, ctx):
    log_exec.info("Permit")
    
  def FindTask(self, lib, ctx):
    task_ptr = ctx.cpu.r_reg(REG_A1)
    if task_ptr == 0:
      addr = lib.access.r_s("ThisTask")
      log_exec.info("FindTask: me=%06x" % addr)
      return addr
    else:
      task_name = ctx.mem.access.r_cstr(task_ptr)
      log_exec.info("Find Task: %s" % task_name)
      raise UnsupportedFeatureError("FindTask: other task!");
  
  def SetSignals(self, lib, ctx):
    new_signals = ctx.cpu.r_reg(REG_D0)
    signal_mask = ctx.cpu.r_reg(REG_D1)
    old_signals = 0
    log_exec.info("SetSignals: new_signals=%08x signal_mask=%08x old_signals=%08x" % (new_signals, signal_mask, old_signals))
    return old_signals
  
  def StackSwap(self, lib, ctx):
    stsw_ptr = ctx.cpu.r_reg(REG_A0)
    stsw = AccessStruct(ctx.mem,StackSwapDef,struct_addr=stsw_ptr)
    # get new stack values
    new_lower = stsw.r_s('stk_Lower')
    new_upper = stsw.r_s('stk_Upper')
    new_pointer = stsw.r_s('stk_Pointer')
    # retrieve current (old) stack
    old_lower = self.stk_lower
    old_upper = self.stk_upper
    old_pointer = ctx.cpu.r_reg(REG_A7) # addr of sys call return
    # get adress of callee
    callee = ctx.mem.access.r32(old_pointer)
    # we report the old stack befor callee
    old_pointer += 4
    log_exec.info("StackSwap: old(lower=%06x,upper=%06x,ptr=%06x) new(lower=%06x,upper=%06x,ptr=%06x)" % (old_lower,old_upper,old_pointer,new_lower,new_upper,new_pointer))
    stsw.w_s('stk_Lower', old_lower)
    stsw.w_s('stk_Upper', old_upper)
    stsw.w_s('stk_Pointer', old_pointer)
    self.stk_lower = new_lower
    self.stk_upper = new_upper
    # put callee's address on new stack
    new_pointer -= 4
    ctx.mem.access.w32(new_pointer,callee)
    # activate new stack
    ctx.cpu.w_reg(REG_A7, new_pointer)
    
  # ----- Libraries -----
  
  def OpenLibrary(self, lib, ctx):
    ver = ctx.cpu.r_reg(REG_D0)
    name_ptr = ctx.cpu.r_reg(REG_A1)
    name = ctx.mem.access.r_cstr(name_ptr)
    lib = self.lib_mgr.open_lib(name, ver, ctx)
    log_exec.info("OpenLibrary: '%s' V%d -> %s" % (name, ver, lib))
    if lib == None:
      return 0
    else:
      return lib.lib_base
  
  def OldOpenLibrary(self, lib, ctx):
    name_ptr = ctx.cpu.r_reg(REG_A1)
    name = ctx.mem.access.r_cstr(name_ptr)
    lib = self.lib_mgr.open_lib(name, 0, ctx)
    log_exec.info("OldOpenLibrary: '%s' -> %s" % (name, lib))
    return lib.lib_base
  
  def CloseLibrary(self, lib, ctx):
    lib_addr = ctx.cpu.r_reg(REG_A1)
    lib = self.lib_mgr.close_lib(lib_addr,ctx)
    if lib != None:
      log_exec.info("CloseLibrary: '%s' -> %06x" % (lib, lib.lib_base))
    else:
      raise VamosInternalError("CloseLibrary: Unknown library to close: ptr=%06x" % lib_addr)
  
  # ----- Memory Handling -----
  
  def AllocMem(self, lib, ctx):
    size = ctx.cpu.r_reg(REG_D0)
    flags = ctx.cpu.r_reg(REG_D1)
    # label alloc
    pc = self.get_callee_pc(ctx)
    tag = ctx.label_mgr.get_mem_str(pc)
    name = "AllocMem(%06x = %s)" % (pc,tag)
    mb = self.alloc.alloc_memory(name,size)
    log_exec.info("AllocMem: %s" % mb)
    return mb.addr
  
  def FreeMem(self, lib, ctx):
    size = ctx.cpu.r_reg(REG_D0)
    addr = ctx.cpu.r_reg(REG_A1)
    if addr == 0 or size == 0:
      log_exec.info("FreeMem: freeing NULL")
      return
    mb = self.alloc.get_memory(addr)
    if mb != None:
      log_exec.info("FreeMem: %s" % mb)
      self.alloc.free_memory(mb)
    else:
      raise VamosInternalError("FreeMem: Unknown memory to free: ptr=%06x size=%06x" % (addr, size))

  def AllocVec(self, lib, ctx):
    size = ctx.cpu.r_reg(REG_D0)
    flags = ctx.cpu.r_reg(REG_D1)
    mb = self.alloc.alloc_memory("AllocVec(@%06x)" % self.get_callee_pc(ctx),size)
    log_exec.info("AllocVec: %s" % mb)
    return mb.addr
    
  def FreeVec(self, lib, ctx):
    addr = ctx.cpu.r_reg(REG_A1)
    if addr == 0:
      log_exec.info("FreeVec: freeing NULL")
      return
    mb = self.alloc.get_memory(addr)
    if mb != None:
      log_exec.info("FreeVec: %s" % mb)
      self.alloc.free_memory(mb)
    else:
      raise VamosInternalError("FreeVec: Unknown memory to free: ptr=%06x" % (addr))
  
  # ----- Misc -----
  
  def RawDoFmt(self, lib, ctx):
    # TODO: Are r16/r32 numeric (d/u) values signed or unsigned? Maybe r_data and struct.unpack is more correct.
    # TODO: To verify correctness this should be unit tested thoroughly.
    format_ptr = ctx.cpu.r_reg(REG_A0)
    format     = ctx.mem.access.r_cstr(format_ptr)
    data_ptr   = ctx.cpu.r_reg(REG_A1)
    putch_ptr  = ctx.cpu.r_reg(REG_A2)
    pdata_ptr  = ctx.cpu.r_reg(REG_A3)
    log_exec.info("RawDoFmt: format='%s' data=%06x putch=%06x pdata=%06x" % (format, data_ptr, putch_ptr, pdata_ptr))

    # Step 1: Do all the formatting.  This will work out how much memory is needed for
    # the trampoline, as well as all the data to churn through it.

    data_mem = ctx.mem.access
    s = self._RawDoFmt(format, data_mem, data_ptr)

    # Step 2: Build the trampoline to pass the formatted text into the callback.
    # The trampoline is not immediately executed.  Instead it gets executed once the call
    # stack has unwound.  If it is to remain local to this function it needs to clean up
    # after itself, i.e. free it's memory - which it can do in instance teardown.
    exec_alloc = self.alloc
    class _Trampoline(Trampoline):
        def __del__(self):
            exec_alloc.free_memory(self.mem)
    
    tr_mem = self.alloc.alloc_memory("SubProcJump", 4 + 6 + 12 * (len(s) + 1) + 4 + 2)
    tr = _Trampoline(ctx, tr_mem)

    tr.init()
    tr.save_all() # 4
    tr.set_ax_l(3, pdata_ptr) # 6
    for i, c in enumerate(s):
        tr.set_dx_l(0, ord(c)) # 6
        tr.jsr(putch_ptr) # 6
    tr.set_dx_l(0, 0) # 6
    tr.jsr(putch_ptr) # 6
    tr.restore_all() # 4
    tr.rts() # 2
    tr.done()

  def _RawDoFmt(self, format, data_mem, data_ptr):
    format_re = re.compile("%(?P<flags>[-]?)(?P<width>0?\d*)(?P<limit>(\.\d+)?)(?P<length>l?)(?P<type>[bduxXsc]{1})")
    format_pos = 0
    s = ""
    while format_pos < len(format):
      match = format_re.search(format, format_pos)
      if match is not None:
        # Copy intermediate text leading up to the found formatting specifier.
        while format_pos < match.start():
          s += format[format_pos]
          format_pos += 1
        data_type = match.group("type")
        format_width_string = match.group("width")
        format_width = None if format_width_string == "" else int(format_width_string)
        format_leading_char = '0' if format_width is not None and format_width_string[0] == '0' else ' '
        format_limit_string = match.group("limit")[1:]
        format_limit = None if format_limit_string == "" else int(format_limit_string)
        format_justify = match.group("flags")
        # Determine data type width and fetch the given value.
        if data_type in ("d", "u", "x", "X", "c"): # signed decimal / unsigned decimal (V37) / hex lowercase / hex uppercase
          data_width = 4 if match.group("length") == "l" else 2
        elif data_type in ("b", "s"): # A c-string or a BSTR. A NULL pointer is treated as an empty string.
          data_width = 4
        if data_width == 4:
          if data_type == "u":
            value_string = data_mem.r_data(data_ptr, data_width)
            value = struct.unpack(">i", value_string)[0]
          else:
            value = data_mem.r32(data_ptr)
        elif data_width == 2:
          if data_type == "u":
            value_string = data_mem.r_data(data_ptr, data_width)
            value = struct.unpack(">h", value_string)[0]
          else:
            value = data_mem.r16(data_ptr)
        # Convert the fetched data to text.
        if data_type == "s":
          value = "" if value == 0 else data_mem.r_cstr(value)
        elif data_type == "b":
          value = "" if value == 0 else data_mem.r_bstr(value)
        elif data_type == "x":
          value = "%x" % value
        elif data_type == "X":
          value = "%X" % value
        elif data_type in ("d", "u"):
          value = "%d" % value
        elif data_type == "c":
          value = "%c" % value
        # Add the formatted text according to width, limit, justification and padding.
        copy_count = len(value) if format_limit is None else min(format_limit, len(value))
        padding_count = max(0, format_width-copy_count) if format_width is not None else 0
        if format_justify != "-":
          s += padding_count * format_leading_char
        s += value[:copy_count]
        if format_justify == "-":
            s += padding_count * format_leading_char
        data_ptr += data_width
        format_pos = match.end()
      else:
        # Copy any trailing text following the final formatting specifier.
        while format_pos < match.start():
          s += format[format_pos]
          format_pos += 1
        break
    return s
    
  # ----- Message Passing -----
  
  def PutMsg(self, lib, ctx):
    port_addr = ctx.cpu.r_reg(REG_A0)
    msg_addr = ctx.cpu.r_reg(REG_A1)
    log_exec.info("PutMsg: port=%06x msg=%06x" % (port_addr, msg_addr))
    has_port = ctx.port_mgr.has_port(port_addr)
    if not has_port:
      raise VamosInternalError("PutMsg: on invalid Port (%06x) called!" % port_addr)
    ctx.port_mgr.put_msg(port_addr, msg_addr)
      
  def GetMsg(self, lib, ctx):
    port_addr = ctx.cpu.r_reg(REG_A0)
    log_exec.info("GetMsg: port=%06x" % (port_addr))
    has_port = ctx.port_mgr.has_port(port_addr)
    if not has_port:
      raise VamosInternalError("GetMsg: on invalid Port (%06x) called!" % port_addr)
    msg_addr = ctx.port_mgr.get_msg(port_addr)
    if msg_addr != None:
      log_exec.info("GetMsg: got message %06x" % (msg_addr))
      return msg_addr
    else:
      log_exec.info("GetMsg: no message available!")
      return 0
  
  def WaitPort(self, lib, ctx):
    port_addr = ctx.cpu.r_reg(REG_A0)
    log_exec.info("WaitPort: port=%06x" % (port_addr))
    has_port = ctx.port_mgr.has_port(port_addr)
    if not has_port:
      raise VamosInternalError("WaitPort: on invalid Port (%06x) called!" % port_addr)
    has_msg = ctx.port_mgr.has_msg(port_addr)
    if not has_msg:
      raise UnsupportedFeatureError("WaitPort on empty message queue called: Port (%06x)" % port_addr)
    msg_addr = ctx.port_mgr.get_msg(port_addr)
    log_exec.info("WaitPort: got message %06x" % (msg_addr))
    return msg_addr
