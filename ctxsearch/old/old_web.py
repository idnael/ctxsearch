#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

from gi.repository import Gtk, Gdk,GObject, WebKit
import io, urllib, subprocess, os, time, re

from gettext import gettext as _

import etc, about

class WebkitWindow(Gtk.Window):
    # After this time, I will try to download again a favicon from a site
    FAVICON_EXPIRE_DAYS = 14

    def __init__(self, actions):
        Gtk.Window.__init__(self)

        self.actions = actions

        # uses the same icon as the floating window
        self.set_icon_from_file(os.path.join(etc.DATA_DIR,"app_icon.png"))

        self.webview = WebKit.WebView()
        self.webview.connect("key-press-event",self.webpage_key_press)
        self.webview.connect_after("populate-popup", self.webpage_populate_popup)

        self.connect("delete-event", self.webpage_window_delete)

        sw = Gtk.ScrolledWindow()
        sw.add(self.webview)
        self.add(sw)



    def webpage_window_delete(self, win, event):
        # just hide the window:
        self.hide()

        # this will prevent the default action, which is to destroy the window
        return True

    def webpage_key_press(self,widget, event, data=None):
        if event.hardware_keycode==9:
            # ESCAPE key closes the window!
            self.hide()

    # Adds my menu items to the webkit standard context menu!
    def webpage_populate_popup(self,view, menu):
        # Based on
        # http://pywebkitgtk.googlecode.com/svn-history/r159/trunk/demos/browser.py

        menu.append(Gtk.SeparatorMenuItem())
        menuitem = Gtk.MenuItem(_("Open in default browser"))
        menuitem.connect('activate', self.on_webpage_open_default_browser)
        menu.append(menuitem)

        menuitem = Gtk.MenuItem(_("Edit CtxSearch actions"))
        menuitem.connect('activate', self.on_edit_actions)
        menu.append(menuitem)

        menuitem = Gtk.MenuItem(_("About CtxSearch"))
        menuitem.connect('activate', self.on_about)
        menu.append(menuitem)

        menuitem = Gtk.MenuItem(_("Manual"))
        menuitem.connect('activate', self.on_help)
        menu.append(menuitem)

        # Add the itens from the actions menu!
        actions_menu = self.actions.actions_menu(self.ctx)
        menuitem = Gtk.MenuItem(_("Other actions"))
        menuitem.set_submenu(actions_menu)
        menu.append(menuitem)
        
        menu.show_all()
        return False

    def on_webpage_open_default_browser(self, menuitem):
        url = self.webview.get_property("uri")
        # Opens the standard browser!

        # TODO: devia fazer aqui o mesmo que faço no actions...

        command = etc.property("browser", "xdg-open")
        etc.open_url(command, url)

        self.hide()

    def on_edit_actions(self, menuitem):
        subprocess.Popen(["xdg-open", etc.CONFIG_FILE])

    def on_about(self, menuitem):
        about.About()

    def on_help(self, menuitem):

        # TODO: podia ter uma versao html da ajuda!

        import urlparse, urllib

        url = urlparse.urljoin('file:', urllib.pathname2url(os.path.abspath(etc.HELP_FILE)))
        self.webview.open(url)

