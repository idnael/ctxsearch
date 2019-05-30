# -*- coding: utf-8 -*-

import subprocess

from .actions import ModuleBase

MODULE_NAME = "CommandModule"

class CommandModule(ModuleBase):

    def accept_action(self, ctx, action):
        return "command" in action

    def execute_action(self, ctx, action):
        print("EXECUTE",action["command"])

        # if the command does not exists, this will not raise an exception, because it is a shell subprocess

        if "command_input" in action and action["command_input"]:
            #print "ACTI?",action["command_input"], type(action["command_input"])

            proc = subprocess.Popen(action["command"], shell=True, stdin=subprocess.PIPE)
            proc.stdin.write(ctx["text"] + "\n")
            proc.stdin.close()

        else:
            proc = subprocess.Popen(action["command"], shell=True)
            
