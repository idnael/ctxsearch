# -*- coding: utf-8 -*-

import yaml, os, shutil, sys

#f =open(sys.argv[1], "r")
#config = yaml.load(f)
#f.close()
#print config


import langid
print "ola",langid.langid.__class__.__name__

langid.langid.set_languages(["pt","es"])
print str(langid.langid)

#x = langid.langid.LanguageIdentifier()

#print langid.langid.classify("test")

