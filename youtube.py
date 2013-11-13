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

VERBOSE = False

class MediaClip:
  def __init__(self):
    self.page = None
    self.url = ''
    self.type = ''
    self.bitrate = 0
    self.localFilePath = None
    self.quality = None
    self.screensize = None

  def download(self, dest):
    if not dest:
      dest = "%s.m4a" % re.search(r'property="og:title" content="(.*?)"',self.page).group(1)
      dest = re.sub('/', '', dest)

    with open(dest, 'wb') as f:
      c = pycurl.Curl()
      c.setopt(pycurl.URL, self.url)
      if VERBOSE:
        c.setopt(pycurl.VERBOSE, 1)
      c.setopt(pycurl.FOLLOWLOCATION, 1)
      c.setopt(pycurl.WRITEFUNCTION, f.write)
      c.setopt(pycurl.NOPROGRESS, 0)
      c.setopt(pycurl.HTTPHEADER, ['Referer: %s' % self.url, 'Origin: http://www.youtube.com'])
      c.perform()
      rescode = c.getinfo(pycurl.RESPONSE_CODE)
      c.close()
    
    if rescode/100==4:
      raise Exception('HTTP Error: %d, url=%s' % (rescode, self.url))
    self.localFilePath = dest
    return self

  def download_mock(self, dest='a.aac'):
    shutil.copy('tmp.aac', dest)
    self.localFilePath = dest
    return self

  def normalize(self, start_time=None):
    """
    Normalizing needs mutagen module and ffmpeg.

    @start_time start time as string '00:04:11.2', it'll passed to ffmpeg as -ss option.
    """
    if not self.localFilePath:
      raise Exception('please download first')

    extra_options = ''
    if start_time:
      extra_options += ' -ss "%s"' % start_time
    
    tmp = 'intermediate.m4a'
    os.system('ffmpeg -i "%s" -y -vn -ab %d %s "%s"' % (self.localFilePath, self.bitrate, extra_options, tmp))
    shutil.move(tmp, self.localFilePath)

    from mutagen.mp4 import MP4, MP4Cover
    f = MP4(self.localFilePath)
    f.tags['\xa9nam'] = re.search(r'property="og:title" content="(.*?)"',self.page).group(1)
    f.tags['\xa9alb'] = 'YouTube.com'
    f.tags['\xa9cmt'] = re.search(r'property="og:url" content="(.*?)"',self.page).group(1)

    cover_data = StringIO.StringIO()
    c = pycurl.Curl()
    if VERBOSE:
      c.setopt(pycurl.VERBOSE, 1)
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
    clip = MediaClip()
    for k, v in [kv.split('=',2) for kv in format_raw.split('&')]:
      if VERBOSE and k != 'url':
        print k, urllib.unquote(v)

      if k=='url':
        clip.url = urllib.unquote(v)
      elif k=='bitrate':
        clip.bitrate = int(v)
      elif k=='quality':
        clip.quality = v
      elif k=='type':
        clip.type = urllib.unquote(v).split(';')[0]
      elif k=='size': 
        clip.screensize = v
    return clip

  def __str__(self):
    return "MediaClip: %s/%s" % (self.bitrate, self.type)

  def __repr__(self):
    return self.__str__()


class YouTube:
  def __init__(self, url):
    self.url = url
    self.page = self.__download_page() 
    match = re.search('"adaptive_fmts": "(.*?)"', self.page)
    if not match:
      match = re.search('"url_encoded_fmt_stream_map": "(.*?)"', self.page)

    self.clips = [MediaClip.parse(x) for x in re.sub(r'\\u([0-9]{4})', lambda x: chr(int(x.group(1),16)), match.group(1)).split(',')]
    for clip in self.clips:
      clip.page = self.page
    self.audioClips = filter(lambda x:x and x.bitrate > 128000, self.clips)

  def audio(self):
    if len(self.audioClips)==0:
      c = filter(lambda x: x.quality=='medium', self.clips)[1]
      print c 
      return c
    return self.audioClips[0]

  def __download_page(self):
    f = StringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, self.url)
    if VERBOSE:
      c.setopt(pycurl.VERBOSE, 1)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.WRITEFUNCTION, f.write)
    c.perform()
    c.close()
    return f.getvalue()


if __name__=='__main__':
  import getopt
  try:
    opts, args = getopt.getopt(sys.argv[1:], "u:o:s:v", \
      ['url=', 'output=', 'start', 'verbose'])
  except getopt.GetoptError as err:
    print(err)
    sys.exit(1)

  url = None
  local_file = None
  start_time = None
  for k, v in opts:
    if k in ('-u', '--url'):
      url = v 
    elif k in ('-o', '--output'):
      local_file = v
    elif k in ('-s', '--starttime'):
      start_time = v
    elif k in ('-v', '--verbose'):
      VERBOSE = True

  if not url:
    raise Exception("--url option is mandatory")
      
  y = YouTube(url)
  clip = y.audio()
  try:
    clip.download(local_file)
  except Exception as e:
    with open('page_for_debug.html', 'w') as f:
      f.write(clip.page)
    raise e
  clip.normalize(start_time)
  clip.copy_to_itunes()

