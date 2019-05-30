#import pygtk
#pygtk.require ("2.0")
#import gtk, gobject

# Reused from TerminatorPP!!!

import gnomevfs
import shutil, os, subprocess, urllib, sys, threading, select, pipes

# if file is inside user home directory, replace by "~"
def path_replace_home(file):
  home = os.getenv("HOME")
        
  if file == home or file.startswith(home + "/"):
    return "~" + file[len(home) : ]
  else:
    return file
  

# Returns a string describing the type of the file
def file_description(file):
  # com o comando file:
  #process = subprocess.Popen(["file", "--brief", file], stdout=subprocess.PIPE)
  #return process.stdout.readline().rstrip()
  mime = gnomevfs.get_file_mime_type(file)
  if mime:
    return gnomevfs.mime_get_description(mime)
  else:
    return None

# forma_number(12345) returns "12 345"
def format_number(n):
    s = str(n)
    res = ""
    while len(s) > 3:
        res = " " + s[len(s) - 3 :] + res
        s = s[0 : len(s) - 3]

    return (s + res).lstrip()


# returns a widget with the file details of the given files
# If it is only one file, returns a single label
# Else, returns a table!
def details(files):

  if len(files) == 1:

    # if it is only one file, show only one Label.
    # the filename is not displayed
    txt = path_replace_home(files[0]) + "\n"
    if not os.path.isdir(files[0]):
      # the file size, if not a directory
      txt += format_number(os.path.getsize(files[0]))+ " bytes  "

    txt += get_file_description(files[0])

    label = gtk.Label(txt)
    label.show()
  
    return label

  else:
    # one extra row!
    table = gtk.Table(rows= 1 + len(files) , columns=3, homogeneous=False)

    total_bytes = 0
    total_files = 0 # the files, not directories

    for row in range(0, len(files)):
      file = files[row]

      label = gtk.Label(os.path.basename(file))
      label.set_alignment(0, 0.5)
      table.attach(label, 0, 1, row, row + 1, xpadding=5)

      if not os.path.isdir(file):
        size = os.path.getsize(file)
        total_bytes += size
        total_files += 1

        label = gtk.Label(format_number(size))
        label.set_alignment(1, 0.5)
        table.attach(label, 1, 2, row, row + 1, xpadding=5)

      label = gtk.Label(get_file_description(file))
      label.set_alignment(0, 0.5)
      table.attach(label , 2, 3, row, row + 1, xpadding=5)

    # The summary row:
    if total_files > 0:
      last_row = len(files)

      # The last row is separated from the others
      table.set_row_spacing(last_row - 1, 10)

      label = gtk.Label(_("TOTAL"))
      table.attach(label, 0, 1, last_row, last_row + 1, xpadding=5)

      label = gtk.Label(format_number(total_bytes))
      label.set_alignment(1, 0.5)
      table.attach(label, 1, 2, last_row, last_row + 1, xpadding=5)

      label = gtk.Label(_("bytes"))
      label.set_alignment(0, 0.5)
      table.attach(label, 2, 3, last_row, last_row + 1, xpadding=5)

    table.show_all()
    return table


# gives a small string describing a set of files, 
# like:
#  folder "myfolder"
#  4 files
# etc
def resume(files):
  txt = ""

  if len(files)==1:
    if os.path.isdir(files[0]):
      txt = "Folder"
    else:
      txt = "File"
    txt += " \""+os.path.basename(files[0])+"\""

  else:

    count_files = 0
    count_dirs = 0

    for file in files:
      if os.path.isdir(file):
        count_dirs += 1
      else:
        count_files += 1

    if count_files==1:
      txt = "1 file"
    elif count_files >1:
      txt = str(count_files)+" files"

    if count_dirs > 0:
      if txt != "":
        txt += " and "

      if count_dirs==1:
        txt += "1 folder"
      else:
        txt += str(count_dirs)+" folders"

  return txt

