# -*- coding: utf-8 -*-

import io, urllib, subprocess, os, time, re, pipes
import unidecode


from .actions import ModuleBase
from .webwindow import WebWindow

MODULE_NAME = "WebModule"

# como tratar os icons?
# tem que receber o ActiosManager!

# TODO ver: target...

from urllib.request import urlopen
import favicon

# After this time, I will try to download again a favicon from a site
FAVICON_EXPIRE_DAYS = 14

# melhor png pq suporta transparencia
ICON_EXTENSION = ".png"

# Converts a action title to an image name, removing the accents and special characters
def get_icon_filename(title):
    name = unidecode.unidecode(title)

    name = name.replace("/", " ")
    name = name + ICON_EXTENSION
    return name

# faz download do faviicon da pagina indicada e grava em file
# converte formato imagem se necesario
def download_favicon(url, file):
    icons = favicon.get(url)
    if len(icons) ==0:
        # # save the favicon, even if empty
        # # If empty, that will prevent from trying to download over again
        with open(file, "wb"):
            pass

    icon = icons[0]

    # por exemplo
    # Icon(url='https://static.publico.pt/files/site/assets/img/ico/apple-touch-icon.png?v=Km29lWbk4K', width=180, height=180, format='png')

    # supoonho que format é a extensao, sem o "."

    # print("download_favicon",url,file)
    # print("icon", icon)
    # print("fav url", icon.url)
    # print("format", icon.format)

    data = urlopen(icon.url).read()

    if "." + icon.format == ICON_EXTENSION:
        # ja esta na formato certa
        with open(file, "wb") as fd:
            fd.write(data)

    else:
        import tempfile
        # cria ficheiro temporaria com a extensao do icon para fazer download
        tmp =tempfile.mkstemp(suffix= "."+icon.format)[1]
        with open(tmp, "wb") as fd:
            fd.write(data)

        # o "[0]" é pq alguns .ico tem varias imagnes... e entao o convert iria adicionar os sufixos -1, -2 etc...
        subprocess.Popen(["convert", tmp+"[0]", file]).wait()

class WebModule(ModuleBase):

    def init(self, manager):
        ModuleBase.init(self, manager)
        
        self.win = None

    def accept_action(self, ctx, action):
        # vou aceitar os actions que tem o elemento "web", que é o url
        # no ficheiro de configuracao, serao usados urls do tipo
        # http://pt.wikipedia.org/wiki/${text__quote}
        # Mas O modsyntax já terá feito as substituicoes portanto eu vou reeber o url final
        if "web" in action:
            if not "icon" in action:
                icon_filename = get_icon_filename(action["title"])
                icon_file = os.path.join(self.cfg.cfgdir, "icons", icon_filename)

                # se existe o icon, usa-o. Se nao, fica vazio. Só vou fazer download dos icons no
                # momento em que a pagina é aberta
                if os.path.exists(icon_file) and os.path.getsize(icon_file) != 0:
                    action["icon"] = icon_filename
            return True
        else:
            return None

    def execute_action(self, ctx, action):
        url = action["web"]
        print(url, type(url))
            
        DEFAULT_TARGET = "internal"
        target = "target" in action and action["target"] or DEFAULT_TARGET

        if target == "detect":
            # If the property is not defined, will use internal!
            command  = self.cfg.property("detected." + ctx.program_name)

        elif target == "browser":
            command = self.cfg.property("browser", "xdg-open")

        elif target == "internal":
            command = None
            
        else:
            # TODO erro... como mostrar??
            print("Target should be detect, browser or internal")
            command = None

        if command:
            command = command + " " + pipes.quote(url)

            #if DEBUG: print "Command", command
            subprocess.Popen(command, shell=True)

        else:
            if self.win == None:
                # Creates the window with a webkit instance
                self.win = WebWindow(self.manager)

            # abro a pagina no webview
            self.win.open(ctx, action)

            # Agora faço download do icon, se ainda nao tenho!

            # Webkit should implement a method get_favicon.
            # since i can't access it, have to download directtly
            icon_name = get_icon_filename(action["title"])
            icon_file = os.path.join(self.cfg.cfgdir, "icons", icon_name)
            if not os.path.exists(icon_file) or time.time() - os.path.getctime(icon_file) > FAVICON_EXPIRE_DAYS * 24 * 3600:

                # devia fazer isto em background???
                download_favicon(action["web"], icon_file)
