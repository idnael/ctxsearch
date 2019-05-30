# -*- coding: utf-8 -*-
from gi.repository import Gtk, Gdk,GObject
from gi.repository.GdkPixbuf import Pixbuf
import copy, os

class ModuleBase:
    def init(self, manager):
        self.manager = manager
        self.cfg = manager.cfg

    def filter_actions(self, ctx, actions):
        return actions

    def prepare_context(self, ctx):
        pass

    def accept_action(self, ctx, action):
        return None

    def execute_action(self, ctx, action):
        pass

class ActionsManager:
    # The icons that shows in the menu!
    # That should not be fixed but based on the screen resolution... how?
    MENU_ICON_SIZE = 20

    def __init__(self, cfg):
        self.cfg = cfg

        self.modules = []

        module_names = ["modgrabinfo", "modlanguage", "modsyntax", "modweb",  "modcommand"] ## "modfiles",
        for modname in module_names:
            # no Python3 leva parentesis!

            exec("from . import "+modname)
            modclass = eval(modname+".MODULE_NAME")
            mod = eval(modname + "." + modclass +"()")
            mod.init(self)

            self.modules.append(mod)

    def _filter_accepted_actions(self, ctx, actions):
        result = []
        for action in actions:
            if "submenu" in action:
                action["submenu"] = self._filter_accepted_actions(ctx, action["submenu"])
                if action["submenu"]: # not empty
                    result.append(action)

            elif "separator" in action:
                result.append(action)

            else:
                #print("TEST?",action)
                for mod in self.modules:
                    #print("MOD...",mod)
                    if mod.accept_action(ctx, action):
                        # nao é um primitivo... devo fazer isto?
                        #self.current_modules[action] = mod
                        action["module"] = mod
                        result.append(action)

                        #print("YEP", mod)

                        break
        return result

    # menu others: os que nao foram validados... mas para isso o accept_action devia poder retornar True, False ou Maybe??
    # menu "more" - quando sao muitas opcoes... suportar "priority" nas actions...
    def menu(self, ctx):
        #print self.cfg.config

        for mod in self.modules:
            mod.prepare_context(ctx)

        # I made a deep copy so I can change the actions strucutre without affecting the actions stored in the config
        actions = copy.deepcopy(self.cfg.property("actions"))

        for mod in self.modules:
            actions = mod.filter_actions(ctx, actions)

        actions = self._filter_accepted_actions(ctx, actions)

        print("CTX", ctx)
        print("ACTIONS", actions)

        if actions:
            return self._actions_to_menu(ctx, actions)
        else:
            #print "Nothing to do..."
            return None

    def _actions_to_menu(self, ctx, actions):
        menu = Gtk.Menu()

        for action in actions:
            if "separator" in action:
                menu.append(Gtk.SeparatorMenuItem())
                if "title" in action:
                    menuitem = Gtk.MenuItem(action["title"])
                    menuitem.set_sensitive(False)
                    menu.append(menuitem)

            elif "submenu" in action:
                submenu = self._actions_to_menu(ctx, action["submenu"])
                menuitem = Gtk.MenuItem(action["title"])
                menuitem.set_submenu(submenu)
                menu.append(menuitem)

            else:
                menu.append(self._action_to_menuitem(ctx, action))
        return menu

    def _action_to_menuitem(self, ctx, action):
        menuitem = Gtk.ImageMenuItem(action["title"])

        # the icon could have been read from the config, or set in one of the modules
        if "icon" in action: # and os.path.exists(action["icon"]):

            # nota: pode ser absoluto já e nesse caso o cfgdir é ignorado
            iconfile = os.path.join(self.cfg.cfgdir, "icons", action["icon"])

            if os.path.exists(iconfile):
                pixbuf = Pixbuf.new_from_file_at_size(iconfile, self.MENU_ICON_SIZE, self.MENU_ICON_SIZE)
                img = Gtk.Image()
                img.set_from_pixbuf(pixbuf)

                menuitem.set_image(img)

                # if I don't call this, the image will only appear if gnome is configured to show images in menus!
                # But I reallly want the images!!!
                menuitem.set_always_show_image(True)

        menuitem.connect('activate', self.on_menu_action, ctx, action)
        return menuitem

    # executes the action!
    def on_menu_action(self, menuitem, ctx, action):
        print(action)
        mod = action["module"]
        mod.execute_action(ctx, action)

if __name__ == "__main__":
    import sys
    #import yaml
    #f =open(sys.argv[1], "r")
    #cfg = yaml.load(f)
    #f.close()
    from config import Config
    cfg = Config(sys.argv[1])
    #print cfg

    man = ActionsManager(cfg)

    ctx = {"text": "I found that lang id works better with small texts", "x":10,"y":100}

    man.menu(ctx)

