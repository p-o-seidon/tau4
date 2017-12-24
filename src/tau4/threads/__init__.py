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


from queue import Empty, Queue
import threading
import time

from tau4.data import pandora
from tau4.multitasking import threads as mtt
from tau4.sweng import PublisherChannel, Singleton


class _LoopMonitor:

    def __init__( self, looptime):
        self.__looptime = looptime

        self.__time = 0

        self.reset()
        return

    def looptime( self):
        return self.__looptime

    def looptime_remainder( self):
        return max( 0, (self.__looptime - (time.time() - self.__time)))

    def reset( self):
        self.__time = time.time()


class Thread(threading.Thread):

    def __init__( self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None, looptime=0.010):
        super().__init__( group, target, name, args, kwargs, daemon=daemon)

        self.__loopmonitor = _LoopMonitor( looptime)

        Threads().append( self)
        return

    def loopmonitor( self):
        return self.__loopmonitor

    def looptime( self):
        return self.__loopmonitor.looptime()


Cycler = mtt.CyclingThread


class Timer(mtt.CyclingThread):

    def __init__( self, cycletime, function):
        super().__init__( cycletime=cycletime, idata=None)

        self._function_ = function
        return

    def _run_( self, *args, **kwargs):
        self._function_()
        return


Threads = mtt.Threads

