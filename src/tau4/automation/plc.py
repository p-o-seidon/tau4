#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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


import abc
from collections import OrderedDict
import time

from tau4.timing import Timer
from tau4.automation.sm import SM, SMState
from tau4.data import flex
from tau4 import ios2
from tau4.sweng import overrides, PublisherChannel, Singleton
from tau4.threads import Cycler


class OpMode:

    class _Common(metaclass=Singleton):

        __switch_AUTO = False
        __switch_EMSTOP = False
        __switch_ENABLE = False
        __switch_ON = False
        __button_START = False
        __button_STOP = False


        def button_START( self, arg=None):
            if arg is None:
                return self.__button_START

            self.__button_START = arg
            return self

        def button_STOP( self, arg=None):
            if arg is None:
                return self.__button_STOP

            self.__button_STOP = arg
            return self

        def switch_AUTO( self, arg=None):
            if arg is None:
                return self.__switch_AUTO

            self.__switch_AUTO = arg
            return self

        def switch_EMSTOP( self, arg=None):
            if arg is None:
                return self.__switch_EMSTOP

            self.__switch_EMSTOP = arg
            return self

        def switch_ENABLE( self, arg=None):
            if arg is None:
                return self.__switch_ENABLE

            self.__switch_ENABLE = arg
            return self

        def switch_ON( self, arg=None):
            if arg is None:
                return self.__switch_ON

            self.__switch_ON = arg
            return self

        def switch_EMSTOP( self, arg=None):
            if arg is None:
                return self.__switch_EMSTOP

            self.__switch_EMSTOP = arg
            return self


    class EmStop(SMState):

        def condition_EMSTOP_IS_RELEASED( self):
            return not self.common().switch_EMSTOP()

        @overrides( SMState)
        def execute( self):
            super().execute()   # Nur zum Breakpoint-Setzen
            return

        @overrides( SMState)
        def value( self):
            return OpModeValues._EMSTOP


    class Off(SMState):

        def condition__SWITCH_ON_IS_ON( self):
            return self.common().switch_ON()

        def condition__EMSTOP_IS_PRESSED( self):
            return self.common().switch_EMSTOP()

        @overrides( SMState)
        def execute( self):
            super().execute()   # Nur zum Breakpoint-Setzen
            return

        @overrides( SMState)
        def value( self):
            return OpModeValues._OFF


    class On(SMState):

        def condition__SWITCH_AUTO_IS_OFF( self):
            return not self.common().switch_AUTO()

        def condition__SWITCH_AUTO_IS_ON( self):
            return self.common().switch_AUTO()

        def condition__SWITCH_ON_IS_OFF( self):
            return not self.common().switch_ON()

        def condition__EMSTOP_IS_PRESSED( self):
            return self.common().switch_EMSTOP()

        @overrides( SMState)
        def execute( self):
            super().execute()   # Nur zum Breakpoint-Setzen
            return

        @overrides( SMState)
        def value( self):
            return OpModeValues._ON


    class Manu:

        class Idle(SMState):

            def condition__SWITCH_AUTO_IS_OFF( self):
                return not self.common().switch_AUTO()

            def condition__SWITCH_AUTO_IS_ON( self):
                return self.common().switch_AUTO()

            def condition__SWITCH_ENABLE_IS_ON( self):
                return self.common().switch_ENABLE()

            def condition__SWITCH_ON_IS_OFF( self):
                return not self.common().switch_ON()

            def condition__EMSTOP_IS_PRESSED( self):
                return self.common().switch_EMSTOP()

            @overrides( SMState)
            def execute( self):
                super().execute()   # Nur zum Breakpoint-Setzen
                return

            @overrides( SMState)
            def value( self):
                return OpModeValues.MANU._IDLE


        class Ready(SMState):

            def condition__SWITCH_AUTO_IS_OFF( self):
                return not self.common().switch_AUTO()

            def condition__SWITCH_AUTO_IS_ON( self):
                return self.common().switch_AUTO()

            def condition__SWITCH_ENABLE_IS_OFF( self):
                return not self.common().switch_ENABLE()

            def condition__SWITCH_ON_IS_OFF( self):
                return not self.common().switch_ON()

            def condition__EMSTOP_IS_PRESSED( self):
                return self.common().switch_EMSTOP()

            @overrides( SMState)
            def execute( self):
                super().execute()   # Nur zum Breakpoint-Setzen
                return

            @overrides( SMState)
            def value( self):
                return OpModeValues.MANU._READY


    class Auto:

        class Idle(SMState):

            def condition__SWITCH_AUTO_IS_OFF( self):
                return not self.common().switch_AUTO()

            def condition__SWITCH_ENABLE_IS_OFF( self):
                return not self.common().switch_ENABLE()

            def condition__SWITCH_ENABLE_IS_ON( self):
                return self.common().switch_ENABLE()

            def condition__SWITCH_ON_IS_OFF( self):
                return not self.common().switch_ON()

            def condition__EMSTOP_IS_PRESSED( self):
                return self.common().switch_EMSTOP()

            @overrides( SMState)
            def execute( self):
                super().execute()   # Nur zum Breakpoint-Setzen
                return

            @overrides( SMState)
            def value( self):
                return OpModeValues.AUTO._IDLE


        class Ready(SMState):

            def close( self):
                if self.common().button_START():
                    self.common().button_START( False)

                super().close()
                return self

            def condition__BUTTON_START_IS_PRESSED( self):
                return self.common().button_START()

            def condition__SWITCH_AUTO_IS_OFF( self):
                return not self.common().switch_AUTO()

            def condition__SWITCH_AUTO_IS_ON( self):
                return self.common().switch_AUTO()

            def condition__SWITCH_ENABLE_IS_OFF( self):
                return not self.common().switch_ENABLE()

            def condition__SWITCH_ON_IS_OFF( self):
                return not self.common().switch_ON()

            def condition__EMSTOP_IS_PRESSED( self):
                return self.common().switch_EMSTOP()

            @overrides( SMState)
            def execute( self):
                super().execute()   # Nur zum Breakpoint-Setzen
                return

            @overrides( SMState)
            def value( self):
                return OpModeValues.AUTO._READY


        class Running(SMState):

            def close( self):
                if self.common().button_STOP():
                    self.common().button_STOP( False)

                super().close()
                return self

            def condition__BUTTON_STOP_IS_PRESSED( self):
                return self.common().button_STOP()

            def condition__SWITCH_AUTO_IS_OFF( self):
                return not self.common().switch_AUTO()

            def condition__SWITCH_AUTO_IS_ON( self):
                return self.common().switch_AUTO()

            def condition__SWITCH_ENABLE_IS_OFF( self):
                return not self.common().switch_ENABLE()

            def condition__SWITCH_ON_IS_OFF( self):
                return not self.common().switch_ON()

            def condition__EMSTOP_IS_PRESSED( self):
                return self.common().switch_EMSTOP()

            @overrides( SMState)
            def execute( self):
                super().execute()   # Nur zum Breakpoint-Setzen
                return

            @overrides( SMState)
            def value( self):
                return OpModeValues.AUTO._RUNNING




    def __init__( self):
        _SMSTable = {\
            self.Off(): \
                [ \
                    (self.Off().condition__SWITCH_ON_IS_ON, self.On()),
                    (self.Off().condition__EMSTOP_IS_PRESSED, self.EmStop()),
                ],

            self.On():
                [ \
                    (self.On().condition__SWITCH_AUTO_IS_ON, self.Auto.Idle()),
                    (self.On().condition__SWITCH_AUTO_IS_OFF, self.Manu.Idle()),
                ],

            self.Manu.Idle():
                [ \
                    (self.Manu.Idle().condition__SWITCH_AUTO_IS_ON, self.Auto.Idle()),
                    (self.Manu.Idle().condition__SWITCH_ENABLE_IS_ON, OpMode.Manu.Ready()),
                    (self.Manu.Idle().condition__SWITCH_ON_IS_OFF, self.Off()),
                ],

            OpMode.Manu.Ready():
                [ \
                    (OpMode.Manu.Ready().condition__SWITCH_AUTO_IS_ON, self.Manu.Idle()),
                    (OpMode.Manu.Ready().condition__SWITCH_ENABLE_IS_OFF, self.Manu.Idle()),
                    (OpMode.Manu.Ready().condition__SWITCH_ON_IS_OFF, self.Off()),
                ],

            OpMode.Auto.Idle():
                [ \
                    (OpMode.Auto.Idle().condition__SWITCH_ON_IS_OFF, OpMode.Off()),
                    (OpMode.Auto.Idle().condition__SWITCH_AUTO_IS_OFF, OpMode.Manu.Idle()),
                    (OpMode.Auto.Idle().condition__SWITCH_ENABLE_IS_ON, OpMode.Auto.Ready()),
                ],

            OpMode.Auto.Ready():
                [ \
                    (OpMode.Auto.Ready().condition__SWITCH_AUTO_IS_OFF, self.Auto.Idle()),
                    (OpMode.Auto.Idle().condition__SWITCH_ENABLE_IS_OFF, self.Auto.Idle()),
                    (OpMode.Auto.Ready().condition__SWITCH_ON_IS_OFF, self.Off()),
                    (OpMode.Auto.Ready().condition__BUTTON_START_IS_PRESSED, OpMode.Auto.Running()),
                ],

            OpMode.Auto.Running():
                [ \
                    (OpMode.Auto.Running().condition__SWITCH_AUTO_IS_OFF, OpMode.Auto.Ready()),
                    (OpMode.Auto.Running().condition__SWITCH_ENABLE_IS_OFF, OpMode.Auto.Ready()),
                    (OpMode.Auto.Running().condition__SWITCH_ON_IS_OFF, OpMode.Off()),
                    (OpMode.Auto.Running().condition__BUTTON_STOP_IS_PRESSED, OpMode.Auto.Ready()),
                ],

            OpMode.EmStop(): \
                [ \
                    (OpMode.EmStop().condition_EMSTOP_IS_RELEASED, OpMode.Off()),
                ],

        }

        self.__sm = SM( _SMSTable, self.Off(), self._Common())
        return

    ### Query the actual operation mode
    #
    def is_AUTO( self):
        return self.sm().smstate_current() is self.Auto()

    def is_AUTO_AND_READY( self):
        return self.sm().smstate_current() is OpMode.Auto.Ready()

    def is_AUTO_AND_RUNNING( self):
        return self.sm().smstate_current() is OpMode.Auto.Running()

    def is_OFF( self):
        return self.sm().smstate_current() is self.Off()

    def is_MANU( self):
        return self.sm().smstate_current() is self.Manu()

    def is_MANU_AND_READY( self):
        return self.sm().smstate_current() is OpMode.Manu.Ready()

    def is_ON( self):
        return self.sm().smstate_current() is self.On()

    ### Change the actual operation mode
    #
    def button_START( self, arg):
        self.sm().common().button_START( arg)
        return self

    def button_STOP( self, arg):
        self.sm().common().button_STOP( arg)
        return self

    def switch_AUTO( self, arg):
        self.sm().common().switch_AUTO( arg)
        return self

    def switch_ENABLE( self, arg):
        self.sm().common().switch_ENABLE( arg)
        return self

    def switch_ON( self, arg):
        self.sm().common().switch_ON( arg)
        return self

    def switch_EMSTOP( self, arg):
        self.sm().common().switch_EMSTOP( arg)
        return self

    ### Some queries besicdes the one about the iperation mode
    #
    def name( self):
        return self.sm().fv_smstatename_current().value()

    def sm( self):
        return self.__sm


