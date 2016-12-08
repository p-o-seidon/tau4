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


from queue import Empty, Queue
import threading
import time

from tau4.data import flex
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
    
    
class Cycler(threading.Thread):
    
    """

    :param  cycletime:
        Cycle time in seconds.
        
    :param  udata:
        User data.
    """
    
    def __init__( self, *, cycletime, udata, is_daemon=True, startdelay=0):
        super().__init__( group=None, target=None, name=None, daemon=is_daemon)

        self.__cycletime = cycletime
        self.__udata = udata
        self.__startdelay = startdelay
        
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

        Threads().append( self)
        
        return
    
    def _ackn_to_app_( self):
        return self.__Q_ackn.put( 42)
        
    def cycletime( self):
        return self.__cycletime

    def _data_from_app_( self, timeout):
        try:
            return self.__Q_data.get( timeout=timeout)
    
        except Empty:
            return None
    
    def data( self, data, timeout):
        """App Data an den Cycler senden.
        """
        return self.__Q_data.put( data, timeout=timeout)
    
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

    def _request_start_( self, request_ackn=False):
        return self._request_( self._START_REQUEST, request_ackn)
    
    def _request_stop_( self, request_ackn=False):
        return self._request_( self._STOP_REQUEST, request_ackn)
    
    def _request_shutdown_( self, request_ackn=False):
        return self._request_( self._SHUTDOWN_REQUEST, request_ackn)
    
    def _request_( self, request, request_ackn=False):
        """App sendet Request an Cycler.
        """
        with self.__lock:
            self.__Q_request.put( (request, request_ackn))
            if request_ackn:
                self.__Q_ackn.get()
                
        return
    
    def _request_from_app_( self, timeout):
        try:
            return self.__Q_request.get( timeout=timeout)
            
        except Empty:
            return (None, False)
    
    def _run_( self, *, udata):
        raise NotImplementedError( "This class cannot handle an app's callable, it must be subclassed and this method must be overridden in the subclass!")
    
    def run( self):

        dt_admin = 0
        dt_user = 0
        is_running = False
        
        time.sleep( abs( self.__startdelay))
    
        while True:
            self._tau4p_on_cycle_beg_()
                                            # Auf   U s e r   warten.
            t_cyclestart = time.time()
            timeout = self.cycletime() - (dt_admin + dt_user)
            if timeout < 0:
                self._tau4p_on_cycletime_underflow_( idata=self.__udata)
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
                self._run_( udata=self.__udata)
                                                # Auf   U s e r   warten.
            self._tau4p_on_cycle_end_()
                                            # Auf   U s e r   warten.
            dt_user = time.time() - dt_user
                                            # Solange haben wir auf den User 
                                            #   gewartet
        return
    
    def start( self, request_ackn=False):
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
                
            return self._request_start_( request_ackn)
    
    def stop( self, request_ackn=False):
        """Send a stop request to the thread's body.
        
        You may start - stop - start - stop - etc. a thread and eventually 
        shutdown a thread. This means, that a stop plays the role of a pause 
        and a start plays the role of a resume - except for the first time 
        where it is a real start(up of the thread).
        """
        return self._request_stop_( request_ackn)
    
    def shutdown( self, request_ackn=False):
        """Send a shutdown request to the thread's body.
        
        You may start - stop - start - stop - etc. a thread and eventually 
        shutdown a thread. This means, that a stop plays the role of a pause 
        and a start plays the role of a resume - except for the first time 
        where it is a real start(up of the thread).
        """
        return self._request_shutdown_( request_ackn)

    
class Timer(Cycler):
    
    def __init__( self, cycletime, function):
        super().__init__( cycletime=cycletime, idata=None)
        
        self._function_ = function
        return

    def _run_( self, *args, **kwargs):
        self._function_()
        return
    
    
class Threads(list, metaclass=Singleton):
    
    def __init__( self, *args):
        self.__fv_count = flex.VariableDeMo( id="tau4.threads.count", value=0, value_min=None, value_max=None, label="# tau4threading.Threads", dim=None)
        return
    
    def append( self, *args):
        super().append( *args)
        self.__fv_count.value( len( self))
        return self
    
    def fv_count( self):
        """Anzahl Threads, die aktuell erzeugt worden sind.
        
        **Usage**::
        
            Threads().fv_count().reg_tau4s_on_modified( self._tau4s_on_threadcount_modified_)
        """
        return self.__fv_count

    def reg_tau4s_on_count_modified( self, tau4s):
        """
        
        **Usage**::
        
            Threads().reg_tau4s_on_count_modified( self._tau4s_on_threadcount_modified_)
        """
        return self.__fv_count.reg_tau4s_on_modified( tau4s)
    
    def shutdown( self, request_ackn=False):
        for thread in self:
            thread.shutdown( request_ackn=request_ackn)
            
        return