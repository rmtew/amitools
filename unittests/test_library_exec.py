import struct
import unittest
from amitools.vamos.lib.ExecLibrary import ExecLibrary
from amitools.vamos.MainMemory import MainMemory
import test_support

class RawDoFmtTests(unittest.TestCase):
  def setUp(self):
    self.raw_mem = test_support.MusashiMEM()
    if not self.raw_mem.init(1024):
        raise RuntimeError("Failed to create memory object")
    self.mem = MainMemory(self.raw_mem, None)
    self.lib = ExecLibrary(None, None)
    self.start_address = 10000

  def tearDown(self):
    pass
    
  def test_RawDoFmt_number_unsigned(self):
    address = self.start_address
    value = 404040404
    self.mem.access.w16(address, value)
    s = self.lib._RawDoFmt("%d", self.mem.access, self.start_address)
    self.assertEqual(s, str(value & 0xFFFF))

  def test_RawDoFmt_number_unsigned_long(self):
    address = self.start_address
    value = 0xFFFFFFFF
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%ld", self.mem.access, self.start_address)
    self.assertEqual(s, str(value))

  def test_RawDoFmt_number_signed(self):
    address = self.start_address
    value = -32111
    value_string = struct.pack(">h", value)
    self.mem.access.w_data(address, value_string)
    s = self.lib._RawDoFmt("%u", self.mem.access, self.start_address)
    self.assertEqual(s, str(value))

  def test_RawDoFmt_number_signed_long(self):
    address = self.start_address
    value = -4322232
    value_string = struct.pack(">i", value)
    self.mem.access.w_data(address, value_string)
    s = self.lib._RawDoFmt("%lu", self.mem.access, self.start_address)
    self.assertEqual(s, str(value))

  def test_RawDoFmt_cstr(self):
    address = self.start_address
    value = "this is a string"
    string_address = self.start_address + 200
    self.mem.access.w_cstr(string_address, value)
    self.mem.access.w32(address, string_address)
    s = self.lib._RawDoFmt("%s", self.mem.access, self.start_address)
    self.assertEqual(s, value)

  def test_RawDoFmt_bstr(self):
    address = self.start_address
    value = "this is a string"
    string_address = self.start_address + 200
    self.mem.access.w_bstr(string_address, value)
    self.mem.access.w32(address, string_address)
    s = self.lib._RawDoFmt("%b", self.mem.access, self.start_address)
    self.assertEqual(s, value)

  def test_RawDoFmt_hex(self):
    address = self.start_address
    value = 0xFFFFFFFF
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%x", self.mem.access, self.start_address)
    self.assertEqual(s, "%x" % (value & 0xFFFF))

  def test_RawDoFmt_HEX(self):
    address = self.start_address
    value = 0xFFFFFFFF
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%X", self.mem.access, self.start_address)
    self.assertEqual(s, "%X" % (value & 0xFFFF))

  def test_RawDoFmt_hex_long(self):
    address = self.start_address
    value = 0xFFFFFFFF
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%lx", self.mem.access, self.start_address)
    self.assertEqual(s, "%x" % value)

  def test_RawDoFmt_HEX_long(self):
    address = self.start_address
    value = 0xFFFFFFFF
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%lX", self.mem.access, self.start_address)
    self.assertEqual(s, "%X" % value)

  def test_RawDoFmt_char(self):
    address = self.start_address
    value = ord("z")
    self.mem.access.w16(address, value)
    s = self.lib._RawDoFmt("%c", self.mem.access, self.start_address)
    self.assertEqual(s, "z")

  def test_RawDoFmt_char_long(self):
    address = self.start_address
    value = ord("z")
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%lc", self.mem.access, self.start_address)
    self.assertEqual(s, "z")

  def test_RawDoFmt_padding_left(self):
    address = self.start_address
    value = ord("z")
    self.mem.access.w16(address, value)
    s = self.lib._RawDoFmt("%5c", self.mem.access, self.start_address)
    self.assertEqual(s, (" "*(5-1) + "z"))

  def test_RawDoFmt_padding_right(self):
    address = self.start_address
    value = ord("z")
    self.mem.access.w16(address, value)
    s = self.lib._RawDoFmt("%-5c", self.mem.access, self.start_address)
    self.assertEqual(s, ("z" + " "*(5-1)))

  def test_RawDoFmt_length(self):
    address = self.start_address
    value = 102030405
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%.5ld", self.mem.access, self.start_address)
    self.assertEqual(s, str(value)[:5])

  def test_RawDoFmt_length_padding(self):
    address = self.start_address
    value = 102030405
    self.mem.access.w32(address, value)
    s = self.lib._RawDoFmt("%10.5ld", self.mem.access, self.start_address)
    self.assertEqual(s, 5*" " + str(value)[:5])

  def test_RawDoFmt_combination(self):
    address = self.start_address
    self.mem.access.w16(address+0, ord("Z"))
    self.mem.access.w32(address+2, ord("z"))
    string_address = self.start_address + 200
    self.mem.access.w_cstr(string_address, "_string_")
    self.mem.access.w32(address+6, string_address)
    string_address = self.start_address + 300
    self.mem.access.w_bstr(string_address, "_bstring_")
    self.mem.access.w32(address+10, string_address)
    self.mem.access.w16(address+14, 101)
    s = self.lib._RawDoFmt("%c%lc%s...%b%d", self.mem.access, self.start_address)
    self.assertEqual(s, "Zz_string_..._bstring_101")

