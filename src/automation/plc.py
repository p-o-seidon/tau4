#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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


import logging; _Logger = logging.getLogger()

import abc, time

from tau4.data import flex
from tau4.io.hal import HAL4IOs
from tau4.sweng import overrides, PublisherChannel
from tau4.threads import Cycler


class PLC(Cycler, metaclass=abc.ABCMeta):
    
    """SPS.
    
    Eine SPS ist üblicherweise der "Schrittmacher" in Automatisierungslösungen.
    """

    class Job(metaclass=abc.ABCMeta):
        
        """Job, der innerhalb eines Zyklus auszuführen ist.
        
        Alle Jobs werden innerhalb ein und desselben Zyklus ausgeführt.
        
        **Zugriff auf die I/Os**:
            Die I/Os werden vo der PLC geselsen und geschrieben, sodass jeder 
            Job auf die mit dem I/O verbundene Variable zugreifen muss/darf.
            
            **Beispiel**::
                ### Eingang lesen
                #
                if HAL4IOs().dinps( 7).fv_raw().value():
                    DO_THIS()
                    
                else:
                    DO_THAT()
                
                ### Ausgang schreiben
                #
                HAL4IOs().douts( 7).fv_raw().value( 1)

        Ein Job kann alles Mögliche sein. Hier ein paar Beispiele:
        
        -   Schlüsselschalter lesen und Betriebsart umschalten, je nach Schlüsselschalterstellung.
        """
        
        _CYCLE_TIME = 0.050
        
        def __init__( self, plc, id, cycletime):
            self.__plc = plc
            self.__id = id if not id in (-1, None, "") else self.__class__.__name__
            self.__cycletime = cycletime
            self.__time_rem = cycletime
                
            return
        
        def cycletime( self):
            return self.__cycletime
    
        @abc.abstractmethod
        def execute( self):
            pass
        
        def id( self):
            return self.__id
        
        def plc( self):
            return self.__plc
            
        def rtime_decr( self, secs):
            """Decrease the remaining time until executed.
            """
            self.__time_rem -= secs
            return self
            
        def rtime( self):
            """Remaining time until executed.
            """
            return self.__time_rem
            
        def rtime_reset( self):
            """Reset remaining time until executed to cycle time again.
            """
            self.__time_rem = self.__cycletime
            return self
            
    
    class OperationMode:
        
        def __init__( self):
            self.__error = None
            self._tau4p_on_error = PublisherChannel.Synch( self)
            
            self.__varbl = flex.VariableDeMo( id="tau4.automation.PLC.operationmode", value="off", label="Op Mode", dim="")
            return
        
        def is_off( self, arg=None):
            value = "off"
            if arg is None:
                return self.__varbl.value() == value
            
            if arg:
                if not self.is_off():
                    self.__error = "Invalid op mode flow: %s to %s!" % (self.__varbl.value(), value)
                    self._tau4p_on_error()
                    self.__error = None
                    
                self.__varbl.value( value)
                
            else:
                raise ValueError( "You cannot switch off an operation mode, you only can choose a new one!")
                
            return self
        
        def is_on( self, arg=None):
            value = "on"
            if arg is None:
                return self.__varbl.value() == value
            
            if arg:
                if not self.is_off():
                    self.__error = "Invalid op mode flow: %s to %s!" % (self.__varbl.value(), value)
                    self._tau4p_on_error()
                    self.__error = None
                    
                self.__varbl.value( value)
                
            else:
                raise ValueError( "You cannot switch off an operation mode, you only can choose a new one!")
                
            return self
        
        def is_started( self, arg=None):
            value = "started"
            if arg is None:
                return self.__varbl.value() == value
            
            if arg:
                if not (self.is_on() or self.is_stopped()):
                    self.__error = "Invalid op mode flow: %s to %s!" % (self.__varbl.value(), value)
                    self._tau4p_on_error()
                    self.__error = None
                    
                self.__varbl.value( value)
                
            else:
                raise ValueError( "You cannot switch off an operation mode, you only can choose a new one!")
                
            return self
        
        def is_stopped( self, arg=None):
            value = "stopped"
            if arg is None:
                return self.__varbl.value() == value
            
            if arg:
                if not self.is_started():
                    self.__error = "Invalid op mode flow: %s to %s!" % (self.__varbl.value(), value)
                    self._tau4p_on_error()
                    self.__error = None
                    
                self.__varbl.value( value)
                
            else:
                raise ValueError( "You cannot switch off an operation mode, you only can choose a new one!")
                
            return self
        
    def __init__( self, *, cycletime_plc, cycletime_ios, is_daemon, startdelay=0):
        """
        
        :param  iainps:
            Appspez. interne I/Os. Müssen Hier angegeben werden, damit sie zur 
            richtigen Zeit execute()ed werden können. Definition und Ausführung 
            liegen völlig im Einflussbereich der App.
            
        Usage::
            2DO: Code aus iio hier her kopieren.
        """
        super().__init__( cycletime=cycletime_plc, idata=None, is_daemon=is_daemon)
        
        self.__jobs = []
        self.__jobindexes = dict( list( zip( [ job.id() for job in self.__jobs], list( range( len( self.__jobs))))))

        self.__operationmode = self.OperationMode()
        return
    
    def _inps_execute_( self):
        HAL4IOs().execute_inps()
        return
    
    def _outs_execute_( self):
        HAL4IOs().execute_outs()
        return

    @abc.abstractmethod    
    def _iinps_execute_( self):
        """Interne Inputs lesen.
        
        Beispiel::
            @overrides( automation.PLC)
            def _iinps_execute_( self):
                iIOs().idinps_plc().execute()
                return
        """
        pass
    
    @abc.abstractmethod    
    def _iouts_execute_( self):
        """Interne Outouts schreiben.
        
        Beispiel::
            @overrides( automation.PLC)
            def _iouts_execute_( self):
                iIOs().idouts_plc().execute()
                return
        """
        pass
    
    def job_add( self, job):
        if job.cycletime() < self.cycletime():
            raise ValueError( "Cycletime of Job '%s' must not be greater than %f, but is %f!" % (self.__class__.__name__, self.cycletime(), job.cycletime()))
        
        self.__jobs.append( job)
        self.__jobindexes = dict( list( zip( [ job.id() for job in self.__jobs], list( range( len( self.__jobs))))))        
        return self
        
    def jobs( self, id=None):
        if id is None:
            return self.__jobs
        
        return self.__jobs[ self.__jobindexes[ id]]
    
    def operationmode( self):
        return self.__operationmode
        
    def _run_( self, idata):
        ### Alle Eingänge lesen
        #
        self._inps_execute_()
        
        ### Alle internen Eingänge lesen
        #
        self._iinps_execute_()
        
        ### Jobs ausführen, wobei der erste Job immer das Lesen der INPs und 
        #   der letzte Job das Schreiben der OUTs ist.
        #
        jobs2exec = []
        for job in self.__jobs:
            job.rtime_decr( self.cycletime())
            if job.rtime() <= 0:
                jobs2exec.append( job)
                job.rtime_reset()
            
        for job in jobs2exec:
            job.execute()
        
        ### Alle Ausgänge schreiben
        #
        self._outs_execute_()
        
        ### Alle internen Ausgänge schreien
        #
        self._iouts_execute_()
        
        return
    
    
