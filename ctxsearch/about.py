# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

from gi.repository import Gtk, Gdk,GObject

from gettext import gettext as _
import os

import config

class About:

    def __init__(self):
        dialog = Gtk.AboutDialog()
        
        description = "CtxSearch - Do actions on selected text.\n"

        # TODO Arranjar outra forma de mostrar isto...
        #if not context.has_language_support():
        #    description += "Please install LangId library for language detection support!\n"

        infos = {
            "name" : "CtxSearch",
            # dont work... "logo-icon-name" : os.path.join(etc.DATA_DIR,"app_icon.png"),
            "version" : config.VERSION,
            "comments" : description,
            "copyright" : config.AUTHOR,
            "website" : config.WEBSITE,
        }

        dialog.set_authors(["Daniel P. Carvalho <idnael@pegada.net>"])

        for prop, val in infos.items():
            dialog.set_property(prop, val)

        dialog.connect("response", self.destroy)
        dialog.show_all()

    def destroy(self, dialog, response):
        dialog.destroy()
        About.__instance = None

