#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Daniel Carvalho <idnael@pegada.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

import time, re

import pyxhook

class KeyDetector:
    MOUSE = 1
    KEYBOARD = 2

#TODO reagir ao mouse wheel tambem
    def event_mouse_down(self, event):
        self.last_event = KeyDetector.MOUSE
        self.mouse_down_y = event.Position[1]

    def event_key_down(self, event):
        self.last_event = KeyDetector.KEYBOARD

    def __init__(self):
        self.hm = pyxhook.HookManager()
        self.hm.HookKeyboard()
        self.hm.HookMouse()

        self.last_event_time = None
        self.last_event_type = None
        
        self.hm.KeyDown = self.event_key_down
        self.hm.MouseAllButtonsDown = self.event_mouse_down
        # TODO: should also detect mouse wheel events. how?

        self.hm.start()

    def check_event(self):
        res = self.last_event
        self.last_event = None
        return res

    def destroy(self):
        self.hm.cancel()
