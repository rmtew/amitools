/* MusashiCPU <-> vamos memory interface
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <stdlib.h>
#include <stdio.h>
#include "mem.h"

#define NUM_PAGES   256

/* ----- Data ----- */
static uint8_t *ram_data;
static uint     ram_size;
static uint     ram_pages;

static read_func_t    r_func[NUM_PAGES][3];
static write_func_t   w_func[NUM_PAGES][3];

static invalid_func_t invalid_func;
static int mem_trace = 0;
static trace_func_t trace_func;
static int is_end = 0;
static uint special_page = NUM_PAGES;

/* ----- Default Funcs ----- */
static void default_invalid(int mode, int width, uint addr)
{
  printf("INVALID: %c(%d): %06x\n",(char)mode,width,addr);
}

static void default_trace(int mode, int width, uint addr, uint val)
{
  printf("%c(%d): %06x: %x\n",(char)mode,width,addr,val);
}

/* ----- End Access ----- */
static uint rx_end(uint addr)
{
  return 0;
}

static uint r16_end(uint addr)
{
  return 0x4e70; // RESET opcode
}

static void wx_end(uint addr, uint val)
{
  // do nothing
}

/* ----- Invalid Access ----- */
static void set_all_to_end(void)
{
  for(int i=0;i<NUM_PAGES;i++) {
    r_func[i][0] = rx_end;
    r_func[i][1] = r16_end;
    r_func[i][2] = rx_end;
    w_func[i][0] = wx_end;
    w_func[i][1] = wx_end;
    w_func[i][2] = wx_end;
  }
  is_end = 1;
}

static uint r8_fail(uint addr)
{
  invalid_func('R', 0, addr);
  set_all_to_end();
  return 0;
}

static uint r16_fail(uint addr)
{
  invalid_func('R', 1, addr);
  set_all_to_end();
  return 0;
}

static uint r32_fail(uint addr)
{
  invalid_func('R', 2, addr);
  set_all_to_end();
  return 0;
}

static void w8_fail(uint addr, uint val)
{
  invalid_func('W', 0, addr);
  set_all_to_end();
}

static void w16_fail(uint addr, uint val)
{
  invalid_func('W', 1, addr);
  set_all_to_end();
}

static void w32_fail(uint addr, uint val)
{
  invalid_func('W', 2, addr);
  set_all_to_end();
}

/* ----- RAM access ----- */
static uint r8_ram(uint addr)
{
  return ram_data[addr];
}

static uint r16_ram(uint addr)
{
  return (ram_data[addr] << 8) | ram_data[addr+1];
}

static uint r32_ram(uint addr)
{
  return (ram_data[addr] << 24) | (ram_data[addr+1] << 16) | (ram_data[addr+2] << 8) | (ram_data[addr+3]);
}

static void w8_ram(uint addr, uint val)
{
  ram_data[addr] = val;
}

static void w16_ram(uint addr, uint val)
{
  ram_data[addr] = val >> 8;
  ram_data[addr+1] = val & 0xff;
}

static void w32_ram(uint addr, uint val)
{
  ram_data[addr]   = val >> 24;
  ram_data[addr+1] = (val >> 16) & 0xff;
  ram_data[addr+2] = (val >> 8) & 0xff;
  ram_data[addr+3] = val & 0xff;
}

/* ----- Musashi Interface ----- */

unsigned int  m68k_read_memory_8(unsigned int address)
{
  uint page = address >> 16;
  uint val = r_func[page][0](address);
  if(mem_trace) {
    trace_func('R',0,address,val);
  }
  return val;
}

unsigned int  m68k_read_memory_16(unsigned int address)
{
  uint page = address >> 16;
  uint val = r_func[page][1](address);
  if(mem_trace) {
    trace_func('R',1,address,val);
  }
  return val;
}

unsigned int  m68k_read_memory_32(unsigned int address)
{
  uint page = address >> 16;
  uint val = r_func[page][2](address);
  if(mem_trace) {
    trace_func('R',2,address,val);
  }
  return val;
}

void m68k_write_memory_8(unsigned int address, unsigned int value)
{
  uint page = address >> 16;
  w_func[page][0](address, value);
  if(mem_trace) {
    trace_func('W',0,address,value);
  }
}

void m68k_write_memory_16(unsigned int address, unsigned int value)
{
  uint page = address >> 16;
  w_func[page][1](address, value);
  if(mem_trace) {
    trace_func('W',1,address,value);
  }
}

void m68k_write_memory_32(unsigned int address, unsigned int value)
{
  uint page = address >> 16;
  w_func[page][2](address, value);
  if(mem_trace) {
    trace_func('W',2,address,value);
  }
}

/* ----- API ----- */

int mem_init(uint ram_size_kib)
{
  ram_size = ram_size_kib * 1024;
  ram_pages = ram_size_kib / 64;
  ram_data = (uint8_t *)malloc(ram_size);
  
  for(int i=0;i<NUM_PAGES;i++) {
    if(i < ram_pages) {
      r_func[i][0] = r8_ram;
      r_func[i][1] = r16_ram;
      r_func[i][2] = r32_ram;
      w_func[i][0] = w8_ram;
      w_func[i][1] = w16_ram;
      w_func[i][2] = w32_ram;
    } else {
      r_func[i][0] = r8_fail;
      r_func[i][1] = r16_fail;
      r_func[i][2] = r32_fail;
      w_func[i][0] = w8_fail;
      w_func[i][1] = w16_fail;
      w_func[i][2] = w32_fail;
    }
  }
  
  trace_func = default_trace;
  invalid_func = default_invalid;

  return (ram_data != NULL);
}

void mem_free(void)
{
  free(ram_data);
  ram_data = NULL;
}

void mem_set_invalid_func(invalid_func_t func)
{
  invalid_func = func;
}

void mem_set_trace_mode(int on)
{
  mem_trace = on;
}

void mem_set_trace_func(trace_func_t func)
{
  trace_func = func;
}

int mem_is_end(void)
{
  return is_end;
}

uint mem_reserve_special_range(uint num_pages)
{
  uint begin_page = special_page - num_pages;
  if(begin_page < ram_pages) {
    return 0;
  }
  special_page = begin_page;
  return begin_page << 16;
}

void mem_set_special_range_read_func(uint page_addr, uint width, read_func_t func)
{
  uint page = page_addr >> 16;
  r_func[page][width] = func;
}

void mem_set_special_range_write_func(uint page_addr, uint width, write_func_t func)
{
  uint page = page_addr >> 16;
  w_func[page][width] = func;
}

uint mem_read(int mode, uint addr)
{
  int save_mem_trace = mem_trace;
  mem_trace = 0;
  uint val = 0;
  switch(mode) {
    case 0:
      val = m68k_read_memory_8(addr);
      break;
    case 1:
      val = m68k_read_memory_16(addr);
      break;
    case 2:
      val = m68k_read_memory_32(addr);
      break;
  }
  mem_trace = save_mem_trace;
  return val;
}

void mem_write(int mode, uint addr, uint value)
{
  int save_mem_trace = mem_trace;
  mem_trace = 0;
  switch(mode) {
    case 0:
      m68k_write_memory_8(addr, value);
      break;
    case 1:
      m68k_write_memory_16(addr, value);
      break;
    case 2:
      m68k_write_memory_32(addr, value);
      break;
  }
  mem_trace = save_mem_trace;
}