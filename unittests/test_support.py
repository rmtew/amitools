from amitools.vamos.MEM import MEM
from musashi import m68k


class MusashiMEM(MEM):
  def __init__(self):
    MEM.__init__(self,"musashi")
  def init(self,ram_size_kib):
    self.ram_size = ram_size_kib * 1024
    return m68k.mem_init(ram_size_kib)
  def free(self):
    m68k.mem_free()
  def reserve_special_range(self,num_pages):
    return m68k.mem_reserve_special_range(num_pages)
  def set_special_range_read_func(self,page_addr, width, func):
    m68k.mem_set_special_range_read_func(page_addr, width, func)
  def set_special_range_write_func(self,page_addr, width, func):
    m68k.mem_set_special_range_write_func(page_addr, width, func)
  def set_mem_trace_mode(self,on):
    m68k.mem_set_trace_mode(on)
  def set_mem_trace_func(self,func):
    m68k.mem_set_trace_func(func)
  def read_ram(self,width, addr):
    return m68k.mem_ram_read(width, addr)
  def write_ram(self,width, addr, val):
    m68k.mem_ram_write(width,addr,val)
  def read_ram_block(self,addr,size,data):
    m68k.mem_ram_read_block(addr,size,data)
  def write_ram_block(self,addr,size,data):
    m68k.mem_ram_write_block(addr,size,data)
  def clear_ram_block(self,addr,size,value):
    m68k.mem_ram_clear_block(addr,size,value)
