#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# vs: ts=2:et 
import locale
locale.setlocale(locale.LC_ALL, '')

import curses
import re
import time

#sentences = [
#  "In every moment of your life, your skills are growing.",
#]

"""
TODO: 줄의 끝에 다다랐을때 addch가 깨지지 않게 하기 

"""

DEBUG = True
THRESHOLD_INFO  = 70
THRESHOLD_WARN  = 170
THRESHOLD_FATAL = 240

def log(value):
  if DEBUG:
    with open('log', 'a') as f:
      f.write('%s\n' % value) 
  
def chr_if_possible(p):
  if p < 256:
    return chr(p)
  return None


class History:
  def __init__(self):
    self.sentence = None
    self.elapsed = 0.0
    self.cpm = 0
    self.diffs = []
    self.offset_warn = {}
    self.offset_fatal = {}

class InputField:
  def __init__(self, window):
    self.window = window
    self.x = 0
    self.y = 0
    self.key_buffer = []
    self.timestamps = []
    self.strict = None

  def set_strict(self, line):
    self.strict = line

  def can_type(self, ch):
    if not self.strict:
      return True
    if self.strict[self.x]==ch:
      return True
    return False

  def getch(self):
    return self.window.getch(self.y, self.x)

  def add(self, ch):
    self.window.addch(self.y, self.x, ch)
    self.x += 1 
    self.key_buffer.append(ch)
    self.timestamps.append(time.time())

  def backspace(self):
    if len(self.key_buffer)<1:
      return
    self.x -= 1
    self.key_buffer.pop()
    self.timestamps.pop()
    self.window.addch(self.y, self.x, ' ')
  
  def redraw_keybuffer(self):
    for i, ch in enumerate(self.key_buffer):
      self.window.addch(self.y, i, ch)

  def reset(self): # C-u
    typed = self.x
    self.x = 0
    self.key_buffer = []
    self.timestamps = []
    # count how many times user try to reset 
    for x in range(self.x, typed):
      self.window.addch(self.y, x, ' ')
    return typed

  def __init_buffers(self):
    self.key_buffer = []
    self.timestamps = []
    self.x = 0

  def newline(self):
    if self.x==0:
      return None
    result = self.__result()
    if not result:
      return None
    result.sentence = ''.join(self.key_buffer)
    self.__init_buffers()
    return result

  def clear(self):
    _, w = self.window.getmaxyx()
    for x in range(w-1):
      self.window.addch(self.y, x, ' ')

  def __result(self):
    if len(self.timestamps) < 2:
      return None

    r = History()
    def reducer(x,y):
      r.diffs.append(int((y-x)*1000))
      return y
    reduce(reducer, self.timestamps)
    r.elapsed = self.timestamps[-1] - self.timestamps[0]
    r.cpm = len(self.key_buffer) * (60.0 / r.elapsed) 

    for x, diff in enumerate(r.diffs):
      if diff > THRESHOLD_FATAL:
        r.offset_fatal[x+1] = True
      elif diff > THRESHOLD_WARN:
        r.offset_warn[x+1] = True
    return r

def resized(stdscr, field, histories):
  stdscr.clear()
  stdscr.border()
#  stdscr.addstr(1, 2, sentences[0])

  height, width = stdscr.getmaxyx()

  field_y = height-2
  prompt = "~/victoria>"
  prompt_x = 2
  prompt_w = len(prompt)
  stdscr.addstr(field_y, prompt_x, prompt[:-1], curses.color_pair(4))
  stdscr.addstr(field_y, prompt_x+prompt_w-1, prompt[-1:])

  field.window.resize(1, width-prompt_x-prompt_w-12)
  field.window.mvwin(field_y, prompt_x + prompt_w + 1)
  field.clear()

  redraw_histories(stdscr, histories)

  stdscr.refresh()

def clear_line(window, y):
  _, w = window.getmaxyx()
  for x in range(1, w-1-1):
    try:
      window.addch(y, x, ' ')
    except: 
      raise Exception("x=%d, y=%d" % (x, y))

def redraw_histories(stdscr, datas):
  height, width = stdscr.getmaxyx()

  start_y = 1 
  last_y = height-3
  x_sentence = 14
  
  y = last_y
  lines = 0
  for item in datas[::-1]:
    lines += 1
    if lines > height-5:
      break

    # Clear line 
    clear_line(stdscr, y)

    # Draw CPM
    x = x_sentence - 1 - 4 - 2 - 4 - 1
    stdscr.addstr(y, x, '%4.1f| %4d|' % (item.elapsed, item.cpm))

    # Draw sentence 
    x = x_sentence
    for offset, ch in enumerate(item.sentence):
      color = curses.color_pair(1)
      if item.offset_warn.has_key(offset):
        color = curses.color_pair(3)
      elif item.offset_fatal.has_key(offset):
        color = curses.color_pair(2)
      stdscr.addch(y, x, ch, color)
      x += 1

    # Draw stat detail 
    if lines==1: # can be configured by manual navigation 
      for l in range(y-3, y):
        clear_line(stdscr, l)

      x = x_sentence 
      for diff in item.diffs: 
        x += 1
        if diff < THRESHOLD_INFO:
          continue
        diff_s = '%3d' % diff
        color = curses.color_pair(1)
        if diff > THRESHOLD_FATAL:
          color = curses.color_pair(2)
        elif diff > THRESHOLD_WARN:
          color = curses.color_pair(3)

        if diff > 999:
          diff_s = '!!!'
        l_y = y-3
        for ch in diff_s:
          stdscr.addch(l_y, x, ch, color)
          l_y += 1
      y -= 3

    y = y-1
    if y < start_y:
      break
  stdscr.refresh()

def main(stdscr):
  curses.noecho()
  curses.cbreak()
  stdscr.clear()

  curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)

  printable = re.compile(r'[A-Za-z \-0-9_.\'"|,;:~!@#$%^&*()+=/?`<>\[\]{}\\]')

  field = InputField(stdscr.subwin(1,10,10,2))
  resized(stdscr, field, [])
  stdscr.refresh()

  histories = []

  while True:
    try:
      key = field.getch()
    except KeyboardInterrupt:
      break
    if key==0x11: # C-q
      break
    if key==0x0a: # enter 
      history = field.newline()
      if history:
        histories.append(history)
        redraw_histories(stdscr, histories)
      field.clear()
      continue
    if key==0x7f: # backspace 
      field.backspace()
      continue
    if key==0x15: # C-u (reset)
      field.reset()
      continue

    ch = chr_if_possible(key)
    if not ch:
      if key==0x19a: # screen bounds resized
        resized(stdscr, field, histories)
        field.redraw_keybuffer()
        log('resized')
        continue
      log('Unexpected special key: %d' % key)
      continue
    if printable.match(ch):
      if not field.can_type(ch):
        log('beep!')
        continue
      field.add(ch)
    else: 
      log('code: 0x%02x, char: %s' % (key, chr_if_possible(key)))

curses.wrapper(main)
