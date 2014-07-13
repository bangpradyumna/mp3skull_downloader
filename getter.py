#!/usr/bin/env python

# (c) 2011 Rdio Inc
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# include the parent directory in the Python path
#import sys,os.path
#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from urllib2 import URLError, HTTPError, urlopen, Request
from threading import Timer
import os
import re
import socket

socket.setdefaulttimeout(5)

def uen(s):
    return s.encode('utf-8')

songs = open('songs.txt', 'r')

song_l = []
for song in songs:
  partition = song.replace('\n', '').partition(' - ')
  song_l.append([partition[0].replace('/', '\/'), partition[2][:partition[2].find('-')-1]])

folder = 'songs'
site = 'http://mp3skull.com/mp3/{0}.html'

# The file has 2 lines without song names first
for song in song_l[2:]:

  fname = song[0] + ' - ' + song[1]

  if os.path.isfile(folder + '/' + fname + '.mp3'):
    print fname + ' already exists!'
    continue

  song[0] = song[0].lower()
  song[1] = song[1].lower()

  print 'Looking up: {0}'.format(fname)
  query = (song[0] + '_ ' + song[1]).replace(' ', '_')
  html = ''
  try:
    html = urlopen(site.format(query)).read()
  except:
    print "Issue making query: {0}".format(query)
    continue

  soup = BeautifulSoup(html, 'html')

  lefts = soup.findAll('div', {'class' : 'left'})
  rights = soup.findAll(id='right_song')

  choices = []

  for left, right in zip(lefts, rights):
    correct_line = [line for line in left if 'kbps' in line]
    if correct_line:
        bitrate = correct_line[0].replace('\n', '').replace('\t', '')[:3]
        if bitrate:
            try:
              bitrate = int(bitrate)
            except ValueError:
              continue
    else:
      continue

    song_name = uen(right.div.string)
    #print 'right: {0}\n\n\n\nright.div: {1}\n\n\n\nright.div.string: {2}\n\n\n\nright.div.b: {3}\n\n\n'.format(
    #    right, right.div, right.div.string, right.div.b)
    url = right.find('a')['href']
    forwards = ' - '.join(song)
    backwards = ' - '.join([song[1], song[0]])
    if forwards in song_name.lower() or backwards in song_name.lower():
      if 'remix' in song_name.lower() and 'remix' not in song[0]:
        continue
      choices += [[song_name, bitrate, url]]

  # sort by bitrate
  if choices:
    #choices.sort(lambda x: x[1])
    #print choices
    sorted_choices = reversed(sorted(choices, key=lambda x: x[1]))
    for choice in sorted_choices:
      print choice
      url = choice[2]
      if url.endswith('.mp3'):
        name = song[0] + ' - ' + song[1]
        try:
          resp = urlopen(url, None, 5)
          """
          print "Speed should be being checked...."
          if not good_speed(url):
            print "Slow connection... looking for new source."
            continue
          print "Speed should be done being checked..."
          """
          resp = urlopen(url)
          t = Timer(10.0, resp.close)
          t.start()
          data = resp.read()
          t.cancel()
          resp.close()
        except HTTPError as e:
          print e
          continue
        except URLError:
          print "Oops, timed out..."
          continue
        except socket.timeout:
          print "Timed out..."
          continue
        except AttributeError:
          print "No data to pull... moving on."
          continue

        f = open(folder + '/' + fname + '.mp3', 'w')
        f.write(data)
        f.close()
        print "Wrote song: {0}".format(fname)
        break
  else:
    print "No songs found for query: {0}".format(query)
    continue

songs.close()
