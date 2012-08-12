# -*- coding: utf-8 -*-

import os.path
import mimetypes

from constants import *
from errors import *

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
            else:
                raise BadStateFile(line)
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
                    raise BadStateFile(line)

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
        self.save()
        os.path.walk(url, self.__index_dir, None)

    def remove_user_directory(self, url):
        if url in self.root_dirs:
            del self.root_dirs[self.root_dirs.index(url)]
            self.save()

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
        if not(self.state.state in (FINISHED, EXPORTED)):
            try:
                self.state.pause(self.current_picture)
            except:
                return

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
                if not(os.path.isdir(os.path.join(dirname, pic))) and pic[0] != '.' \
                        and mimetypes.guess_type(pic)[0] == "image/jpeg":
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

        try:
            self.state = State(sfile)
        except BadStateFile:
            self.__fill_state_file(sfile)
            self.state = State(sfile)

        if self.state.paused_picture != "":
            self.current_picture = self.state.paused_picture
        elif len(self.state.pictures) > 0:
            self.current_picture = self.state.pictures[0]
        else:
            raise NoImgInDir(directory)
