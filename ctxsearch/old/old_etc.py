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

VERSION = "0.5"

CONFIG_DIR = os.path.join(os.getenv("HOME"), ".ctxsearch")

CONFIG_FILE = os.path.join(CONFIG_DIR, "actions.yaml")

# the data dir is based on the python module dir
#DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PY_DIR = os.path.dirname(__file__)
if PY_DIR.startswith("/usr/local/lib/"):
    DATA_DIR = "/usr/local/share/ctxsearch"
elif PY_DIR.startswith("/usr/lib/"):
    DATA_DIR = "/usr/share/ctxsearch"
else:
    DATA_DIR = os.path.join(PY_DIR, "../data")
    if not os.path.exists(DATA_DIR):
        raise "Can't find data dir"

HELP_FILE = os.path.join(DATA_DIR, "ctxsearch-help.html")

DEBUG = False

# config information read from yaml CONFIG_FILE!
config = {}
config_time = None

default_config = {}

# return true if config was changed on config file
def check_config():
    # if there is no config dir, creates a default configuration
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        os.makedirs(os.path.join(CONFIG_DIR, "favicons"))

    if not os.path.exists(CONFIG_FILE):
        shutil.copy(os.path.join(DATA_DIR, "default_actions.yaml"), CONFIG_FILE)

    global config_time
    global config
    global DEBUG

    try:
        if config_time and config_time == os.path.getmtime(CONFIG_FILE):
            return False

        # set the config time event if there was an error in the config file, 
        # so I don't need to read again
        config_time = os.path.getmtime(CONFIG_FILE)

        f =open(CONFIG_FILE, "r")
        config = yaml.load(f)
        f.close()

    except Exception as ex:
        print ex
        raise Exception(_("Error in config file %s") % CONFIG_FILE)

    DEBUG = "debug" in config and config["debug"]
    return True

# gets a property value
def property(name, default=None):
    global config

    if name in config:
        return config[name]
    else:
        return default






import re
word_separator_regexp = re.compile(r'[ ,.;!?]+')

def split_words(str):
    global word_separator_regexp
    return word_separator_regexp.split(str.strip())

def message_dialog(message):
    dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.INFO,
                               Gtk.ButtonsType.OK, message)
    dialog.run()
    dialog.destroy()


def reduce_text(txt, max_len):
    txt = txt.replace("\n","\\n")
    if len(txt) <= max_len:
        return txt
    else:
        l = max_len / 2
        return txt[0:l] + " ... " + txt[-l:]

    
def open_url(command, url):
    # open with external command
    # TODO: could be other thing other than the string "URL"
    if command.find("URL") != -1:
        command = command.replace("URL", url)
    else:
        import pipes
        command = command + " " + pipes.quote(url)

    if DEBUG: print "Command", command
    subprocess.Popen(command, shell=True)