# convert a list of uris to files
# Ignore the uris which are not files
def uris_to_paths(uris):

  paths = []
  for uri in uris:
    if uri.startswith("file:/"):
      uri = uri[5:] # keep the "/"
      while uri.startswith("//"):
        uri = uri[1:]

      paths.append(urllib.unquote(uri))

  return paths

# convert a list of file paths to uris
# The paths should be absolute
def paths_to_uris(paths):
    return [ "file:"+urllib.quote(path) for path in paths ]      


# Gives a human readable string for the given drag and drop action
def action_name(action):
  if action == gtk.gdk.ACTION_COPY:
    return "Copy"
  elif action == gtk.gdk.ACTION_MOVE:
    return "Move"
  elif action == gtk.gdk.ACTION_LINK:
    return "Link"
  else:
    return None

# Varios file operations
class FileOperations:

  def __init__(self):

    self.clipboard = gtk.clipboard_get()

  # Opens the given files using the operation system associated applications
  def open(self, files):

    for file in files:
      dbg("Opening %s" % file)
      subprocess.Popen(["gnome-open",file])

  # Verifies if the clipboard has files. The response will be given in the callback
  # callback(are_available, user_data)
  def clipboard_files_available(self, callback, user_data):
    # Will have to request the list of supported targets
    self.clipboard.request_targets(self.clipboard_targets_callback, (callback, user_data))
   
  def clipboard_targets_callback(self, clipboard, targets, user_data2):
    files_available = "x-special/gnome-copied-files" in targets

    # call the user callback that was given in clipboard_files_available, with the user_data also given as the last argument
    (user_callback, user_data) = user_data2
    user_callback(files_available, user_data)

  # copy or cut a list of files to the clipboard
  # Note: this wont have results until the user pastes then somewhere
  def copy_to_clipboard(self, files, cut=False):

    # they will be copied as list of files or as a string
    # Use differentes info number, to identify it when clipboard_get_callback is called!
    targets = [('x-special/gnome-copied-files', 0, 0), ("UTF8_STRING", 0, 1)]

    user_data = (files, cut and "cut" or "copy")

    self.clipboard.set_with_data(targets, self.clipboard_get_callback, self.clipboard_clear_callback, user_data)

  # the system as requested the data to be copied to the clipboard!
  def clipboard_get_callback(self, clipboard, selectiondata, info, user_data):
    (files, action) = user_data

    if info == 0:
      # The first line is the action (copy or cut) and the others are the uris:
      # This was based in Thunar source code!
      txt = action + "\n" + "\n".join(paths_to_uris(files))

      selectiondata.set(selectiondata.get_target(), 8, txt)

    else:
      selectiondata.set_text("\n".join(files) + "\n")
        
  def clipboard_clear_callback(self, clipboard, user_data):
    pass

  # Pastes files to the given folder
  def paste_from_clipboard(self, destination):
    self.clipboard.request_contents("x-special/gnome-copied-files", self.clipboard_paste_callback, destination)
    
  # the system is giving the list of files to be copied or moved!
  def clipboard_paste_callback(self, clipboard, selectiondata, user_data):
    
    destination = user_data

    lines = selectiondata.data.splitlines()

    action_str = lines[0].rstrip()
    if action_str == "copy":
      action = gtk.gdk.ACTION_COPY
    elif action_str == "cut":
      action = gtk.gdk.ACTION_MOVE
    else:
      # not supported...
      return

    uris = lines[1:]
    files = uris_to_paths(uris)

    # do the file operation
    self.copy_or_move(destination, action, files)

  # Asks the user if he wants to delete the files, and if he says Yes, deletes then
  def delete_confirm(self, files):

    names_folders = []
    names_files = [] # files that are not folders!
    for file in files:
      if os.path.isdir(file):
        names_folders.append(os.path.basename(file))
      else:
        names_files.append(os.path.basename(file))

    
    dialog = gtk.Dialog("", None, gtk.DIALOG_MODAL  | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT, gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

    vbox = dialog.get_content_area()
    vbox.set_spacing(10)

    if names_folders:
      vbox.add(gtk.Label("Recursive delete this folders?"))

      # Display the list of files inside a ScrolledWindow because they could be many!
      text = gtk.TextView()
      text.set_editable(False)
      text.get_buffer().set_text("\n".join(names_folders))

      scroll = gtk.ScrolledWindow()
      scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
      scroll.add(text)

      vbox.add(scroll)
      
    if names_files:
      if names_folders:
        vbox.add(gtk.Label("And these files?"))
      else:
        vbox.add(gtk.Label("Delete these files?"))


      text = gtk.TextView()
      text.set_editable(False)
      text.get_buffer().set_text("\n".join(names_files))

      scroll = gtk.ScrolledWindow()
      scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
      scroll.add(text)

      vbox.add(scroll)

    dialog.show_all()

    response = dialog.run()
    dialog.destroy()

    if response == gtk.RESPONSE_ACCEPT:
      # delete the files!
      self.delete(files)            
    
  # Start a thread to copy or move files to the destination
  def copy_or_move(self, destination_folder, action, files):
    if action == gtk.gdk.ACTION_COPY:
      title = "Copying files"
      commands = [ ["cp", "-rvp", file, destination_folder] for file in files ]

    elif action == gtk.gdk.ACTION_MOVE:
      title = "Moving files"
      commands = [ ["mv", "-v", file, destination_folder] for file in files ]

    else:
      return

    ThreadCommands(commands)

  # Start a thread to delete the files
  def delete(self, files):
    commands = [ ["rm", "-rvf", file] for file in files ]

    ThreadCommands(commands)


        
# A thread that executes a list of external commands
# If it takes some time to execute, it opens a window with information
# The title of the window is the command being executed
# A label displays the last line read from stdout
# A textarea shows the stderr of the commands
# A button allows the user to cancel execution of the commands
class ThreadCommands(threading.Thread):

  # commands is a list of lists with each command arguments
  # This will start the daemon
  def __init__(self, commands):
    threading.Thread.__init__(self)

    self.commands = commands

    # says if the user has clicked the button to cancel execution
    self.cancelled = threading.Event()

    self.terminated = False

    # the current process
    self.process = None

    # this label will have the last line read from stdout
    self.output_label = gtk.Label("")
    self.output_label.set_selectable(True)
    self.output_label.show()
    
    # this textarea will have the lines from stderr
    self.error_area = gtk.TextView()

    self.error_area_scroll = gtk.ScrolledWindow()
    self.error_area_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.error_area_scroll.add(self.error_area)

    # button to stop the process (or close the window)
    self.button = gtk.Button("Stop")
    self.button.connect("clicked", self.button_clicked)
    self.button.show()

    hbox = gtk.HBox(False,10)
    hbox.show()
    hbox.pack_start(self.output_label,True,True)
    hbox.pack_end(self.button, False,False)

    vbox = gtk.VBox(False,10)
    vbox.show()
    vbox.pack_start(hbox,False,False)
    vbox.pack_start(self.error_area_scroll, True, True)

    # the window will be initially hidden
    self.window = gtk.Window()

    self.window.set_size_request(500, 50)
    self.window.set_modal(False)
    self.window.add(vbox)

    # this will make the window show if the thread runs for some time
    gobject.timeout_add (2000, self.show_window)

    # update the output_label asynchronously in fixed intervals
    self.line_stdout = ""
    gobject.timeout_add (50, self.update_output_label)

    self.setDaemon(True)
    self.start()

  def button_clicked(self, b):
    # kill or close button

    self.cancelled.set()

    # if there is a process running, kill it!
    if self.process:
      self.process.kill()

    self.window.destroy()

  def show_window(self):
    if self.is_alive():
      self.window.show()
    # dont repeat
    return False

  def update_output_label(self):
    self.output_label.set_text(self.line_stdout)

    # return value of True means to continue executing this timer

    # repeats the timer while the thread is alive:
    return not self.terminated
    
  # add this line to the textarea, if it is the first line, make the window visible!
  def add_error(self, line):
    self.error_area.get_buffer().insert_at_cursor(line)
    if not self.error_area_scroll.get_property("visible"):
      self.window.set_size_request(500, 200)
      self.window.show()
      self.error_area_scroll.show_all()

  def run(self):
    try:
      error_count = 0

      for command_args in self.commands:
        if self.cancelled.isSet(): break

        command_str = " ".join(command_args)

        gtk.gdk.threads_enter()
        self.window.set_title(command_str)
        gtk.gdk.threads_leave()

        self.process = subprocess.Popen(command_args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        stderr = self.process.stderr
        stdout = self.process.stdout

        while True:
          if self.cancelled.isSet(): break

          handles = []
          if stdout: handles.append(stdout)
          if stderr: handles.append(stderr)

          # read from both sides without blocking:
          # http://docs.python.org/library/select.html
          handles_ready = select.select(handles, [], [], 100) [0]

          if stderr in handles_ready:
              line = stderr.readline()
              if line == "":
                  stderr = None 
              else:
                error_count +=1
                gtk.gdk.threads_enter()
                self.add_error(line)
                gtk.gdk.threads_leave()

          if stdout in handles_ready:
            line = stdout.readline()
            if line == "":
              stdout = None
            else:
              self.line_stdout = line

          self.process.poll()
          if self.process.returncode != None and not stdout and not stderr:
              break
         
      self.process = None

      if self.window.get_property("visible"):
        if not self.cancelled.isSet() and error_count > 0 :

          self.button.set_label("Close")

        else:
          self.window.destroy()

      self.terminated = True
    except:
      msg = str( sys.exc_info()[1] )
      print("error",msg)
  

class ApplicationInfo:
  def __init__(self, gnomevfs_info):
    self.name = gnomevfs_info[1]
    self.command = gnomevfs_info[2]
    self.can_multiple = gnomevfs_info[3]
    self.expect_uris = gnomevfs_info[4]


# If all the files on the list have the same default application, returns it. Else, returns None
# The application is returned as a tuple
# (id, Name, Command, can_open_multiple_files, expect_uris, uri_schemes, requires_terminal)
def get_default_application_for_files(files):
    id_comum = None
    for file in files:
        mime = gnomevfs.get_file_mime_type(file)
        if not mime:
          return None
        # Query the MIME database for the default Bonobo component to be activated to view files of MIME type mime_type
        app = gnomevfs.mime_get_default_application(mime)
        if not app:
          return None

        if id_comum == None:
            id_comum = app[0]
        elif app[0] != id_comum:
            return None
    return ApplicationInfo(gnomevfs.mime_application_new_from_id(id_comum))

# Returns the list of applications that can open all of the given files
# if any of the files don't have associated applications, returns None
def get_applications_for_files(files):
    ids_comuns = None
    for file in files:
        mime = gnomevfs.get_file_mime_type(file)
        if not mime:
          return None

        ids = set([app[0] for app in gnomevfs.mime_get_all_applications(mime)])
        if ids_comuns == None:
            ids_comuns = ids
        else:
            ids_comuns = ids_comuns & ids
    if ids_comuns:
      return [ApplicationInfo(gnomevfs.mime_application_new_from_id(id)) for id in ids_comuns]
    else:
      return None


# Open the set of files with the given application
def open_files_with_application(application, files):
    #can_multiple = application[3]
    #expect_uris = application[4]
    #command = application[2] # can have spaces!

    if application.expect_uris:
        args = paths_to_uris(files)
    else:
        args = files

    if application.can_multiple:
        cmd = application.command + " " + " ".join([ pipes.quote(file) for file in files])
        subprocess.Popen(cmd, shell=True)
    else:
      # If the app can only open one file, I will have to call it many times
      for arg in args:
        cmd = application.command + " " + pipes.quote(file)
        subprocess.Popen(cmd, shell=True)


if __name__ == "__main__":
  #gtk.gdk.threads_init()

  #command = ["cp","-rvp","/home/daniel/CESTO/_REC","/home/daniel/CESTO/_DEST"]

  #ThreadCommands([command])

  file = sys.argv[1]
  print(file,get_default_application_for_files(file))
  #gtk.main()
