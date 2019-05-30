# -*- coding: utf-8 -*-

import subprocess, os, psutil

from .actions import ModuleBase

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
    name = proc.name()

    i = name.find(" ")
    if i != -1: name = name[0 : i]

    i = name.rfind("/")
    if i != -1: name = name[i+1 :]

    return name

MODULE_NAME = "GrabInfoModule"

class GrabInfoModule(ModuleBase):
    def prepare_context(self, ctx):
        # TODO e o x y (e time) ????


        # See which window is active now, which should be where the clipboard selection was made
        # TODO xwindows.get_active_window
        ctx["wid"] = get_active_window()

        # get the program name
        ctx["pid"], ctx["window_title"] = get_window_pid_and_title(ctx["wid"])

        ctx["program_name"] = get_program_name(ctx["pid"])

        #if etc.DEBUG: print "Program is", self.program_name
