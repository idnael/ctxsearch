# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

from gi.repository import Gtk, Gdk,GObject

import subprocess
import yaml, os, shutil
from gettext import gettext as _

AUTHOR = "Copyright © Daniel P. Carvalho <idnael@pegada.net>"
WEBSITE = "http://idnael.pegada.net/ctxsearch"
VERSION = "0.7"

#CONFIG_DIR = os.path.join(os.getenv("HOME"), ".ctxsearch")

class Config:
    def __init__(self, cfgdir):
        self.cfgdir = cfgdir
        self.cfgfile = os.path.join(self.cfgdir, "actions.yaml")
        self.config = {}
        self.config_time = None

        # the data dir is based on the python module dir
        #self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        py_dir = os.path.dirname(__file__)
        if py_dir.startswith("/usr/local/lib/"):
            self.data_dir = "/usr/local/share/ctxsearch"
        elif py_dir.startswith("/usr/lib/"):
            self.data_dir = "/usr/share/ctxsearch"
        else:
            self.data_dir = os.path.join(py_dir, "../data")
            if not os.path.exists(self.data_dir):
                raise "Can't find data dir"

        self.help_file = os.path.join(self.data_dir, "ctxsearch-help.html")

        self.DEBUG = True
        
        self.check()


    # return true if config was changed on config file
    def check(self):
        # if there is no config dir, creates a default configuration
        if not os.path.exists(self.cfgdir):
            os.makedirs(self.cfgdir)
            os.makedirs(os.path.join(self.cfgdir, "favicons"))

        if not os.path.exists(self.cfgfile):
            shutil.copy(os.path.join(self.data_dir, "default_actions.yaml"), self.cfgfile)

        try:
            if self.config_time and self.config_time == os.path.getmtime(self.cfgfile):
                return False

            # set the config time event if there was an error in the config file, 
            # so I don't need to read again
            self.config_time = os.path.getmtime(self.cfgfile)

            f =open(self.cfgfile, "r")
            self.config = yaml.load(f)
            f.close()

        except Exception as ex:
            print(ex)
            raise Exception(_("Error in config file %s") % self.cfgfile)

        #???
        self.DEBUG = "debug" in self.config and self.config["debug"]
        return True

    # gets a property value
    def property(self, name, default=None):

        if name in self.config:
            return self.config[name]
        else:
            return default

