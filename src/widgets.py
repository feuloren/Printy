# -*- coding: utf-8 -*-

from gi.repository import Gtk, Gdk, GdkPixbuf
import os.path

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

    def set_image(self, url):
        if not(os.path.isfile(url)):
            raise FileDoesntExist()
        self.image_url = url

        try:
            self.original_pixbuf = GdkPixbuf.Pixbuf.new_from_file(url)
        except:
            raise FileIsNotAnImage(url)
        if self.get_realized():
            self.__configure(self, None)
            self.queue_draw()

    def __draw(self, widget, cr):
        if not(self.pixbuf):
            return

        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, self.xorig, self.yorig)
        cr.paint()

    def __configure(self, widget, event):
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        imgwidth, imgheight = self.original_pixbuf.get_width(), self.original_pixbuf.get_height()

        if imgwidth <= width and imgheight <= height:
            self.pixbuf = self.original_pixbuf
        else:
            if float(width)/height <= float(imgwidth)/imgheight:
                imgheight *= float(width)/imgwidth
                imgwidth = width
            else:
                imgwidth *= float(height)/imgheight
                imgheight = height
            self.pixbuf = self.original_pixbuf.scale_simple(imgwidth, imgheight, GdkPixbuf.InterpType.BILINEAR)
        self.xorig = (width - imgwidth)/2
        self.yorig = (height - imgheight)/2

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request(640, 480)
        self.connect("draw", self.__draw)
        self.connect_after("configure-event", self.__configure)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.pixbuf = None
        self.original_pixbuf = None
        self.image_url = ""

class LittleDialog(Gtk.Dialog):
    """A dialog with  simple OK button and a line of text"""
    def display(self):
        self.run()
        self.destroy()

    def __init__(self, parent, title, text):
        Gtk.Dialog.__init__(self)
        self.set_title(title)
        self.set_transient_for(parent)
        self.add_button(Gtk.STOCK_OK, 1)

        box = self.get_content_area()
        intitle = Gtk.Label()
        intitle.set_markup("<b><big>%s</big></b>" % title)
        box.pack_start(intitle, True, True, 10)
        intitle.show()

        label = Gtk.Label(text)
        box.pack_start(label, True, True, 10)
        label.show()
