# -*- coding: utf-8 -*-

class DirDoesntExist(IOError):
    def __init__(self, string):
        self.message = string

class FileDoesntExist(IOError):
    def _init__(self, string):
        self.message = string

class BadStateFile(Exception):
    def __init__(self, string):
        self.message = string

class NoImgInDir(Exception):
    def __init__(self, string):
        self.message = string

class FileIsNotAnImage(Exception):
    def __init__(self, string):
        self.message = string
