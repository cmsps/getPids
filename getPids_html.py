#!/usr/bin/env python
'''
  getPids station     region | hd | fm | lw | ''     [ extraDays ]

  Wed Apr 5 12:02:10 BST 2017

  Copyright (C) 2017 Peter Scott - p.scott@shu.ac.uk

  Licence
  =======
     This program is free software: you can redistribute it and / or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>

  Purpose
  =======
     Get BBC schedule for today and optional extra days with PIDs and dates
     (most recent last).

  Examples:
  =========
     $ getPids bbcone yorkshire
     $ getPids bbctwo hd 6
     $ getPids bbctwo england 30
     $ getPids radio4 fm
     $ getPids radio3 ''
     $ getPids 1xtra ''
     $ getPids 6music ''

  Notes:
  ======
     I am not a Python programmer.  This is a transcription of an earlier
     shell script that used sed and awk for the screen scraping.  All offers
     of improvement would be gladly accepted.

     The output order differs from that of the shell script version.
     This is partly to avoid reinventing the tac command in Python.

     I am not sure this version with HTMLParser.py will be easier to
     maintain than the previous one.
'''

from HTMLParser import HTMLParser
import requests, re, sys, datetime, time, os

class MyHTMLParser( HTMLParser):
  def __init__( self):
    self.date = ''
    self.time = ''
    self.pid = ''
    self.title = ''
    self.subtitle = ''
    self.repeat = ''
    self.step = 0
    self.expected = ''
    self.hadPid = {}
    HTMLParser.__init__( self)


  def printProgramme( self):
    ''' this is messy but it avoids print's trailing spaces!
    '''

    # drop tomorrow's programmes and repeated PIDs
    #
    if self.date == self.expected and self.pid not in self.hadPid:
        print '{0}-{1} {2}'.format( self.date, self.time, self.pid),
        if self.subtitle + self.repeat == '':
            print '"{0}"'.format( self.title)
        elif self.repeat == '':
            print '"{0} - {1}"'.format( self.title, self.subtitle)
        elif self.subtitle == '':
            print '"{0}" {1}'.format( self.title, self.repeat)
        else:
            print '"{0} - {1}" {2}'.format( \
                                        self.title, self.subtitle, self.repeat)
        self.hadPid [self.pid] = True


  def handle_starttag( self, tag, attrs):

    # The h3 tag starts a new programme.  When we get one, print
    # the previous programme, if any, and prepare for the next.
    #
    if tag == 'h3':
        if self.step != 0:
            self.printProgramme()
        self.date = ''
        self.time = ''
        self.pid = ''
        self.title = ''
        self.subtitle = ''
        self.repeat = ''
        self.step = 1

    # for all html tags, examine the attributes and values and collect the
    # relevant ones
    #
    for n in range( 0, len( attrs)):
        attr  = attrs [n][0]
        value = attrs [n][1]
        if self.step == 1 and attr == 'content':
            self.date = re.sub( '-', '/', value[0:10])
            self.step = 2
        elif self.step == 2 and value == 'timezone--time':
            self.step = 3   # next data
        elif self.step == 4 and attr == 'data-pid':
            self.pid = value
            self.step = 5
        elif self.step == 5 and value == 'programme__title ':
            self.step = 6
        elif self.step == 6 and value == 'name':
            self.step = 7   # next data
        elif self.step == 8 and value == 'programme__subtitle centi':
            self.step = 9
        elif self.step == 9 and value == 'name':
            self.step = 10   # next data
        elif self.step == 11 and value == 'Repeat':
            self.repeat = '(R)'
            self.step = 12   # why not?


  def handle_data( self, data):
      if self.step == 3:
          self.time = data
          self.step = 4
      elif self.step == 7:
          self.title = data
          self.step = 8
      elif self.step == 10:              # subtitle can be more than one line
          data = data.strip( ' \t\n\r')
          if data[-1:] == ',':
              data = data + ' '
          self.subtitle = self.subtitle + data


  def handle_endtag( self, tag):
      if tag == 'h4':
          self.step = 11            # terminate subtitle
      elif tag == 'html':
          self.printProgramme()     # flush out final programme
          self.step = 0             # prepare for possible next page


  def newDate( self, expected):
    self.expected = expected
    self.step = 0             # why not?


def errorMessage( message):
  sys.stderr.write( NAME + ': ' + message + '\n')


def usage():
  sys.stderr.write( 'Usage: ' + NAME + \
                  ' station   region | hd | fm | lw | ''  [ extraDays ]' + '\n')
  exit( 1)


def getArgs():
  global NAME, station, region, extra

  nargs = len( sys.argv) - 1
  NAME = os.path.basename( sys.argv [0])
  if nargs < 2 or nargs > 3:
      usage()
  station = sys.argv [1]
  region = sys.argv [2]
  if region.isdigit():
      errorMessage( 'warning: ' + region + ": doesn't look like a region")
  if nargs == 3:
      try:
          extra = int( sys.argv [3])
      except ValueError:
          extra = sys.argv [3]
          errorMessage( extra + ": isn't a number")
          exit( 2)


def mkDates (extra):
  ''' make a list of dates so that running through midnight while waiting
      for web pages doesn't mess up datetime.timedelta()
  '''
  start = 0
  finish = 999
  while start != finish:      # repeat until would be handy
      dateQueue = []
      today = datetime.date.today()
      start = today.day
      for n in range( extra, -1, -1):
          past = today - datetime.timedelta( days=n)
          year = str( past.year)
          month = str( past.month).zfill( 2)
          day = str( past.day).zfill( 2)
          date = (year, month, day)
          dateQueue.append( date)
      finish = today.day
  return dateQueue


parser = MyHTMLParser()  # kept between pages to keep track of repeated PIDs

NAME = ''                # globals
station = ''
region = ''
extra = 0

getArgs()
dates = mkDates( extra)
while len( dates) != 0:
    year = dates [0][0]
    month = dates [0][1]
    day = dates [0][2]
    date = year + '/' + month + '/' + day
    remaining = len( dates) - 1
    url = 'http://www.bbc.co.uk/' + station + '/programmes/schedules/'
    if region == '':
        url = url + date
    else:
        url = url + region + '/' + date
    try:
        page = requests.get(url)
        response = page.status_code
    except:
        errorMessage( 'network error')
        exit( 3)
    if response == 200:
        parser.newDate( date)
        parser.feed( page.content)
    else:
        error = "couldn't get: " + url
        if remaining != 0:
            error = error + ' (continuing without it)'
        errorMessage( error)
        if remaining == 0:
            exit( 4)
    if remaining != 0:
        time.sleep( 3)          ################ kindness
    del dates [0]
exit( 0)
