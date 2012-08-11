#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf, GLib, GObject
import os.path
import copy

#modes
(SUBDIR,
DUPLICATE) = range(2)
#tree model columns
(COLUMN_NAME,
COLUMN_STATE,
COLUMN_URL) = range(3)
#states
STATES = (NONE, PAUSED, FINISHED,
          EXPORTED) = ("None", "Paused",
                       "Finished", "Exported")

class DirDoesntExist(IOError):
    def __init__(self, string):
        self.message = string

class FileDoesntExist(IOError):
    def _init__(self, string):
        self.message = string

class BadStateFile(StandardError):
    def __init__(self, string):
        self.message = string

class State(object):
    def __del__(self):
        self.save()

    def save(self):
        with open(self.file_uri, "w") as statefile:
            if self.state == PAUSED:
                statefile.write(PAUSED + "/" +self.paused_picture + "\n")
            else:
                statefile.write(self.state + "\n")
            for pic in self.pictures:
                statefile.write(pic + "/" + str(self.counts[pic]) + "\n")

    def set_picture_count(self, picture, count):
        if picture in self.pictures:
            self.counts[picture] = count

    def set_exported(self):
        self.state = EXPORTED
        self.save()

    def set_finished(self):
        self.state = FINISHED
        self.save()

    def pause(self, picture):
        if picture in self.pictures:
            self.state = PAUSED
            self.paused_picture = picture
            self.save()

    def __restore_state(self, line):
        var = line.split("/")
        try:
            s = var[0].split("\n")[0]
            if s in STATES:
                self.state = s
                if self.state == PAUSED:
                    self.paused_picture = var[1].split("\n")[0]
        except IndexError:
            raise BadStateFile(line)

    def __init__(self, file_uri):
        self.pictures = []
        self.counts = {}
        self.state = NONE
        self.paused_picture = ""

        if not(os.path.isfile(file_uri)):
            raise FileDoesntExist(file_uri)
        self.file_uri = file_uri

        with open(file_uri, "r") as statefile:
            self.__restore_state(statefile.readline())
            line = statefile.readline()
            while line != "" and line != "\n" and line != None:
                a = line.split("/")
                line = statefile.readline()
                try:
                    pic = a[0]
                    count = int(a[1])
                except ValueError, IndexError:
                    continue

                self.pictures.append(pic)
                self.counts[pic] = count

class Manager(object):
    """The Manager deals with directories listing and plain text file management
    so that the Window doesn't have to care about IO except for loading the pictures
    """

    def __del__(self):
        self.save()

    def save(self):
        with open(self.settings_file, "w") as sfile:
            for root in self.root_dirs:
                sfile.write(root + "\n")

    def get_directories(self):
        """Returns: a tuple ((Dir_Name, State, (Subdir))...)"""
        for i in self.directories:
            yield (i, self.directories[i])

    def export_to_directory(self, directory, dir_listing, mode):
        """Export all the pictures marked for export in the directories given in parameter"""
        pass

    def add_user_directory(self, url):
        """Add a direcotory to the list of indexed directories"""
        if not(os.path.isdir(url)):
            raise DirDoesntExist(url)

        self.root_dirs.append(url)
        os.path.walk(url, self.__index_dir, None)

    def remove_user_directory(self, url):
        if url in self.root_dirs:
            del self.root_dirs[self.root_dirs.index(url)]

            for subdir in self.directories:
                if subdir.startswith(url):
                    del self.directories[subdir]

    def update_dir_state(self, url, state):
        if state in STATES and self.directories.has_key(url):
            self.directories[url] = state

    def __get_dir_state(self, url):
        statefile = os.path.join(url, ".printy_state")
        if (os.path.isfile(statefile)):
            with open(statefile, "r") as sfile:
                line = sfile.readline()
                if line is '':
                    return NONE

                state = line.split("/")[0].split("\n")[0]
                if state in STATES:
                    return state
                else:
                    return NONE

        else:
            return NONE

    def __index_dir(self, arg, dirname, fnames):
        state = self.__get_dir_state(dirname)
        self.directories[dirname] = state

    def __init__(self):
        self.root_dirs = []
        self.directories = {}
        self.settings_file = ""

        #first we read the list of root dirs
        self.settings_file = os.path.join(os.path.expanduser("~/.local/share"), "printy/settings")
        if not(os.path.isfile(self.settings_file)):
            open(settings_file, "w")

        with open(self.settings_file, "r") as sfile:
            line = sfile.readline()
            while line:
                url = line.split("\n")[0]
                if os.path.isdir(url):
                    self.root_dirs.append(url)
                line = sfile.readline()

        #then we list each subdir and determine its state
        for root in self.root_dirs:
            os.path.walk(root, self.__index_dir, None)

