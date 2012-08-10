#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, GdkPixbuf
import os.path

#modes
(SUBDIR,
DUPLICATE) = range(2)

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
    pictures = [];
    counts = {};
    state = "Paused";
    paused_picture = "";
    file_uri = "";

    def __del__(self):
        self.save()

    def save(self):
        with file(self.file_uri, "w") as statefile:
            if self.state == "Paused":
                statefile.write("Paused/" +self. paused_picture + "\n")
            for pic in self.pictures:
                statefile.write(pic + "/" + str(self.counts[pic]) + "\n")

    def set_picture_count(self, picture, count):
        if picture in self.pictures:
            self.counts[picture] = count

    def set_exported(self):
        self.state = "Exported"
        self.save()

    def set_finished(self):
        self.state = "Finished"
        self.save()

    def pause(self, picture):
        if picture in self.pictures:
            self.state = "Paused"
            self.paused_picture = picture
            self.save()

    def __restore_state(self, line):
        var = line.split("/")
        try:
            if var[0] in ("Paused", "Finished", "Exported"):
                self.state = var[0]
                if self.state == "Paused":
                    self.paused_picture = var[1].split("\n")[0]
        except IndexError:
            raise BadStateFile(line)

    def __init__(self, file_uri):
        if not(os.path.isfile(file_uri)):
            raise FileDoesntExist(file_uri)
        self.file_uri = file_uri

        with file(file_uri, "r") as statefile:
            self.__restore_state(statefile.readline())
            line = statefile.readline()
            while line:
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
    root_dirs = []
    directories = {}
    settings_file = ""

    def __del__(self):
        self.save()

    def save(self):
        with file(self.settings_file, "w") as sfile:
            for root in self.root_dirs:
                sfile.write(root + "\n")

    def get_user_directories(self):
        """Returns: a tuple ((Dir_Name, State, (Subdir))...)"""
        pass

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

    def __get_dir_state(self, url):
        statefile = os.path.join(url, ".printy_state")
        if (os.path.isfile(statefile)):
            with file(statefile, "r") as sfile:
                line = sfile.readline()
                if line is '':
                    return "None"

                state = line.split("/")[0]
                if state in ("Paused", "Finished", "Exported"):
                    return state
                else:
                    return "None"

        else:
            return "None"

    def __index_dir(self, arg, dirname, fnames):
        state = self.__get_dir_state(dirname)
        self.directories[dirname] = state

    def __init__(self):
        #first we read the list of root dirs
        self.settings_file = os.path.join(os.path.expanduser("~/.local/share"), "printy/settings")
        if not(os.path.isfile(self.settings_file)):
            file(settings_file, "w")

        with file(self.settings_file, "r") as sfile:
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
    directory = None
    current_picture = None
    state = None

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
        return self.state.pictures.index(self.current_image) + 1

    def get_nb_pictures(self):
        """Returns the number of pictures in this directory"""
        return len(self.state.pictures)

    def get_state(self):
        return self.state.state

    def pause(self):
        """Pause the processing of this directory"""
        self.state.pause(self.current_picture)

    def __fill_state_file(self, sfile):
        """Fill the state file with all the pictures in this directory with a count
        of 0 for each picture.
        State is set to Paused on first picture found"""
        def do_dir(statefile, dirname, fnames):
            i = 0;
            fnames.sort()
            for index, pic in enumerate(fnames):
                if(os.path.isfile(os.path.join(dirname, pic)) and not(pic[0] is '.')):
                    if i is 0:
                        statefile.write("Paused/" + pic + "\n")
                        i += 1;
                    statefile.write(pic + "/0\n")
                else:
                    del fnames[index]

        with file(sfile, "w") as statefile:
            os.path.walk(self.directory, do_dir, statefile)

    def __init__(self, directory):
        self.directory = directory
        if not(os.path.isdir(directory)):
            raise DirDoesntExist(directory)

        sfile = os.path.join(directory, ".printy_state")
        if not(os.path.isfile(sfile)):
            self.__fill_state_file(sfile)

        self.state = State(sfile)
        self.current_picture = self.state.paused_picture

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
        pass

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
        backButton = Gtk.Button("< Retour")
        controlBox.pack_start(backButton, False, False, 5)
        space1 = Gtk.Label(" ")
        controlBox.pack_start(space1, True, True, 5)
        for i in range(4):
            button = Gtk.Button(str(i))
            controlBox.pack_start(button, False, False, 5)
        space2 = Gtk.Label(" ")
        controlBox.pack_start(space2, True, True, 5)
        nextButton = Gtk.Button("Suivant >")
        controlBox.pack_end(nextButton, False, False, 5)
        previousButton = Gtk.Button("< Précédent")
        controlBox.pack_end(previousButton, False, False, 5)

        self.progressBar, self.nbLabel, self.totalLabel, self.drawingArea = progressBar, nbLabel, totalLabel, drawingArea

    def __init_home(self):
        bigBox = Gtk.VBox()
        self.notebook.append_page(bigBox, Gtk.Label("Home"))

    def __init__(self):
        Gtk.Window.__init__(self)
        self.connect("delete-event", lambda a, b: quit())
        self.get_settings().set_property("gtk-application-prefer-dark-theme", True)
        self.set_hide_titlebar_when_maximized(True)
        self.maximize()

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.add(self.notebook)

        #self.__init_home()
        self.__init_viewer()

if __name__ == "__main__":
    w = Window()
    w.show_all()
    Gtk.main()
