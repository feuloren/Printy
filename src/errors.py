# -*- coding: utf-8 -*-

class DirDoesntExist(IOError):
    def __init__(self, string):
        self.message = string

class FileDoesntExist(IOError):
    def _init__(self, string):
        self.message = string

class BadStateFile(StandardError):
    def __init__(self, string):
        self.message = string

class NoImgInDir(StandardError):
    def __init__(self, string):
        self.message = string

class FileIsNotAnImage(StandardError):
    def __init__(self, string):
        self.message = string
