#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
#
#   This file is part of tau4.
#
#   tau4 is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   tau4 is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with tau4. If not, see <http://www.gnu.org/licenses/>.


import os

from tau4.data import flex
from tau4.sweng import PublisherChannel


class LogFileControllerModel:

    def __init__( self):
        self.__fv_logfile_pathname = flex.VariableDeMoPe( value="./oscilloscope.xy.log", label="Pathname of log file", dim="", dirname="./")
        self.__fv_logfile_pathname.restore()
        self.__logfile = None
        self.__is_enabled = True
        self.__is_open = False
        self.__exception = ""

        self.__tau4p_on_modified = PublisherChannel.Synch( self)
        return

    def logfile_disable( self):
        self.__is_enabled = False

        self.__tau4p_on_modified()
        return self

    def logfile_enable( self):
        self.__is_enabled = True

        self.__tau4p_on_modified()
        return self

    def logfile_is_enabled( self):
        return self.__is_enabled == True

    def logfile_pathname( self, arg=None):
        if arg is None:
            return self.__fv_logfile_pathname

        logfile_was_enabled = self.logfile_is_enabled()
        self.logfile_disable()

        self.__fv_logfile_pathname.value( str( arg))
        self.__fv_logfile_pathname.store()

        if self.logfile_is_open():
            self.logfile_close()
            self.logfile_open()

        if logfile_was_enabled:
            self.logfile_enable()

        self.__tau4p_on_modified()
        return self

    def logfile_close( self):
        self.__logfile.close()
        self.logfile_is_open( False)
        return self

    def logfile_exception( self):
        return self.__exception

    def logfile_is_open( self, arg=None):
        if arg is None:
            return self.__is_open

        self.__is_open = arg
        return self

    def logfile_open( self):
        try:
            self.__logfile = open( self.logfile_pathname().value(), "a")
            self.__exception = ""
            self.logfile_is_open( True)

        except FileNotFoundError as e:
            self.__exception = e

        return

    def logfile_reset( self):
        if self.logfile_is_open():
            self.logfile_close()
            os.unlink( self.logfile_pathname())
            self.logfile_open()

        else:
            os.unlink( self.logfile_pathname())

        return self

    def logfile_write( self, x, y, flush=False):
        if self.logfile_is_open():
            self.__logfile.write( "%s\t%s\n" % (x, y))
            if flush:
                self.__logfile.flush()

        return self

    def reg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified += tau4s
        return self

