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


import time
from timeit import default_timer

from tau4.threads import Thread

#from _4all import _settings


class Scheduler:

    """Führt Jobs zu bestimmten Zeitpunkten aus, die natürlich programmierbar sind.

    **Applikation**::

        def fun():
            DO SOME SERIOUS WORK HERE

        def another_fun():
            DO SOME SERIOUS WORK HERE

        sch = Scheduler( id="main", resolution_ms=10)
        sch.job_add( callable=fun, interval_ms=10)
        sch.job_add( callable=another_fun, interval_ms=100)
                                        # Die Reihenfolge der Aufrufe im Falle
                                        #   mehrerer "gleichzeitiger" Aufrufe ist
                                        #   definert durch die Reihenfolge, in der
                                        #   die callables hinzugefügt werden.
        sch.start()
        time.sleep( 1000)
        sch.stop()
    """

    class _Job:

        def __init__( self, *, interval_ms, callable, data4callable=None):
            self.__callable = callable
            self.__interval_ms = interval_ms
            self.__data4callable = data4callable

            self._time_to_execute_ms = self.__interval_ms
            return

        def execute( self):
            if self.__data4callable:
                return self.__callable( self.__data4callable)

            return self.__callable()

        def time_to_execute_is_elapsed( self):
            return self._time_to_execute_ms <= 0

        def time_to_execute_dec( self, ms):
            self._time_to_execute_ms -= ms
            return self

        def time_to_execute_reset( self):
            self._time_to_execute_ms = self.__interval_ms
            return self


    def __init__( self, *, id, resolution_ms):
        self.__id = id

        self.__time_last_executed = 0
        self.__interval_ms = resolution_ms

        self.__jobs = []
        self.__is_inhibited = True
        return

    def execute( self):
        """Diese Methode ist periodisch auszuführen, am besten alle resolution_ms() Millisekunden oder schneller.

        .. note::
            Die Ausführung von start() ist Voraussetzung!
        """
        if not self.__is_inhibited:
            now = time.time()
            ms = (now - self.__time_last_executed) * 1000
            for job in self.__jobs:
                job.time_to_execute_dec( ms=ms)
                if job.time_to_execute_is_elapsed():
                    job.execute()
                    job.time_to_execute_reset()

            self.__time_last_executed = now

        return self

    def job_add( self, callable, interval_ms):
        self.__jobs.append( self._Job( interval_ms=interval_ms, callable=callable))
        return self

    def reset( self):
        for job in self.__jobs:
            job.time_to_execute_reset()

        return self

    def resolution_ms( self):
        return self.__interval_ms

    def start( self):
        self.__is_inhibited = False
        self.__time_last_executed = time.time()
        return self

    def stop( self):
        self.__is_inhibited = True
        return self


class SchedulerThread(Thread):

    def __init__( self, *, id, looptime):
        super().__init__()

        self.__is_stop_request = False
        self.__scheduler = Scheduler( id=id, resolution_ms=looptime*1000)
        return

    def run( self):
        while not self.__is_stop_request:
            self.loopmonitor().reset()
            self.__scheduler.execute()
            time.sleep( self.loopmonitor().looptime_remainder())

        return

    def scheduler( self):
        return self.__scheduler

    def start( self):
        self.__scheduler.start()
        return super().start()

    def shutdown( self, request_ackn=False):
        self.__is_stop_request = True
        return


class Timer(object):

    """Zeitnehmer.
    """

    def __init__( self, verbose=False):
        self.__verbose = verbose

        self.__start = -1       
        self.__timer = default_timer
        self.__elapsed_ms = -1
        self.__elapsed_s = -1
        self.__elapsed_us = -1
        return

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

    def elapsed_us( self):
        return self.__elapsed_us


class Timer2(Timer):

    """Zeitnehmer mit detaillierterem "Dump".
    """

    def __init__( self, info_about_testee=None):
        super().__init__( False)

        self.__info_about_testee = info_about_testee

        self.__timer = default_timer
        return

    def __enter__( self):
        if self.__info_about_testee:
            print( "Timer(): Start timing '%s'..." % self.__info_about_testee)
            
        else:
            pass

        return super().__enter__()

    def __str__( self):
        return self.results()

    def elapsed_ms( self, divisor=1.):
        return super().elapsed_ms()/divisor

    def elapsed_s( self, divisor=1.):
        return super().elapsed_s()/divisor
    elapsed_time = elapsed_s

    def elapsed_us( self, divisor=1.):
        return super().elapsed_us()/divisor

    def results( self, divisor=1.):
        if self.__info_about_testee:
            return "Timer(): '%s' took %.3f s = %.3f ms = %.3f us. " \
                  % (self.__info_about_testee, self.elapsed_s( divisor), self.elapsed_ms( divisor), self.elapsed_us( divisor))
        
        return "Timer(): The timed operation took %.3f s = %.3f ms = %.3f us. " \
              % (self.elapsed_s( divisor), self.elapsed_ms( divisor), self.elapsed_us( divisor))