class Dir(object):
    """Represents a directory and manages its hidden file"""

    def __del__(self):
        del self.state

    def get_current_picture_name(self):
        return self.current_picture

    def get_current_picture_uri(self):
        """Returns the current picture uri"""
        return os.path.join(self.directory, self.current_picture)

    def get_current_picture_count(self):
        """Returns the number of time the current picture should be printed"""
        return self.state.counts[self.current_picture]

    def set_count(self, count):
        """Define the number of times a picture should be printed
        and returns the next picture uri or a None if there is no more picture"""
        self.state.set_picture_count(self.current_picture, count)
        return self.next_picture()

    def __move(self, count):
        i = self.state.pictures.index(self.current_picture)
        try:
            self.current_picture = self.state.pictures[i+count]
        except IndexError:
            return None

        return self.get_current_picture_uri()

    def previous_picture(self):
        """Returns the uri of the previous picture"""
        return self.__move(-1)

    def next_picture(self):
        """Returns the uri of the following picture"""
        return self.__move(1)

    def get_total_count(self):
        total = 0
        for picname in self.state.pictures:
            total += self.state.counts[picname]

        return total

    def get_current_picture_number(self):
        return self.state.pictures.index(self.current_picture) + 1

    def get_nb_pictures(self):
        """Returns the number of pictures in this directory"""
        return len(self.state.pictures)

    def get_state(self):
        return self.state.state

    def set_finished(self):
        self.state.set_finished()

    def set_exported(self):
        self.state.set_exported()

    def pause(self):
        """Pause the processing of this directory"""
        self.state.pause(self.current_picture)

    def __fill_state_file(self, sfile):
        """Fill the state file with all the pictures in this directory with a count
        of 0 for each picture.
        State is set to Paused on first picture found"""
        def do_dir(statefile, dirname, fnames):
            fnames.sort()
            statefile.write(NONE + "\n")
            for index, pic in enumerate(fnames):
                if not(os.path.isdir(os.path.join(dirname, pic))) and pic[0] != '.':
                    statefile.write(pic + "/0\n")
            del fnames[:]

        with open(sfile, "w") as statefile:
            os.path.walk(self.directory, do_dir, statefile)

    def __init__(self, directory):
        self.directory = directory
        if not(os.path.isdir(directory)):
            raise DirDoesntExist(directory)

        sfile = os.path.join(directory, ".printy_state")
        if not(os.path.isfile(sfile)):
            self.__fill_state_file(sfile)

        self.state = State(sfile)
        if self.state.paused_picture != "":
            self.current_picture = self.state.paused_picture
        else:
            self.current_picture = self.state.pictures[0]

class CountLabel(Gtk.Label):
    singular_message = "%s"
    plural_message = "%s"
    count = 0

    def set_count(self, count):
        self.count = count
        if (count > 1):
            self.set_label(self.plural_message % count)
        else:
            self.set_label(self.singular_message % count)

    def __init__(self, singular, plural, count):
        Gtk.Label.__init__(self)

        self.singular_message = singular
        self.plural_message = plural
        self.set_count(count)

