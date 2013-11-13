#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# vs: ts=2:et 
import locale
locale.setlocale(locale.LC_ALL, '')

import curses
import re
import time

sentences = [
  "In every moment of your life, your skills are growing.",
]

DEBUG = True

def log(value):
  if DEBUG:
    with open('log', 'a') as f:
      f.write('%s\n' % value) 
  
def chr_if_possible(p):
  if p < 256:
    return chr(p)
  return None

class StateMachine:
  def __init__(self, window):
    self.window = window
    self.x = 0
    self.y = 2
    self.key_buffer = []
    self.timestamps = []
    self.history = []
    self.strict = None

  def set_strict(self, line):
    self.strict = line

  def can_type(self, ch):
    if not self.strict:
      return True
    if self.strict[self.x]==ch:
      return True
    return False

  def add(self, ch):
    self.x += 1 
    self.key_buffer.append(ch)
    self.timestamps.append(time.time())

  def backspace(self):
    if len(self.key_buffer)<1:
      return
    self.x -= 1
    self.key_buffer.pop()
    self.timestamps.pop()
  
  def newline(self):
    if self.x==0:
      return
    self.x = 0
    self.history.append(self.key_buffer)
    self.result()
    self.key_buffer = []
    self.timestamps = []
    self.y += 1 

  def reset(self): # C-u
    typed = self.x
    self.x = 0
    self.key_buffer = []
    self.timestamps = []
    return typed

  def result(self):
    if len(self.timestamps) < 2:
      return
    time_diffs = []
    def reducer(x,y):
      time_diffs.append(int((y-x)*1000))
      return y
    reduce(reducer, self.timestamps)
    log("Diffs: %s" % repr(time_diffs))
    elapsed = self.timestamps[-1] - self.timestamps[0]
    cpm = len(self.key_buffer) * (60.0 / elapsed) 
    log('Elapsed: %4.1fs, CPM: %2.1f' % (elapsed, cpm))

    l_x = 1
    for diff in time_diffs:
      color = 0
      if diff > 200:
        color = 1
      elif diff > 160:
        color = 2
      if color>0: 
        self.window.addch(self.y, l_x, self.key_buffer[l_x], curses.color_pair(color))
      l_x += 1

def main(stdscr):
  curses.noecho()
  curses.cbreak()
  stdscr.clear()

  stdscr.addstr(0, 0, "# " + sentences[0])
  curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

  printable = re.compile(r'[A-Za-z \-0-9_.\'"|,;:~!@#$%^&*()+=/?`<>\[\]]')
  sm = StateMachine(stdscr)
  #sm.set_strict(sentences[0])
  while True:
    key = stdscr.getch(sm.y, sm.x)
    if key==0x11: # C-q
      break
    if key==0x0a: # enter 
      sm.newline()
      continue
    if key==0x7f: # backspace 
      sm.backspace()
      stdscr.addch(sm.y, sm.x, ' ')
      continue
    if key==0x15: # C-u (reset)
      for x in range(sm.reset()):
        stdscr.addch(sm.y, x, ' ')
      continue

    ch = chr_if_possible(key)
    if not ch:
      if key==0x19a: # screen bounds resized
        stdscr.refresh()
        continue
    if printable.match(ch):
      if not sm.can_type(ch):
        log('beep!')
        continue
      sm.add(ch)
      stdscr.addch(sm.y, sm.x-1, ch)
    
    log('code: 0x%02x, char: %s, kb: %s' % (key, chr_if_possible(key), ''.join(sm.key_buffer)))

curses.wrapper(main)
