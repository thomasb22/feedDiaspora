#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys
import wget
import diaspy
import feedparser
from bs4 import BeautifulSoup
import warnings

__pod__ = 'https://diasporafoundation.org'
__username__ = ''
__passwd__ = ''

feedurl = 'https://example.org/feed.xml'
hashtags = '#feedDiaspora #Diaspora'

database = 'feedDiaspora-db.txt'
tmpdir = 'tmp'
show_summary = False
show_picture = False
maxmsg = 2
maxchar = 1000

c = diaspy.connection.Connection(
	pod=__pod__,
	username=__username__,
	password=__passwd__
)

nbmsg = 0
feed = feedparser.parse(feedurl)

for item in reversed(feed.entries):
	send = True
	soup = BeautifulSoup(item.title, 'lxml')
	title = soup.text
	soup = BeautifulSoup(item.summary, 'lxml')
	summary = soup.text
	link = item.link
	msg = '### ' + title + '\n\n' + link

	if show_summary:
		summary = '> '.join( ( '\n' + summary.lstrip() ).splitlines(True) )
		msg = '### ' + title + '\n\n' + summary + '\n\n' + link

	if hashtags:
		msg += '\n\n' + hashtags

	if show_summary and len(msg) > maxchar and len(summary) > (len(msg) - maxchar) - 2:
		if hashtags:
			maxsum = len(summary) - (len(msg) - maxchar) - 2
		else:
			maxsum = len(summary) - (len(msg) - maxchar) - 1
		msg = title + '\n\n' + summary[:maxsum] + '…\n\n' + link

		if hashtags and len(msg) <= maxchar - (len(hashtags) + 1):
			msg += '\n\n' + hashtags
	elif len(msg) > maxchar and len(title) > (len(msg) - maxchar) - 1:
		maxtitle = len(title) - (len(msg) - maxchar) - 1
		msg = title[:maxtitle] + '… ' + link

		if hashtags and len(msg) <= maxchar - (len(hashtags) + 1):
			msg += ' ' + hashtags

	if len(msg) > maxchar:
		send = False

	if os.path.exists(database):
		db = open(database, "r+")
		entries = db.readlines()
	else:
		db = open(database, "a+")
		entries = []

	for entry in entries:
		if link in entry:
			send = False

	if send:
		if nbmsg == 0:
			c.login()
			stream = diaspy.streams.Stream(c)

		if show_picture and item.enclosures:
			if item.enclosures[0].type[:5] == 'image' and int(item.enclosures[0].length) <= 1000000:
				tmpfilename = item.enclosures[0].href.split('/')[-1]
				tmppath = tmpdir + '/' + tmpfilename
				picture = tmppath

				if not os.path.exists(tmpdir):
					os.mkdir(tmpdir)

				wget.download(item.enclosures[0].href, tmppath)

				try:
					stream.post(text=msg, photo=picture)
				except (diaspy.errors.StreamError) as e:
					warnings.warn('{0}')
				finally:
					pass

				os.remove(tmppath)
		else:
			stream.post(msg)

		db.write(link + '\n')
		db.flush()

		nbmsg = nbmsg + 1
		if nbmsg >= maxmsg:
			break

	db.close()

if os.path.exists(tmpdir):
	os.rmdir(tmpdir)