class OpModeValues:

    _OFF = 0
    _ON = 1

    class MANU:

        _IDLE = 10
        _READY = 11


    class AUTO:

        _IDLE = 20
        _READY = 21
        _RUNNING = 22

    _EMSTOP = 9


class OpModeNameFinder(metaclass=Singleton):

    def name( self, value):
        return \
            {
                OpModeValues._OFF: "OFF",
                OpModeValues._ON: "ON",
                OpModeValues._EMSTOP: "EMSTOP",
                OpModeValues.MANU._IDLE: "MANU - IDLE",
                OpModeValues.MANU._READY: "MANU - READY",
                OpModeValues.AUTO._IDLE: "AUTO - IDLE",
                OpModeValues.AUTO._READY: "AUTO - READY",
                OpModeValues.AUTO._RUNNING: "AUTO - RUNNING",

            }[ value]


class PLC(Cycler, metaclass=abc.ABCMeta):

    """SPS.

    Eine SPS ist üblicherweise der "Schrittmacher" in Automatisierungslösungen.
    """

    def __init__( self, *, cycletime_plc, cycletime_ios, is_daemon, startdelay=0):
        """

        :param  iainps:
            Appspez. interne I/Os. Müssen Hier angegeben werden, damit sie zur
            richtigen Zeit execute()ed werden können. Definition und Ausführung
            liegen völlig im Einflussbereich der App.

        Usage::
            2DO: Code aus iio hier her kopieren.
        """
        super().__init__( cycletime=cycletime_plc, udata=None, is_daemon=is_daemon)

        self.__jobs = []
        self.__jobindexes = dict( list( zip( [ job.id() for job in self.__jobs], list( range( len( self.__jobs))))))

        self.__operationmode = OpMode()
        return

    def _inps_execute_( self):
        ios2.IOSystem().execute_inps()
        return

    def _outs_execute_( self):
        ios2.IOSystem().execute_outs()
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

    def operationmode( self) -> OpMode:
        return self.__operationmode

    def _run_( self, udata):
        ### Alle Eingänge lesen
        #
        self._inps_execute_()

        ### Alle internen Eingänge lesen
        #
        self._iinps_execute_()

        ### Jobs ausführen, wobei der erste Job immer das Lesen der INPs und
        #   der letzte Job das Schreiben der OUTs ist.
        #
        self.operationmode().sm().execute()

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

    def plc( self) -> PLC:
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




