#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by F. Geiger, 1998 - 2017
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

"""\package setup4app

Synopsis:
    Unterstützung der Konfiguration von Apps.

History:
    -   2017-11-17:
        -   Setup durch Setup4 ersetzt.

    -   2017-11-15:
        -   Dokumetation.

    -   2017-11-12:
        -   Erstellt.
"""


import abc
import os
import platform
import time
from ruamel.yaml import YAML
yaml = YAML()
yaml.default_flow_style = False
yaml.indent = 4
yaml.width = 120

from tau4.oop import Singleton



class Setup4(metaclass=Singleton):

    """Base Class fürs Setup on Tau und einer App, muss abgeleitet werden.

    Verwendet yaml zum Lesen und Schreiben, was komplexe und doch übersichtliche
    Setup Files ermöglicht.

    \note
        Eines der ersten Statements von Apps, die dieses Singleton verwenden, muss

        \code{.py}
            Setup4_APP_NAME_GOES_HERE().appname( "YOUR APP NAME GOES HERE")

            print( Setup4_APP_NAME_GOES_HERE()._filepathname_())
                                            # Liefert "setup.YOUR APP NAME GOES HERE.yaml"
        \endcode

        sein!

        Das kann natürlich auch in der Base Class erfolgen.

    Usage:
        \code

        \endcode
    """

    def __init__( self):
        super().__init__()

        self.__appname = None
        self.__dirname = "."

        self.__setupdatadict_mtime = 0
        self.__setupdatadict = {}

        return

    def appname( self, appname=None):
        """Name der App, muss schreibend ausgeführt werden, bevor irgendeine andere Methode ausgeführt wird.
        """
        if appname is None:
            return self.__appname

        self.__appname = appname
        return self

    def _dirname_( self, dirname=None):
        if dirname is None:
            return self.__dirname

        self.__dirname = dirname
        return self

    def filecontent_default( self, yamlstring):
        """Schreibt yamlstring ins File self._filepathname_(), wenn das File nicht existiert oder leer ist.
        """
        if self._file_exists_( self._filepathname_()) and self._filesize_( self._filepathname_()) > 0:
            return self

        with open( self._filepathname_(), "w") as f:
            f.write( yamlstring)

        return self

    def _file_exists_( self, pathname):
        return os.path.exists( pathname) and os.path.isfile( pathname)

    def _filepathname_( self):
        if not self._is_appname_valid_():
            raise ValueError( """App name not set, yet. Call '%s().appname( "YOUR APP'S NAME")'. """ % self.__class__.__name__)

        return "%s/setup.%s.yaml" % (self.__dirname, self.__appname)

    def _filesize_( self, pathname):
        filestat = os.stat( pathname)
        return filestat.st_size

    def _hostname_( self):
        """name der CPU, auf der die SW läuft, also ariell, triton, rovercpu01 usw.
        """
        return platform.node()

    def _is_appname_valid_( self):
        """App Name ist zur Zeit genau dann nicht valid, wenn er None ist.
        """
        return self.__appname is not None

    def paramvalue( self, *keys):
        """Lesen eines Parameters.

        Usage:
            \code{.py}
                Setup4MyApp().paramvalue( "Section", "Key", 42)
                value = Setup4MyApp().paramvalue( "Section", "Key")
            \endcode

            oder

            \code{.py}
                Setup4MyApp().paramvalue( "Level 1", "Level 2", "Key", 42)
                value = Setup4MyApp().paramvalue( "Level 1", "Level 2", "Key")
            \endcode

            usw.
        """
        d = self.__setupdatadict
        for key in keys:
            d = d[ key]

        return d

    def paramvalue_change( self, *args):
        """Schreiben eines Parameters.

        Usage:
            \code{.py}
                Setup4MyApp().paramvalue( "Section", "Key", 42)
                value = Setup4MyApp().paramvalue( "Section", "Key")
            \endcode

            oder

            \code{.py}
                Setup4MyApp().paramvalue( "Level 1", "Level 2", "Key", 42)
                value = Setup4MyApp().paramvalue( "Level 1", "Level 2", "Key")
            \endcode

            usw.
        """
        keys = args[ :-1]
        value = args[ -1]
        d = self.__setupdatadict
        for key in keys[ :-1]:
            d = d[ key]

        d[ keys[ -1]] = value
        self.__setupdatadict_mtime = time.time()
        return d

    def sync( self):
        """YAML-Struktur mit Daten im Memory mit File auf Disk synch'en (beide Richtungen!)
        """
        pathname = self._filepathname_()
        filestat = os.stat( pathname)

        if self.__setupdatadict_mtime < filestat.st_mtime:
            with open( pathname, "r") as f:
                filecontent = f.read()

            setupdatadict = yaml.load( filecontent)
            if setupdatadict:
                self.__setupdatadict.update( setupdatadict)
                self.__setupdatadict_mtime = filestat.st_mtime

        elif self.__setupdatadict_mtime > filestat.st_mtime:
            with open( pathname, "w") as f:
                yaml.dump( self.__setupdatadict, f)

        return


