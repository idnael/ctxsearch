# -*- coding: utf-8 -*-

import re

#module_files = ["modgrabinfo","modlanguage", "modsyntax", "modweb"]
#for modfile in module_files:

modname = "modlanguage"


# http://stackoverflow.com/questions/301134/dynamic-module-import-in-python

exec "import "+modname
for modclass in eval(modname+".MODULE_NAMES"):
    mod = eval(modname + "." + modclass +"()")
    mod.init({})

    
