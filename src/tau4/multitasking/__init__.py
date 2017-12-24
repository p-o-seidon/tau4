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

import abc
import threading

from tau4.multitasking import _multitasking


CycletimeMonitor = _multitasking._CycletimeMonitor


class RWLock:

    """Readers-Writers Lock.

    Lockt eine Shared Region (SR) folgendermaßen:

    -   Es kann sich nur ein Writer und kein Reader in der SR aufhalten.

    -   Es können sich beliebig viele Reader und kein Writer in der SR aufhalten.

    Funktioniert in MT-Umgebung. Ob's in MP-Umgebung funktioniert, weiß ich nicht.
    OTOH interessiert mich das eigentlich gar ncht, denn das MP-Abenteuer habe
    ich hinter mir - ist einfach Crap.

    \note
        Ist read-preferring.
    """

    class _Logger:

        def debug( self, *args):
            print( args[ 0] % args[ 1:])
            return


    class _DummyLogger(_Logger):

        def debug( self, *args):
            return


    def __init__( self, do_logging=False):
        self.__logger = self._Logger() if do_logging else self._DummyLogger()

        self.__lock = threading.Condition()
        self.__num_readers = 0
        self.__one_writer = False
        return

    def acquire_readaccess( self):
        _names = ( self.__class__.__name__, "acquire_readaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            while self.__one_writer:
                self.log( "%s.%s(), called by %s: Wait for lock (writer waiting). ", *_names)
                self.__lock.wait()

            self.__num_readers += 1
            self.log( "%s.%s(), called by %s: %d readers now. ", *_names, self.__num_readers)

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def acquire_writeaccess( self):
        _names = ( self.__class__.__name__, "acquire_writeaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            while self.__one_writer or self.__num_readers > 0:
                self.log( "%s.%s(), called by %s: Wait for lock (writers and/or readers waiting). ", *_names)
                self.__lock.wait()

            self.__one_writer = True
            self.log( "%s.%s(), called by %s: Writer has access now. ", *_names)

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def log( self, *args):
        self.__logger.debug( *args)
        return

    def release_readaccess( self):
        _names = ( self.__class__.__name__, "release_readaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            if self.__num_readers > 0:
                self.__num_readers -= 1
                self.log( "%s.%s(), called by %s: %d readers now. ", *_names, self.__num_readers)
                if self.__num_readers == 0:
                    self.log( "%s.%s(), called by %s: Notify all. ", *_names)
                    self.__lock.notify_all()

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def release_writeaccess( self):
        _names = ( self.__class__.__name__, "release_writeaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            self.__one_writer = False
            self.log( "%s.%s(), called by %s: Notify all. ", *_names)
            self.__lock.notify_all()

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return


class RWLockWritePreferring:

    """Readers-Writers Lock.

    Lockt eine Shared Region (SR) folgendermaßen:

    -   Es kann sich nur ein Writer und kein Reader in der SR aufhalten.

    -   Es können sich beliebig viele Reader und kein Writer in der SR aufhalten.

    -   Wartet ein Writer, so warten alle neuen Reader.

    Funktioniert in MT-Umgebung. Ob's in MP-Umgebung funktioniert, weiß ich nicht.
    OTOH interessiert mich das eigentlich gar ncht, denn das MP-Abenteuer habe
    ich hinter mir - ist einfach Crap.

    \note
        Ist write-preferring.

    \_2DO
        Testsuite schreiben! Hmm, aber wie testet man sowas?
    """

    class _Logger:

        def debug( self, *args):
            print( args[ 0] % args[ 1:])
            return


    class _DummyLogger(_Logger):

        def debug( self, *args):
            return


    def __init__( self, do_logging=False):
        self.__logger = self._Logger() if do_logging else self._DummyLogger()

        self.__lock = threading.Condition()
        self.__num_readers = 0
        self.__one_writer = False
        self.__num_writers_waiting = 0
        return

    def acquire_readaccess( self):
        _names = ( self.__class__.__name__, "acquire_readaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            while self.__one_writer or self.__num_writers_waiting > 0:
                self.log( "%s.%s(), called by %s: Wait for lock (writer waiting). ", *_names)
                self.__lock.wait()

            self.__num_readers += 1
            self.log( "%s.%s(), called by %s: %d readers now. ", *_names, self.__num_readers)

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def acquire_writeaccess( self):
        _names = ( self.__class__.__name__, "acquire_writeaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            self.__num_writers_waiting += 1
            while self.__one_writer or self.__num_readers > 0:
                self.log( "%s.%s(), called by %s: Wait for lock (writers and/or readers waiting). ", *_names)
                self.__lock.wait()

            self.__one_writer = True
            self.__num_writers_waiting += 1
            self.log( "%s.%s(), called by %s: Writer has access now. ", *_names)

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def log( self, *args):
        self.__logger.debug( *args)
        return

    def release_readaccess( self):
        _names = ( self.__class__.__name__, "release_readaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            if self.__num_readers > 0:
                self.__num_readers -= 1
                self.log( "%s.%s(), called by %s: %d readers now. ", *_names, self.__num_readers)
                if self.__num_readers == 0:
                    self.log( "%s.%s(), called by %s: Notify all. ", *_names)
                    self.__lock.notify_all()

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return

    def release_writeaccess( self):
        _names = ( self.__class__.__name__, "release_writeaccess", threading.current_thread().getName())
        self.log( "%s.%s(), called by %s: E n t e r e d. ", *_names)

        with self.__lock:
            self.__one_writer = False
            self.log( "%s.%s(), called by %s: Notify all. ", *_names)
            self.__lock.notify_all()

        self.log( "%s.%s(), called by %s: Exit now.\n", *_names)
        return


