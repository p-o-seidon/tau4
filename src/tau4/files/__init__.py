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

import psutil

from tau4 import ThisName
from tau4 import threads
from tau4.data import pandora
from tau4.datalogging import SysEventLog
from tau4.oop import PublisherChannel, Singleton


class Monitor4OpenFiles(threads.Cycler, metaclass=Singleton):

    def __init__( self):
        self.__tau4p_on_modified = PublisherChannel.Synch( self)

        self.__process = psutil.Process()
        self.__pathnames = []

        self.__p_num_files_open = pandora.BoxMonitored( value=0, label="# open files")
        self.__p_num_files_open.reg_tau4s_on_modified( self._on_modified_num_files_open_)

        super().__init__( cycletime=15, udata=None)
        self.start()
        return

    def num_files_open( self):
        return self.__p_num_files_open.data()

    def _on_modified_num_files_open_( self, tau4pc):
        self.__tau4p_on_modified()
        return

    def pathnames_of_open_files( self):
        return self.__pathnames

    def reg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified += tau4s
        return

    def _run_( self, udata):
        try:
            self.__pathnames[:] = self.__process.open_files()
            self.__p_num_files_open.data( len( self.__pathnames))

        except psutil.NoSuchProcess as e:
            SysEventLog().log_error( "Exception encountered: '%s'. " % e, ThisName( self))

        return
