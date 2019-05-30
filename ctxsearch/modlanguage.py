# -*- coding: utf-8 -*-

import re
from .actions import ModuleBase

import langdetect

DEFAULT_LANGID_CONFIDENCY = 0.999  ## TODO config!

MODULE_NAME = "LanguageModule"

class LanguageModule(ModuleBase):

    def init(self, manager):
        ModuleBase.init(self, manager)


    def prepare_context(self, ctx):
        # if there is no support, put ""

        filter_langs = self.cfg.property("languages").split(",")

        try:
            results = langdetect.detect_langs(ctx["text"])

            if len(results) == 0:
                return

            # apenas as langs configuradas
            results = [result for result in results if result.lang in filter_langs]

            # a maior prob
            best = max(results, key=lambda result: result.prob)

            ctx["language"] = best.lang

        except:
            # da erro se nao tiver nada...
            pass

