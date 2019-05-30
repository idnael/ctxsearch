# -*- coding: utf-8 -*-

import io, urllib, subprocess, os, time, re, sys, psutil

from .actions import ModuleBase
# como tratar os icons?
# tem que receber o ActiosManager!

MODULE_NAME = "FilesModule"


# TODO recobnhecer tambem "ls -l"


# TODO pode ter icons para copiar, apagar etc. E para abrir, usa os icons dos programas!



# nota: ficheiros nao podem ter espacos no inicvio ou fim!
def format_size(bytes):
    K = 1024
    if bytes < 10*K:
        return "" + str(bytes) + " B"
    elif bytes < 10*K*K:
        return "" + str(bytes/K) + " KB"
    else:
        return "" + str(bytes/K/K) + " MB"

def path_replace_user(path):
    home = os.getenv("HOME")
    if path == home:
        return "~"
    elif path.startswith(home+"/"):
        return "~" + path[len(home) :]
    else:
        return path

import lsparser
import filetools

def getprocesscwd(pid):
    p = subprocess.Popen(["pwdx", str(pid)], stdout=subprocess.PIPE)
    p.wait()
    x = p.stdout.readline()
    # TODO melhorar
    return x[ x.find(" ") +1 : ].strip()

class FilesModule(ModuleBase):

    def init(self, manager):
        ModuleBase.init(self, manager)

    RE_TERMINAL = re.compile("^term|x-term$")
    RE_SHELL = re.compile("^bash$")

    # E se for uma subshell?
    # ou um ssh? navegar na hierarquia de processos...?

    # 1. Knowing the pid of the process where the selecion was made, detects if it is a terminal.
    # 2. Then find the pid os the shell inside that terminal, and it's current working directory.
    # 3. Uses the directory to detect the files included in the selection.
    # 4. If all the text matches, then it considers a sucess.
    # 5. If it is a multi terminal, can have more than one shell inside. In that case, only proceeds if the match was sucesseful in just one shell.
    def prepare_context(self, ctx):
        if not self.RE_TERMINAL.match(ctx["program_name"]):
            #print "Not terminal"
            return False

        # TODO testar program_name -regexp
        #print ctx["pid"]
        # e se forem dois bashe no mesmo cwd? nao precisa testar... lista possibles_cwd


        processes_basedirs = set()
        for proc in psutil.Process(ctx["pid"]).get_children(False):
            if self.RE_SHELL.match(proc.name):
                processes_basedirs.add(getprocesscwd(proc.pid))

        title_basedirs =set()

        home = os.getenv("HOME")
        if home:
            home = os.path.abspath(home)

        for dir in processes_basedirs:
            regex = r'(^|\s)(' +  re.escape(dir) + "|" + re.escape(path_replace_user(dir)) + r')($|\s)'
            if re.search(regex, ctx["window_title"]):
                title_basedirs.add(dir)

        possible_basedirs = title_basedirs or processes_basedirs
        print(possible_basedirs)
        basedir, files = lsparser.parse(ctx["text"], possible_basedirs)
        if basedir:
            # sucess!!!
            info = {}
            info["basedir"] = basedir
            info["list"] = files
            info["description"] = self.description(basedir, files)

            print("Encontrei")
            print("\n".join(files))

            info["defaultopen"] =filetools.get_default_application_for_files(files)
            info["openothers"] =filetools.get_applications_for_files(files)
            #print filetools.get_file_description(files[0])
            ctx["files"] = info

            return True

        else:
            return False

    def accept_action(self, ctx, action):
        return "openwith" in action

    def execute_action(self, ctx, action):
        print("EXEC",action["openwith"])
        print(action["openwith"].command)
        filetools.open_files_with_application(action["openwith"], ctx["files"]["list"])

    def description(self, basedir, files):
        count_dirs = 0
        total_size = 0
        for file in files:
            if os.path.isdir(file):
                count_dirs +=1
            elif os.path.isfile(file):
                total_size += os.path.getsize(file)
        count_files = len(files) - count_dirs
        
        res = ""
        if count_files:
            if count_files == 1 and count_dirs == 0:
                res += filetools.file_description(files[0])
            else:
                res += str(count_files) + " file" + (count_files!=1 and "s" or "")
            res += " (" + format_size(total_size) + ")"

        if count_dirs:
            if res: res += " and "
            res += str(count_dirs) + " directory" + (count_dirs!=1 and "s" or "")
        
        res += " in " + path_replace_user(basedir)
        print("RE",res)
        return(res)
        


if __name__ == "__main__":
    mod = FilesModule()
    #mod.basedir = "."
    text = """
about.py    control.py      main.py         modlanguage.py  pyxhook.py  unac.py
actions.py  __init__.py     modfiles.py     modsyntax.py    t2.py       web.py
config.py   keydetector.py  modgrabinfo.py  modweb.py       t_.py
"""
    #print(mod.parsefiles(text))

    #print mod.description("/home/daniel/comp", ["
