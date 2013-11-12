#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi: ts=2:et 

import os
import sys
import re 
import urllib
import pycurl
import StringIO
import shutil


class AudioClip:
  def __init__(self):
    self.page = None
    self.url = ''
    self.type = ''
    self.bitrate = ''
    self.localFilePath = None

  def download(self, dest):
    if not dest:
      dest = "%s.m4a" % re.search(r'property="og:title" content="(.*?)"',self.page).group(1)

    with open(dest, 'wb') as f:
      c = pycurl.Curl()
      c.setopt(pycurl.URL, self.url)
      c.setopt(pycurl.FOLLOWLOCATION, 1)
      c.setopt(pycurl.WRITEFUNCTION, f.write)
      c.setopt(pycurl.NOPROGRESS, 0)
      c.setopt(pycurl.HTTPHEADER, ['Referer: %s' % self.url, 'Origin: http://www.youtube.com'])
      c.perform()
      c.close()
    self.localFilePath = dest
    return self

  def download_mock(self, dest='a.aac'):
    shutil.copy('tmp.aac', dest)
    self.localFilePath = dest
    return self

  def normalize(self):
    """
    Normalizing needs mutagen module and ffmpeg.
    """
    if not self.localFilePath:
      raise Exception('please download first')
    tmp = 'intermediate.m4a'
    os.system('ffmpeg -i "%s" -y -ab %d "%s"' % (self.localFilePath, self.bitrate, tmp))
    shutil.move(tmp, self.localFilePath)

    from mutagen.mp4 import MP4, MP4Cover
    f = MP4(self.localFilePath)
    f.tags['\xa9nam'] = re.search(r'property="og:title" content="(.*?)"',self.page).group(1)
    f.tags['\xa9alb'] = 'YouTube.com'
    f.tags['\xa9cmt'] = re.search(r'property="og:url" content="(.*?)"',self.page).group(1)

    cover_data = StringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, re.search(r'property="og:image" content="(.*?)"',self.page).group(1))
    c.setopt(pycurl.WRITEFUNCTION, cover_data.write)
    c.perform()
    c.close()
    f.tags['covr'] = [MP4Cover(cover_data.getvalue(), MP4Cover.FORMAT_JPEG)]
    f.save()
    return self
  
  def copy_to_itunes(self):
    if not self.localFilePath:
      raise Exception('please download first')
    shutil.copy(self.localFilePath, '%s/Music/iTunes/iTunes Media/Automatically Add to iTunes.localized/%s' % (os.environ['HOME'], os.path.split(self.localFilePath)[-1]))

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
    self.url = url
    self.page = self.__download_page() 
    match = re.search('"adaptive_fmts": "(.*?)"', self.page)
    if not match:
      match = re.search('"url_encoded_fmt_stream_map": "(.*?)"', self.page)
    self.audioClips = []
    self.audioClips = filter(lambda x:x and x.bitrate > 128000, [AudioClip.parse(x) for x in re.sub(r'\\u([0-9]{4})', lambda x: chr(int(x.group(1),16)), match.group(1)).split(',')])
    for clip in self.audioClips:
      clip.page = self.page

  def audio(self):
    return self.audioClips[0]

  def __download_page(self):
    f = StringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, self.url)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.WRITEFUNCTION, f.write)
    c.perform()
    c.close()
    return f.getvalue()


if __name__=='__main__':
  url = sys.argv[1] # http://www.youtube.com/watch?v=zg9tf87MdiM
  local_file = None
  if len(sys.argv)>=3:
    local_file = sys.argv[2]
  #YouTube(url).audio().download(local_file)
  YouTube(url).audio().download(local_file).normalize().copy_to_itunes()

