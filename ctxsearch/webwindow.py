# -*- coding: utf-8 -*-

import pipes, os, time, subprocess

import gi
gi.require_version('WebKit2', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk,GObject, WebKit2

# Uma janela com um webview. É preservada entre chamadas. Quando nao é usada, esconde-se. Assim é mais rapido (?)
class WebWindow(Gtk.Window):
    def __init__(self, manager):
        Gtk.Window.__init__(self)

        self.manager = manager
        self.cfg = manager.cfg

        # uses the same icon as the floating window
        self.set_icon_from_file(os.path.join(self.cfg.data_dir,"app_icon.png"))

        # https://lazka.github.io/pgi-docs/WebKit2-4.0/classes/WebView.html
        self.webview = WebKit2.WebView()
        self.webview.connect("key-press-event",self.webpage_key_press)
        self.webview.connect("context-menu", self.webpage_populate_popup)

        self.connect("delete-event", self.webpage_window_delete)

        sw = Gtk.ScrolledWindow()
        sw.add(self.webview)
        self.add(sw)

    def open(self, ctx, action):
        #print "OPEN URL",action["web"]
        self.ctx = ctx
        self.url = action["web"]

        self.set_title(action["title"])

        # the window size could be specified in the action
        w = "width" in action and action["width"] or self.cfg.property("width", 400)
        h = "height" in action and action["height"] or self.cfg.property("height", 400)

        self.resize(w, h)

        # TODO 201905 agora uso WebView2! talvez tenha funcioanlidades que podem ser uteis!!!

        # clears the previous page while loading the new one
        ###self.webview.load_string("ola", "text/html", "utf-8", "about:blank")
        ###self.webview.clear()

        # problemas com isto?
        #self.webview.execute_script("document.open()")


        # self.webview.connect("notify::favicon", self.favicon) NUNCA é chamado

        self.webview.load_uri(self.url)

        # if I hide and then show the window, it will be in the current desktop...!
        self.hide()
        self.show_all()

        # show the window where the mouse was when the text selection was made
        x = ctx["x"]
        y = ctx["y"]
        screen_w = self.get_screen().get_width()
        screen_h = self.get_screen().get_height()

        #guaranted that the window is inside the screen:
        if x + w > screen_w:
            x = screen_w - w
        if y + h > screen_h:
            y = screen_h - h
        self.move(x, y)

        # raise the window, if it was covered
        self.present()

    def favicon(self, a,b):
        print("FAVICON",a,b)

    def webpage_window_delete(self, win, event):
        # just hide the window:
        self.hide()

        # this will prevent the default action, which is to destroy the window
        return True

    def webpage_key_press(self,widget, event, data=None):
        #print("webpage_key_press")
        #print(self.webview.get_favicon()) Retorna SEMPRE NONE

        # 201905 como nao consegui colocar a funcionar o contetxt menu, defini que shift + ESC fecha o webview e abre o url no default browser

        if event.hardware_keycode==9:
            # ESCAPE key closes the window!

            if event.state & Gdk.ModifierType.SHIFT_MASK:
                print("SHIFT")
                self.on_webpage_open_default_browser()

            self.hide()

    # Adds my menu items to the webkit standard context menu!
    def webpage_populate_popup(self,view, menu, *args):
        print("webpage_populate_popup")

        # com webkit agora é assim... nao funciona...
        # https://lazka.github.io/pgi-docs/WebKit2-4.0/classes/ContextMenu.html
        # https://lazka.github.io/pgi-docs/WebKit2-4.0/classes/ContextMenuItem.html

        menu.append(WebKit2.ContextMenuItem.new_separator())
        menu.append(WebKit2.ContextMenuItem.new_separator())

        # Based on
        # http://pywebkitgtk.googlecode.com/svn-history/r159/trunk/demos/browser.py

        # menuitem = Gtk.MenuItem("Open in default browser")
        # menuitem.connect('activate', self.on_webpage_open_default_browser)
        # menu.append(menuitem)
        #
        # menuitem = Gtk.MenuItem("Edit CtxSearch actions")
        # menuitem.connect('activate', self.on_edit_actions)
        # menu.append(menuitem)
        #
        # menuitem = Gtk.MenuItem("About CtxSearch")
        # menuitem.connect('activate', self.on_about)
        # menu.append(menuitem)
        #
        # menuitem = Gtk.MenuItem("Manual")
        # menuitem.connect('activate', self.on_help)
        # menu.append(menuitem)
        #
        # # Add the itens from the actions menu!
        # actions_menu = self.manager.menu(self.ctx)
        # menuitem = Gtk.MenuItem("Other actions")
        # menuitem.set_submenu(actions_menu)
        # menu.append(menuitem)
        #
        # menu.show_all()
        return False

    def on_webpage_open_default_browser(self, *args):
        #url = self.webview.get_property("uri")
        # Opens the standard browser!

        # TODO: devia fazer aqui o mesmo que faço no actions...

        # isto está repetido no modweb.py...
        command = self.cfg.property("browser", "xdg-open") + " " + pipes.quote(self.url)
        subprocess.Popen(command, shell=True)

        self.hide()

    def on_edit_actions(self, menuitem):
        # mais um que devia estar noutro sitio...
        subprocess.Popen(["xdg-open", self.cfg.cfgfile])

    def on_about(self, menuitem):
        import about
        about.About()

    def on_help(self, menuitem):

        # TODO: podia ter uma versao html da ajuda!

        import urlparse, urllib

        url = urlparse.urljoin('file:', urllib.pathname2url(os.path.abspath(self.cfg.help_file)))
        self.webview.open(url)
