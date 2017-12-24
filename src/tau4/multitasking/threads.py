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
from queue import Empty, Full, Queue
import threading
import time


from tau4 import Object
from tau4.data import pandora
from tau4.multitasking import _multitasking
from tau4.oop import overrides, PublisherChannel, Singleton


class CyclingThread(Object, threading.Thread, metaclass=abc.ABCMeta):

    """Thread mit fester Cycle Time.

    :param  cycletime:
        <b>Default-Wert</b> der Zykluszeit in Sekunden. Der aktuelle Wert wird
        aus dem File "setup.ID.dat" gelesen. Existiert es nicht, wird es mit den
        Default-Werten angelegt.

    :param  udata:
        User data.

    \warning
        Fügt die kreierte Instanz dem Singleton Threads hinzu.

    """

    def __init__( self, *, id, cycletime, udata, is_daemon=True, startdelay=0):
        Object.__init__( self, id=id)
        threading.Thread.__init__( self, group=None, target=None, name=id, daemon=is_daemon)

        self.__cycletime = cycletime
        self.__udata = udata
        self.__startdelay = startdelay

        self.__cycletime_effective = 0.0
        self.__is_super_started = False

        self.__lock = threading.RLock()

        self._NO_REQUEST = 0
        self._START_REQUEST = 1
        self._STOP_REQUEST = 2
        self._SHUTDOWN_REQUEST = 3

        self.__Q_ackn = Queue( 1)
        self.__Q_data = Queue( 1)
        self.__Q_request = Queue( 1)

        self._tau4p_on_START_REQUEST_ = PublisherChannel.Synch( self)
        self._tau4p_on_STOP_REQUEST_ = PublisherChannel.Synch( self)
        self._tau4p_on_SHUTDOWN_REQUEST_ = PublisherChannel.Synch( self)
        self._tau4p_on_START_STOP_REQUEST_mismatch_ = PublisherChannel.Synch( self)

        self._tau4p_on_cycle_beg_ = PublisherChannel.Synch( self)
        self._tau4p_on_cycle_end_ = PublisherChannel.Synch( self)
        self._tau4p_on_cycletime_underflow_ = PublisherChannel.Synch( self)

        self.__cycletimemonitor = _multitasking._CycletimeMonitor( self.__class__.__name__, cycletime)

        Threads().append( self)

        return

    def _ackn_to_app_( self):
        return self.__Q_ackn.put( 42)

    def cycletime( self):
        return self.__cycletime

    def cycletime_effective( self):
        return self.__cycletime_effective

    def _data_from_app_( self, timeout):
        try:
            return self.__Q_data.get( timeout=timeout)

        except Empty:
            return None

    def data( self, data, timeout):
        """App Data an den Cycler senden.
        """
        return self.__Q_data.put( data, timeout=timeout)

    def on_cyclebeg( self):
        """zu überschreiben in Subclasses.
        """
        pass

    def on_cycleend( self):
        """zu überschreiben in Subclasses.
        """
        self.__cycletimemonitor.execute()
        return

    def reg_tau4s_on_START_REQUEST( self, tau4s):
        self._tau4p_on_START_REQUEST_ += tau4s

    def reg_tau4s_on_STOP_REQUEST( self, tau4s):
        self._tau4p_on_STOP_REQUEST_ += tau4s

    def reg_tau4s_on_SHUTDOWN_REQUEST( self, tau4s):
        self._tau4p_on_SHUTDOWN_REQUEST_ += tau4s

    def reg_tau4s_on_START_STOP_REQUEST_mismatch( self, tau4s):
        self._tau4p_on_START_STOP_REQUEST_mismatch_ += tau4s

    def reg_tau4s_on_CYCLE_BEG( self, tau4s):
        self._tau4p_on_cycle_beg_ += tau4s

    def reg_tau4s_on_CYCLE_END( self, tau4s):
        self._tau4p_on_cycle_end_ += tau4s

    def reg_tau4s_on_CYCLE_time_underflow( self, tau4s):
        self._tau4p_on_cycletime_underflow_ += tau4s

    def _request_start_( self, syncly=False):
        return self._request_( self._START_REQUEST, syncly)

    def _request_stop_( self, syncly=False):
        return self._request_( self._STOP_REQUEST, syncly)

    def _request_shutdown_( self, syncly=False):
        return self._request_( self._SHUTDOWN_REQUEST, syncly)

    def _request_( self, request, syncly=False):
        """App sendet Request an Cycler.
        """
        with self.__lock:
            self.__Q_request.put( (request, syncly))
            if syncly:
                self.__Q_ackn.get()

        return

    def _request_from_app_( self, timeout):
        try:
            return self.__Q_request.get( timeout=timeout)

        except Empty:
            return (None, False)

    @abc.abstractmethod
    def _run_( self, *, udata):
        raise NotImplementedError( "This class cannot handle an app's callable, it must be subclassed and this method must be overridden in the subclass!")

    def run( self):

        self.setup()

        dt_admin = 0
