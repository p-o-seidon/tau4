#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2016
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


import time
from timeit import default_timer


class Timer(object):

    """Zeitnehmer.
    """

    def __init__( self, verbose=False):
        self.__verbose = verbose
        self.__timer = default_timer

    def __enter__( self):
        self.__start = self.__timer()
        return self

    def __exit__( self, *args):
        end = self.__timer()
        self.__elapsed_s = end - self.__start
        self.__elapsed_ms = self.__elapsed_s * 1000
        self.__elapsed_us = self.__elapsed_ms * 1000
        if self.__verbose:
            print( "Timer(): This operation took %.3f s = %.3f ms = %.3f us. " % (self.__elapsed_s, self.__elapsed_ms, self.__elapsed_us))

    def elapsed_ms( self):
        return self.__elapsed_ms

    def elapsed_s( self):
        return self.__elapsed_s
    elapsed_time = elapsed_s
    elapsed = elapsed_s

    def elapsed_us( self):
        return self.__elapsed_us


class Timer2(Timer):

    """Zeitnehmer mit detaillierterem "Dump".
    """

    def __init__( self, info_about_testee=None):
        Timer.__init__( self, False)

        self.__info_about_testee = info_about_testee

        self.__timer = default_timer

    def __enter__( self):
        if self.__info_about_testee:
            print( "Timer(): Start timing '%s'..." % self.__info_about_testee)
        else:
            pass

        return Timer.__enter__( self)

    def __str__( self):
        return self.results()

    def elapsed_ms( self, timedivider=1.):
        return Timer.elapsed_ms( self)/timedivider

    def elapsed_s( self, timedivider=1.):
        return Timer.elapsed_s( self)/timedivider
    elapsed_time = elapsed_s

    def elapsed_us( self, timedivider=1.):
        return Timer.elapsed_us( self)/timedivider

    def results( self, timedivider=1.):
        if self.__info_about_testee:
            return "%s(): '%s' took %.3f s = %.3f ms = %.3f us. " \
                  % (self.__class__.__name__, self.__info_about_testee, self.elapsed_s( timedivider), self.elapsed_ms( timedivider), self.elapsed_us( timedivider))
        return "%s(): The timed operation took %.3f s = %.3f ms = %.3f us. " \
              % (self.__class__.__name__, self.elapsed_s( timedivider), self.elapsed_ms( timedivider), self.elapsed_us( timedivider))


