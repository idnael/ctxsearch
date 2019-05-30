# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

import os, time, re, subprocess, sys, signal, psutil
from gettext import gettext as _

import etc

def count_words(str):
    return len(etc.split_words(str))

# LANGUAGE DETECTION
# see https://pypi.python.org/pypi/langid

language_support = False

# Gives an exception if library not present
def init_languages():
    # This takes some time to load:
    global language_support

    # Imported modules are just variables - names binded to some values. So all you need is to import them and make them global with global keyword.
    global langid
    import langid
    
    # I have to do that for the library to initialize, which takes some time
    langid.classify("test")

    language_support = True
    print "Language identification support loaded"

def has_language_support():
    global language_support
    return language_support

DEFAULT_LANGID_CONFIDENCY = 0.999  ## TODO config!
def detect_language(text):
    global language_support

    detected_language = None

    if language_support:
        # I found that lang id works better with small texts if I repeat it!
        str = ""
        for i in range(0,4):
            str = str + " " + text

        if etc.property("languages"):
            langid.langid.set_languages(etc.split_words(etc.property("languages")))

        lang,prob = langid.classify(str)
        # only uses the detected languge if the probability is high.
        if prob >= etc.property("lang_confidency", DEFAULT_LANGID_CONFIDENCY):
            detected_language = lang

    return detected_language

# WINDOWS AND PROCESSES

def get_active_window():
    process = subprocess.Popen(["xdotool","getactivewindow"], stdout=subprocess.PIPE)
    wid = int(process.stdout.readline().strip())
    return wid

def get_window_pid_and_title(wid):
    process = subprocess.Popen(["xdotool","getwindowname",str(wid),"getwindowpid", str(wid)], stdout=subprocess.PIPE)
    title = process.stdout.readline().strip()
    pid = int(process.stdout.readline().strip())
    return pid,title

def get_program_name(pid):
    proc = psutil.Process(pid)
    name = proc.name

    i = name.find(" ")
    if i != -1: name = name[0 : i]

    i = name.rfind("/")
    if i != -1: name = name[i+1 :]

    return name
        
   
########

class Context:
    def __init__(self, text, x=0, y=0):
        self.text = text
        self.x = x
        self.y = y

        self.time = time.time()

        # See which window is active now, which should be where the clipboard selection was made
        # TODO xwindows.get_active_window
        self.wid = get_active_window()

    def complete(self):
        # get the program name
        self.pid, self.window_title = get_window_pid_and_title(self.wid)

        self.program_name = get_program_name(self.pid)

        if etc.DEBUG: print "Program is", self.program_name

        # The language id of the text, or None if can't detect
        self.detected_language = detect_language(self.text)
        if etc.DEBUG: print "Language:",self.detected_language

        self.word_count = count_words(self.text)

