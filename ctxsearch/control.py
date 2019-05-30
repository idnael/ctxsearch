#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

# 0.5

from gi.repository import Gtk, Gdk,GObject
import cairo
import os, time, re, sys, signal, math

from .keydetector import KeyDetector
#import etc
from .actions import ActionsManager
#from etc import _

class Control:
    # The time the floating shows, in seconds
    DEFAULT_HIDE_TIME = 3

    # The distance in pixels the mouse can move away from the floating icon, until it disappears.
    # TODO should be in inchs? and should be configurable...
    DEFAULT_HIDE_DISTANCE = 400

    # interval where I check mouse events etc. In miliseconds
    TIMER_INTERVAL = 50

    # Percentage of time after which floating will start to became transparent until disapear.
    # A value of 1 means only to hide imediatly when time is finished
    HIDE_FACTOR = 0.9

    # Minimum time the floating window shows, even if there is a mouse event or other event.
    MINIMUM_TIME = 0.2

    # after a selection is detected, we wait this time before showing the floating window.
    # This is because some programs create continuos selection events while the user
    # is dragging the mouse. and it is better if the floating window only appear in the end.
    DEFAULT_SELECTION_DELAY = 0.150

    # When a text is selected, the floating window doesn't shows
    # exactly in the mouse position but at this vertical distance.
    # This is not to cover the text that is in the mouse position, and make the application least intrusive, if the user has not made ​​a selection without intention to perform an action.

    DEFAULT_SELECTION_DISTANCE = 20

    def __init__(self, cfg):
        self.cfg = cfg
        self.check_config() ##aquui????

        # the borderless always on top transparent window that shows an image near the place where
        # the mouse was when the selection was made.
        self.floating = Gtk.Window(Gtk.WindowType.POPUP)

        self.floating.set_border_width(0)
        # Gdk.Screen object representation of the screen on which windows can be displayed and on which the pointer moves:
        screen = self.floating.get_screen()

        # Make the window transparent. 
        # gets a Gdk.Visual object to use for creating windows with an alpha channel.
        visual = screen.get_rgba_visual() 
        if visual != None and screen.is_composited():
            self.floating.set_visual(visual)
            self.floating.set_app_paintable(True)
            #This signal is emitted when a widget is supposed to render itself
            self.floating.connect("draw", self.area_draw) 
        else:
            print("Transparency not supported.")
            # O icon que uso é quase quadrado por isso pouco se nota se não ficar transparente.
            # Podia usar icons diferentes no caso de a transparencia nao ser suportada!
            
        eventbox = Gtk.EventBox()
        # This is to detect mouse clicks:
        eventbox.connect("button-press-event", self.clicked)
        self.floating.add(eventbox)

        img = Gtk.Image()
        img.set_from_file(os.path.join(self.cfg.data_dir,"floating.png"))
        eventbox.add(img)
        eventbox.show_all()
        
        # now launch a keydetector, to detect if the user presses a key
        # or do a mouse click. That should make the floating window
        # disappear.

        # This prints some annoying messages... <class 'Xlib.protocol.request.QueryExtension'>
        self.keydetector =KeyDetector()

        # start detecting clipboard events!
        # The primary selection is used everytime the user selects text!
        clip = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        clip.connect('owner-change', self.on_clipboard_owner_change)

        # this is where we put information about the event, which is used to produce the actions menu
        # this will also check if the xdotool is present, and exit if not
        self.ctx = {}
        
        #TODO testar etc.message_dialog(_("Need xdotool to run."))         sys.exit(1)

        self.timer = None

        self.manager = ActionsManager(self.cfg)

    # This is necessay for the window transparency
    # Last argument cr is a cairo.Context object
    def area_draw(self, widget, cr):
        cr.set_source_rgba(.2, .2, .2, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE) # replace destination layer
        cr.paint() #A drawing operator that paints the current source everywhere within the current clip region
        cr.set_operator(cairo.OPERATOR_OVER) # destination on top of source

    def mouse_xy(self):
        hello, x, y, mods = self.floating.get_screen().get_root_window().get_pointer()
        return x,y

    def on_clipboard_owner_change(self, clipboard, event):
        text = clipboard.wait_for_text() or ""

        #if self.cfg.DEBUG: print "Clipboard change" #, "###" + etc.reduce_text(text,40) + "###"

        # Ignore clipboard selections made by keyboard
        if text and self.keydetector.check_event() != KeyDetector.KEYBOARD:
            mouse_x, mouse_y = self.mouse_xy()

            # reads again the configuration file so it can be changed without restarting the program!
            self.check_config()

            # time aquui?
            self.ctx = {"text":text, "x":mouse_x, "y":mouse_y, "time": time.time()}

            # I have to define as a object variable, or it will loose scope and the menus will close after this method returns!

            # 201905 isto vai adicionar outros items ao ctx
            self.menu = self.manager.menu(self.ctx)

            if not self.menu:
                # empty menu, don't show
                return

            if not self.timer:
                # start the timer that will be use to show and hide the floating
                self.timer = GObject.timeout_add(self.TIMER_INTERVAL, self.timer_func)

            # There are some applications that produce several clipboard events while
            # the user is grabbing the mouse to make the selection.
            # So we wait some time before showing the floating icon.
            # The show_me method will be called from the timer...
            self.delayed_to_show = True

        else:
            if self.cfg.DEBUG: print("Ignored")

    def timer_func(self):
        if self.delayed_to_show:
            if time.time() > self.ctx["time"] + self.SELECTION_DELAY:
                self.show_floating()

        else:
            mouse_x, mouse_y = self.mouse_xy()

            distance = math.sqrt((mouse_x - self.floating_x) * (mouse_x - self.floating_x) + (mouse_y - self.floating_y) * (mouse_y - self.floating_y))

            # combine the elapsed time and the distance in one factor
            k= distance / self.HIDE_DISTANCE + (time.time() - self.ctx["time"]) / self.HIDE_TIME

            if k > 1:
                self.hide_floating("time or distance")

            elif k > self.HIDE_FACTOR:
                self.floating.set_opacity( (1 - k ) / (1 - self.HIDE_FACTOR))

            else:
                self.floating.set_opacity(1)

        last_event = self.keydetector.check_event()

        if last_event and time.time() - self.ctx["time"] > self.MINIMUM_TIME:
            self.hide_floating((last_event == KeyDetector.MOUSE) and "mouse" or "keyboard")
            
        return True

    def show_floating(self):
        #if self.cfg.DEBUG: print "Show"

        self.delayed_to_show = False
        w, h = self.floating.get_size()

        if self.ctx["y"] > self.keydetector.mouse_down_y:
            delta_y = self.SELECTION_DISTANCE
        else:
            delta_y = - self.SELECTION_DISTANCE

        # the floating position:
        self.floating_x = self.ctx["x"] - w /2
        self.floating_y = self.ctx["y"] + delta_y - h / 2

        self.floating.move(self.floating_x, self.floating_y)
        self.floating.set_opacity(1)

        self.floating.show()
        
    def hide_floating(self, comment):
        self.floating.hide()
        if self.cfg.DEBUG:
            print("Hide by"+comment)
            print("")

        if self.timer:
            # stop it
            GObject.source_remove(self.timer) 
            self.timer = None

    def clicked(self, widget, event):
        #if self.cfg.DEBUG: print "Clicked"

        # nao é usado... self.ctx.event = event #???

        self.menu.show_all()

        self.menu.popup(None, None, None, None, event.button, event.get_time())

        return True

    def inic_prop(self, name):
        uname = name.upper()
        value = self.cfg.property(name, getattr(self, "DEFAULT_"+uname))
        setattr(self, uname, value)

    def check_config(self):
        try:
            if self.cfg.check():
                if self.cfg.DEBUG: print("Config changed")
                
            # exexcutao sempre... pro causa da primeira vez...
            self.inic_prop("hide_time")
            self.inic_prop("hide_distance")
            self.inic_prop("selection_delay")
            self.inic_prop("selection_distance")

        except:
            # An error in the configuration file...
            # displays a error message, but continues!
            etc.message_dialog(sys.exc_info()[1])

