#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi: ts=2:et 

import sys
import re 
import urllib
import pycurl
import StringIO


class AudioClip:
  def __init__(self):
    self.url = ''
    self.type = ''
    self.bitrate = ''

  def download(self, dest='a.aac'):
    with open(dest, 'wb') as f:
      c = pycurl.Curl()
      c.setopt(pycurl.URL, self.url)
      c.setopt(pycurl.FOLLOWLOCATION, 1)
      c.setopt(pycurl.WRITEFUNCTION, f.write)
      c.setopt(pycurl.NOPROGRESS, 0)
      c.setopt(pycurl.HTTPHEADER, ['Referer: %s' % self.url, 'Origin: http://www.youtube.com'])
      c.perform()
      c.close()

  @staticmethod
  def parse(format_raw):
    clip = AudioClip()
    for k, v in [kv.split('=',2) for kv in format_raw.split('&')]:
      if k=='url':
        clip.url = urllib.unquote(v)
      elif k=='bitrate':
        clip.bitrate = int(v)
      elif k=='type':
        clip.type = urllib.unquote(v).split(';')[0]
      elif k=='size': # Skip video clips
        return None
    return clip

  def __str__(self):
    return "AudioClip: %dk/%s %s" % (self.bitrate/1000, self.type, self.url)

  def __repr__(self):
    return self.__str__()


class YouTube:
  def __init__(self, url):
    self.page = self.__download_page(url) 
    self.audioClips = []
    match = re.search('"adaptive_fmts": "(.*?)"', self.page)
    if not match:
      match = re.search('"url_encoded_fmt_stream_map": "(.*?)"', self.page)
    self.audioClips = filter(lambda x:x and x.bitrate > 128000, [AudioClip.parse(x) for x in re.sub(r'\\u([0-9]{4})', lambda x: chr(int(x.group(1),16)), match.group(1)).split(',')])

  def audio(self, high_quality=False):
    if high_quality:
      return self.audioClips[-1]
    return self.audioClips[0]

  def __download_page(self, url):
    f = StringIO.StringIO()
    def callback_write(chunk):
      f.write(chunk)
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.WRITEFUNCTION, callback_write)
    c.perform()
    c.close()
    return f.getvalue()


if __name__=='__main__':
  YouTube(sys.argv[1]).audio(high_quality=False).download('my.aac')

