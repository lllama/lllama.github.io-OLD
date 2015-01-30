#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Felix Ingram'
SITENAME = 'Stupentest'
SITEURL = ''

PATH = 'content'

STATIC_PATHS = ['images', r'extra\CNAME']
EXTRA_PATH_METADATA = {r'extra\CNAME': {'path':'CNAME'},}

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = 'en'

THEME = r'../pelican-themes/monospace'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
        )

# Social widget
SOCIAL = (('Twitter', 'https://twitter.com/lllamaboy'),
        ('Github', 'https://github.com/lllama'),)

DEFAULT_PAGINATION = False
DEFAULT_METADATA = {
        'status': 'draft'
        }

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
