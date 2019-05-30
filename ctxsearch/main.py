#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnaed@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.


import sys, os, subprocess
from gettext import gettext as _

from gi.repository import Gtk, Gdk,GObject

from . import config

from . import control
#import ctxsearch.etc as etc

# If you are only interested in Ctrl-c finishing your application and you don't
# need special cleanup handlers, the following will perhaps work for you:
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

GObject.set_application_name('Context Search')
GObject.set_prgname('ctxsearch')

cfgdir = os.path.join(os.getenv("HOME"), ".ctxsearch")
#cfgdir = "_config"

cfg = config.Config(cfgdir)

control.Control(cfg)

Gtk.main()