#        dt_user = 0
        dt_user = time.time()
        is_running = False

        time.sleep( abs( self.__startdelay))

        while True:
            t_cyclestart = time.time()
            self.on_cyclebeg()
            self._tau4p_on_cycle_beg_()

            dt_user = time.time() - dt_user
                                            # Solange haben wir auf den User
                                            #   gewartet
            timeout = self.cycletime() - (dt_admin + dt_user)
            if timeout < 0:
                self._tau4p_on_cycletime_underflow_( abs( timeout), idata=self.__udata)
                timeout = 0

            request, is_ackn_requested = self._request_from_app_( timeout=timeout)
                                                # Auf   A p p   warten.
            dt_admin = time.time()
            if request == self._START_REQUEST:
                if not is_running:
                    self._tau4p_on_START_REQUEST_( idata=self.__udata)
                    is_running = True
                    if is_ackn_requested:
                        self._ackn_to_app_()

                else:
                    self._tau4p_on_START_STOP_REQUEST_mismatch_()

            elif request == self._STOP_REQUEST:
                if is_running:
                    self._tau4p_on_STOP_REQUEST_( idata=self.__udata)
                    is_running = False
                    if is_ackn_requested:
                        self._ackn_to_app_()

                else:
                    self._tau4p_on_START_STOP_REQUEST_mismatch_()

            elif request == self._SHUTDOWN_REQUEST:
                self._tau4p_on_SHUTDOWN_REQUEST_( idata=self.__udata)
                is_running = False
                if is_ackn_requested:
                    self._ackn_to_app_()

                break

            dt_admin = time.time() - dt_admin
                                            # Solange haben wir für das
                                            #   Request Handling gebraucht
            dt_user = time.time()
            if is_running:
                with self.__cycletimemonitor.stopwatch_user():
                    self._run_( udata=self.__udata)
                                                    # Auf   U s e r   warten.
            self.on_cycleend()
            self._tau4p_on_cycle_end_()

#            dt_user = time.time() - dt_user
#                                            # Solange haben wir auf den User
#                                            #   gewartet
            self.__cycletime_effective = time.time() - t_cyclestart

        Threads().remove( self)
        return

    def setup( self):
        """Ausführung von Code in run(), bevor die Methode in die while-Schleife eintritt; zu überschreiben in Sub Classes.
        """
        pass

    def start( self, syncly=False):
        """Send a start request to the thread's body.

        You may start - stop - start - stop - etc. a thread and eventually
        shutdown a thread. This means, that a stop plays the role of a pause
        and a start plays the role of a resume - except for the first time
        where it is a real start(up of the thread).
        """
        with self.__lock:
            if not self.__is_super_started:
                super().start()
                self.__is_super_started = True

            return self._request_start_( syncly)

    def stop( self, syncly=False):
        """Send a stop request to the thread's body.

        You may start - stop - start - stop - etc. a thread and eventually
        shutdown a thread. This means, that a stop plays the role of a pause
        and a start plays the role of a resume - except for the first time
        where it is a real start(up of the thread).
        """
        return self._request_stop_( syncly)

    def shutdown( self, syncly=False):
        """Send a shutdown request to the thread's body.

        You may start - stop - start - stop - etc. a thread and eventually
        shutdown a thread. This means, that a stop plays the role of a pause
        and a start plays the role of a resume - except for the first time
        where it is a real start(up of the thread).
        """
        return self._request_shutdown_( syncly)


class Threads(list, metaclass=Singleton):

    def __init__( self, *args):
        self.__p_count = pandora.BoxMonitored( id="tau4.threads.count", value=0, label="# tau4.threads.Threads")
        return

    def append( self, *args):
        super().append( *args)
        self.__p_count.value( len( self))
        return self

    def p_count( self):
        """Anzahl Threads, die aktuell erzeugt worden sind.

        **Usage**::

            Threads().fv_count().reg_tau4s_on_modified( self._tau4s_on_threadcount_modified_)
        """
        return self.__p_count

    def reg_tau4s_on_count_modified( self, tau4s):
        """

        **Usage**::

            Threads().reg_tau4s_on_count_modified( self._tau4s_on_threadcount_modified_)
        """
        return self.__p_count.reg_tau4s_on_modified( tau4s)

    def shutdown( self, syncly=False):
        for thread in self:
            thread.shutdown( syncly=syncly)

        return