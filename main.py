#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, GLib, GObject
import os.path
import copy

from src import *

class Window(Gtk.Window):
    """Display the pictures, the total count, progress bar..."""
    workingDir = None

    def export(self):
        print "I'm gonna export"

    def reload_viewer(self):
        #get all the data from the current Dir
        nb = self.workingDir.get_current_picture_number()
        nb_pictures = self.workingDir.get_nb_pictures()
        total = self.workingDir.get_total_count()
        count = self.workingDir.get_current_picture_count()

        #Update the widgets
        self.picCountLabel.set_count(count)
        self.totalLabel.set_count(total)
        self.drawingArea.set_image(self.workingDir.get_current_picture_uri())
        fraction = float(nb-1) / nb_pictures
        self.progressBar.set_fraction(fraction)
        self.progressBar.set_text("Photo %s sur %s" % (nb-1, nb_pictures))

        self.notebook.set_current_page(1)

    def set_count(self, count):
        if not(self.workingDir):
            return
        next_pic = self.workingDir.set_count(count)
        self.process_move(next_pic)

    def process_move(self, next_pic):
        if next_pic:
            try:
                self.reload_viewer()
            except FileIsNotAnImage:
                self.process_move(self.workingDir.next_picture())
        else:
            if self.workingDir.get_current_picture_number() != 1:
                dialog = LittleDialog(self, "Félicitations", "Il n'y a plus d'image à traiter dans ce dossier")
                dialog.display()
                self.workingDir.set_finished()
                self.reload_home()

    def reload_home(self):
        if self.workingDir:
            #update the treeview and the underlying Manager
            state = self.workingDir.get_state()
            url = self.workingDir.directory
            self.workingDir = None

            self.manager.update_dir_state(url, state)
            self.__fill_view() #ugly

        self.notebook.set_current_page(0)

    def __init_viewer(self):
        viewerBox = Gtk.VBox()
        self.notebook.append_page(viewerBox, Gtk.Label("Viewer"))

        infoBox = Gtk.HBox(False, 5)
        viewerBox.pack_start(infoBox, False, True, 5)
        progressBar = Gtk.ProgressBar()
        progressBar.set_show_text(True)
        picCountLabel = CountLabel("À imprimer %s fois", "À imprimer %s fois", 0)
        totalLabel = CountLabel("%s photo à imprimer", "%s photos à imprimer", 0)
        infoBox.pack_start(picCountLabel, False, False, 5)
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

        self.progressBar, self.picCountLabel, self.totalLabel, self.drawingArea = progressBar, picCountLabel, totalLabel, drawingArea

    def __init_home(self):
        def row_activated(widget, path, column):
            url = self.tree[path][COLUMN_URL]
            try:
                self.workingDir = Dir(url)
            except NoImgInDir:
                dialog = LittleDialog(self, "Erreur", "Il n'y a aucune photo dans ce dossier")
                dialog.display()
            else:
                self.reload_viewer()

        def set_icon(col, cell, model, iter_, data):
            state = model[iter_][COLUMN_STATE]
            icons = {PAUSED: Gtk.STOCK_MEDIA_PAUSE,
                     FINISHED: Gtk.STOCK_APPLY,
                     EXPORTED: Gtk.STOCK_FLOPPY,
                     NONE: Gtk.STOCK_DIRECTORY}
            cell.set_property("stock-id", icons[state])

        def add_dir(button):
            dialog = Gtk.FileChooserDialog("Choisissez le dossier à ajouter",
                                           self, Gtk.FileChooserAction.SELECT_FOLDER)
            dialog.add_buttons(Gtk.STOCK_CANCEL, 0,
                               Gtk.STOCK_OK, 1)
            if dialog.run() == 1:
                url = GLib.filename_from_uri(dialog.get_uri(), "")
                dialog.destroy()
                self.manager.add_user_directory(url)
                self.__fill_view()

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
        add_dirButton.connect("clicked", add_dir)
        exportButton = Gtk.Button("Exporter les images sélectionnées")
        exportButton.connect("clicked", lambda b: self.export())
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
