import pygtk
pygtk.require ("2.0")

import os, sys, pyinotify
from sets import Set

# Notifies about files being deleted
class FileWatcher(pyinotify.ProcessEvent):
    def __init__(self, on_delete):
        pyinotify.ProcessEvent.__init__(self)

        self.on_delete = on_delete

        self.wm = pyinotify.WatchManager()

        self.notifier = pyinotify.ThreadedNotifier(self.wm, self)
        self.notifier.setDaemon(True)
        self.notifier.start() # Comienza el thread

        self.file2ids = {} # the key is the file and the value is a Set of ids
        self.id2file = {} # the key is the id and the value is the file

        self.file2wd = {} # the key is the file and the value is the watch descriptor

    def process_default(self, event):
        #print "evento", event,"..."
        # em certos casos recebo um IN_IGNORED mas nao o IN_DELETE...
        # por isso processo ambos!

        #if event.mask & pyinotify.IN_DELETE:
            file = event.name and os.path.join(event.path, event.name) or event.path
            # only "delete" events?
            print "deleted",file
            if file in self.file2ids:
                for id in self.file2ids[file]:
                    self.on_delete(id)
                    del self.id2file[id]

                del self.file2ids[file]

    def add_watch(self,id, file):
        self.id2file[id] = file


        if file in self.file2ids:
            self.file2ids[file].add(id)
        else:
            self.file2ids[file] = Set([id])
            res = self.wm.add_watch(file, pyinotify.IN_DELETE) ## pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM)
            if file in res:
                print "add watch", file
                self.file2wd[file] = res[file]

    def remove_watch(self, id):
        if id in self.id2file:
            file = self.id2file[id]
            del self.id2file[id]

            if file in self.file2ids:
                self.file2ids[file].remove(id)
                if len(self.file2ids[file]) == 0:
                    del self.file2ids[file]

                    if file in self.file2wd:
                        print "remove watch", file
                        self.wm.rm_watch(self.file2wd[file], False)
            
                        del self.file2wd[file]

    def get_file(self, id):
        if id in self.id2file:
            return self.id2file[id]
        else:
            return None