class MagicImage(Gtk.DrawingArea):
    hsize = 0
    vsize = 0
    imgheight = 0
    imgwidth = 0
    image_url = ""

    def set_image(self, url):
        if not(os.path.isfile(url)):
            raise FileDoesntExist()
        self.image_url = url

    def __draw(self, widget, cr):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        if width != self.hsize or height != self.vsize:
            self.hsize, self.vsize = width, height

        if self.imgwidth > width and self.imgheight > height:
            #on redimensionne
            pass
        elif self.imgwidth < width and self.imgheight > height:
            pass
        elif self.imgheight < height and self.imgwidth > width:
            pass
        else:
            pass

        #set_source_pixbuf(resized_pixbuf, xanchor, yanchor)
        cr.set_source_rgb(1, 0.5, 0.25)
        cr.rectangle(0, 0, self.imgwidth, self.imgheight)
        cr.fill()

    def __configure(self, widget, event):
        pass

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(640, 480)
        self.connect("draw", self.__draw)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.p = GdkPixbuf.Pixbuf.new_from_file("/home/florent/Images/4137393_700b.jpg")#"/home/florent/Images/2005-11 Paris grand palais/Paris Grand Palais-11.JPG")
        self.imgwidth, self.imgheight = self.p.get_width(), self.p.get_height()

class Window(Gtk.Window):
    """Display the pictures, the total count, progress bar..."""
    workingDir = None

    def reload_viewer(self):
        nb = self.workingDir.get_current_picture_number()
        self.nbLabel.set_count(nb)
        self.totalLabel.set_count(self.workingDir.get_total_count())
        self.drawingArea.set_image(self.workingDir.get_current_picture_uri())
        fraction = float(nb-1) / self.workingDir.get_nb_pictures()
        self.progressBar.set_fraction(fraction)

        self.notebook.set_current_page(1)

    def set_count(self, count):
        if not(self.workingDir):
            return
        next_pic = self.workingDir.set_count(count)
        self.process_move(next_pic)

    def process_move(self, next_pic):
        if next_pic:
            self.reload_viewer()
        else:
            if self.workingDir.get_current_picture_number() != 1:
