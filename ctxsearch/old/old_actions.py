# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

import io, urllib, subprocess, os, time, re, sys
from gettext import gettext as _

from gi.repository import Gtk, Gdk,GObject
from gi.repository.GdkPixbuf import Pixbuf

import etc, web

class ActionsManager:
    # An action that is a shell command that receives the text in the standard input
    # The process continues to run in the background
    # TODO: could also receive text as argument?
    # TODO: run the process in a thread, so I can open a warning window if it exits with error,
    # and display an option in the actions menu to interrupt a long running process.
    def execute_command(self, ctx, action):
        # if the command does not exists, this will not raise an exception, because it is a shell subprocess
        proc = subprocess.Popen(action["command"], shell=True, stdin=subprocess.PIPE)
        proc.stdin.write(ctx.text + "\n")
        proc.stdin.close()
 

    # A web action
    def execute_webpage(self, ctx, action):
        # In the url given in the config file, replaces the special text "XYZ" by the url-encoded text!
        replace_mark = "XYZ" # TODO: etc.DEFAULT_REPLACE_MARK...
        if "location.token" in action:
            replace_mark = action["location.token"]

        if  "location.quote" in action:
            quote = action["location.quote"]
        else:
            quote = True

        if quote:
            # for instance: https://www.google.pt/search?q=XYZ
            ctx.url = action["location"].replace(replace_mark, urllib.quote(ctx.text))
        else:
            # useful for "open location" action
            ctx.url = ctx.text

        if etc.DEBUG: 
            #print "Opening", etc.reduce_text(ctx.url, 50)
            print "Opening", ctx.url

        # NOW OPEN THE URL
        
        DEFAULT_TARGET = "internal"
        target = "target" in action and action["target"] or DEFAULT_TARGET

        if target == "detect":
            # If the property is not defined, will use internal!
            command  = etc.property("detected." + ctx.program_name)

        elif target == "browser":
            command = etc.property("browser", "xdg-open")

        elif target == "internal":
            command = None
            
        else:
            print "Target should be detect, browser or internal"
            command = None

        if command:
            etc.open_url(command, ctx.url)

        else:
            if self.win == None:
                # Creates the window with a webkit instance
                self.win = web.WebkitWindow(self)
            self.win.open(action, ctx)

