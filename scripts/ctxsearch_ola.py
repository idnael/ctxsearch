#!/usr/bin/env python3

# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnaed@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.


import sys, os, subprocess
from gettext import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk,GObject

import ctxsearch.main as main
import ctxsearch.etc as etc

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        try:
            global html2text
            import html2text
        except:
            print("Library html2text not available")
            sys.exit(1)

        import codecs
        f = codecs.open(etc.HELP_FILE, "r", "utf-8")
        html = f.read()
        f.close()

        text = html2text.html2text(html)

        import tempfile
        txtfile = tempfile.mkstemp(".txt","_ctxsearch-help")[1]
        f = codecs.open(txtfile, "w", "utf-8")
        f.write(text)
        f.close()

        pager = os.getenv("PAGER") or "less"
        proc = subprocess.Popen([pager, txtfile])
        proc.wait()
        sys.exit(0)

    # If you are only interested in Ctrl-c finishing your application and you don't
    # need special cleanup handlers, the following will perhaps work for you:
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    GObject.set_application_name('Context Search')
    GObject.set_prgname('ctxsearch')

    main.Main()

    Gtk.main()