#Show a little dialog that says "hey there is no more pictures to process" and give the number of pictures to print
                self.workingDir.set_finished()
                self.reload_home()

    def reload_home(self):
        if self.workingDir:
            state = self.workingDir.get_state()
            url = self.workingDir.directory
            self.workingDir = None

            self.manager.update_dir_state(url, state)
            self.__fill_view()

        self.notebook.set_current_page(0)

    def __init_viewer(self):
        viewerBox = Gtk.VBox()
        self.notebook.append_page(viewerBox, Gtk.Label("Viewer"))

        infoBox = Gtk.HBox(False, 5)
        viewerBox.pack_start(infoBox, False, True, 5)
        progressBar = Gtk.ProgressBar()
        progressBar.set_fraction(22./144)
        nbLabel = CountLabel("Photo n°%s", "Photo n°%s", 1)
        totalLabel = CountLabel("%s photo à imprimer", "%s photos à imprimer", 14)
        infoBox.pack_start(nbLabel, False, False, 5)
        infoBox.pack_start(progressBar, True, True, 5)
        infoBox.pack_start(totalLabel, False, False, 5)

        drawingArea = MagicImage()
        viewerBox.pack_start(drawingArea, True, True, 0)

        controlBox = Gtk.HBox(False, 5)
        viewerBox.pack_start(controlBox, False, False, 5)
        def back():
            self.workingDir.pause()
            self.reload_home()
        backButton = Gtk.Button("< Retour")
        backButton.connect("clicked", lambda b: back())
        controlBox.pack_start(backButton, False, False, 5)

        space1 = Gtk.Label(" ")
        controlBox.pack_start(space1, True, True, 5)

        #count buttons
        def get_count_button(button):
            try:
                no = int(button.get_label())
            except ValueError:
                print "Caught you bitch !"
                return
            self.set_count(no)
        for i in range(5):
            button = Gtk.Button(str(i))
            controlBox.pack_start(button, False, False, 5)
            button.connect("clicked", get_count_button)

        space2 = Gtk.Label(" ")
        controlBox.pack_start(space2, True, True, 5)

        #Navigation buttons
        nextButton = Gtk.Button("Suivant >")
        def next_picture():
            if self.workingDir:
                self.process_move(self.workingDir.next_picture())
        nextButton.connect("clicked", lambda b: next_picture())
        controlBox.pack_end(nextButton, False, False, 5)
        previousButton = Gtk.Button("< Précédent")
        def prev_picture():
            if self.workingDir:
                self.process_move(self.workingDir.previous_picture())
        previousButton.connect("clicked", lambda b: prev_picture())
        controlBox.pack_end(previousButton, False, False, 5)

        self.progressBar, self.nbLabel, self.totalLabel, self.drawingArea = progressBar, nbLabel, totalLabel, drawingArea

    def __init_home(self):
        def row_activated(widget, path, column):
            url = self.tree[path][COLUMN_URL]
            self.workingDir = Dir(url)
            self.reload_viewer()

        def set_icon(col, cell, model, iter_, data):
            state = model[iter_][COLUMN_STATE]
            icons = {PAUSED: Gtk.STOCK_MEDIA_PAUSE,
                     FINISHED: Gtk.STOCK_APPLY,
                     EXPORTED: Gtk.STOCK_FLOPPY,
                     NONE: Gtk.STOCK_DIRECTORY}
            cell.set_property("stock-id", icons[state])

        bigBox = Gtk.VBox(False, 5)
        self.notebook.append_page(bigBox, Gtk.Label("Home"))

        #Welcome labels
        welcome = Gtk.Label("<big><b>Bienvenue</b></big>")
        welcome.set_use_markup(True)
        welcome.set_justify(Gtk.Justification.LEFT)
        bigBox.pack_start(welcome, False, False, 5)
        welcome2 = Gtk.Label("Double cliquez sur le dossier à traiter\nou choisissez \"Ajouter un dossier d'images\" pour définir les dossier contenants vos photos")
        welcome2.set_justify(Gtk.Justification.LEFT)
        bigBox.pack_start(welcome2, False, False, 5)

        #Directories view
        scroll = Gtk.ScrolledWindow()
        bigBox.pack_start(scroll, True, True, 5)

        view = Gtk.TreeView()
        view.set_headers_visible(False)
        view.connect("row-activated", row_activated)
        scroll.add(view)

        box = Gtk.CellAreaBox()
        pixbuf = Gtk.CellRendererPixbuf()
        box.pack_start(pixbuf, False, False, True)

        text = Gtk.CellRendererText()
        box.pack_start(text, True, False, False)
        box.attribute_connect(text, "text", COLUMN_NAME)

        col = Gtk.TreeViewColumn.new_with_area(box)
        col.set_cell_data_func(pixbuf, set_icon);
        view.append_column(col)

        self.tree = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING)
        self.tree.set_sort_column_id(COLUMN_NAME, Gtk.SortType.ASCENDING)
        view.set_model(self.tree)
        self.view = view

        #Action buttons
        controlBox = Gtk.HBox(True, 0)
        bigBox.pack_start(controlBox, False, False, 5)

        add_dirButton = Gtk.Button("Ajouter un dossier de photos")
        exportButton = Gtk.Button("Exporter les images sélectionnées")
        controlBox.pack_start(add_dirButton, True, True, 5)
        controlBox.pack_start(exportButton, True, True, 5)

    def __fill_view(self):
        """Une fonction toute pleine de récursion :-)"""
        self.tree.clear()

        dirs = copy.copy(self.manager.directories)
        iters = {}

        def do(url):
            if not(iters.has_key(url)):
                parent = get_or_make_parent(url)
                iters[url] = iter_ = self.tree.append(parent)
                self.tree.set(iter_, COLUMN_NAME, os.path.basename(url),
                              COLUMN_STATE, dirs[url],
                              COLUMN_URL, url)
                return iter_

        def get_or_make_parent(url):
            root = os.path.dirname(url)
            if dirs.has_key(root):
                if iters.has_key(root):
                    return iters[root]
                else:
                    return do(root)

        for url in dirs:
            do(url)

        for root in self.manager.root_dirs:
            path = self.tree.get_path(iters[root])
            self.view.expand_row(path, False)

    def __init__(self, manager):
        Gtk.Window.__init__(self)
        self.set_title("Printy")
        self.connect("delete-event", lambda a, b: quit())
        self.get_settings().set_property("gtk-application-prefer-dark-theme", True)
        self.set_hide_titlebar_when_maximized(True)
        self.maximize()

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.add(self.notebook)

        self.__init_home()
        self.__init_viewer()

        self.manager = manager
        self.__fill_view()

if __name__ == "__main__":
    m = Manager()
    w = Window(m)
    w.show_all()
    w.notebook.set_current_page(0)
    Gtk.main()
