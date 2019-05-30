# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.


# para criar debs:
from distutils.core import setup

setup(name='ctxsearch',
      version='0.5',
      packages=['ctxsearch'],
      scripts=['scripts/ctxsearch'],
      data_files=[('share/ctxsearch', ['data/ctxsearch-help.html', 'data/floating.png', 'data/app_icon.png','data/default_actions.yaml']),
                  ('/etc/xdg/autostart', ['ctxsearch-autostart.desktop'])]
      )

