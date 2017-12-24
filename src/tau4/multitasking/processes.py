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


"""\package processing  Threads und Processes.

Synopsis:
    Unterstützung für Multithreading und Multiprocessing.

History:
    2017-08-15:
        \li Erstellt.
"""

import abc
import logging; _Logger = logging.getLogger()
import queue
import multiprocessing as mp
import os
import time

from tau4 import Id, Object
from tau4.datalogging import DefaultProcessLoggerConfiger
from tau4.multitasking import _multitasking
from tau4.oop import overrides


class CyclingProcess(mp.Process, metaclass=abc.ABCMeta):

    """Bauplan für Prozesse.
    """

    class Priority:

        _PRIO_LOW = 10
        _PRIO_VERY_LOW = 15
        _PRIO_LOWEST = 19
        _PRIO_NORMAL = 0
        _PRIO_HIGH = -10
        _PRIO_VERY_HIGH = -15
        _PRIO_HIGHEST = -20


    def __init__( self, *, id, cycletime: float, prio=Priority._PRIO_NORMAL):
        super().__init__()

        self.__id = id
        self.__cycletime = cycletime
        self.__niceness = prio

        self.__q_from_app = mp.Queue()
        self.__q_to_app = mp.Queue()
        self.__lock = mp.Lock()

        self.__cycletime_effective = self.__cycletime
        self.__num_cycles = 0
        self.__num_cycletimeexceedings = 0
        self.__cycletimemonitor = _multitasking._CycletimeMonitor( id, cycletime)

        self.__start_syncly = False

        self.daemon = True
        return

    def critical_section( self):
        """Lock der Kommunikation.

        Usage
            \code{.py}
                with paramserver.critical_region():
                    paramserver.message( IpmRequestPlatformname())
                    ipm = paramserver.message()

                print( ipm.data())
            \endcode
        """
        return self.__lock

    def cycletime( self):
        return self.__cycletime

    def cycletime_effective( self):
        return self.__cycletime_effective

    def id( self):
        return self.__id

    def _is_start_syncly_( self):
        return self.__start_syncly

    def message( self, ipm=None):
        """Message an Process oder von Process.

        \note   Erstaunlich eigentlich, dass das funktioniert: Die Queue wird beim
        Instanzieren des Process angelegt und nicht vom den Process erzeugenden
        Process an den Process übergeben. <b>Kann sein, dass das mal zu ändern ist.</b>
        """
        if ipm is None:
            return self.__q_to_app.get()

        self.__q_from_app.put( ipm)
        return

    def message_nowait( self, ipm=None):
        """Message an Process oder von Process.

        \note   Erstaunlich eigentlich, dass das funktioniert: Die Queue wird beim
        Instanzieren des Process angelegt und nicht vom den Process erzeugenden
        Process an den Process übergeben. <b>Kann sein, dass das mal zu ändern ist.</b>
        """
        try:                return self.__q_to_app.get_nowait()
        except queue.Empty: return None

    def _message_from_app_( self, timeout):
        try:                return self.__q_from_app.get( block=timeout > 0, timeout=timeout)
        except queue.Empty: return None

    def _message_to_app_( self, ipm):
        self.__q_to_app.put( ipm)
        return self

    def on_cyclebeg( self):
        """Ausführung am Beginn eines Zuyklus; zu überschreiben in Sub Classes.

        \note
            \li Ein abschießender Base-Cass Call ist angezeigt.
            \li Der LAufzeitbedarf dieser Methode wird in die Berechnung der
                effektiven Zyluszeit miteinbezogen
        """
        pass

    def on_cycleend( self):
        """Ausführung am Ende eines Zyklus; zu überschreiben in Sub Classes.

        \note
            \li Ein abschließender Base-Class Call ist **zwingend erforderlich**!
            \li Der Laufzeitbedarf dieser Methode wird in die Berechnung der
                effektiven Zykluszeit miteinbezogen
        """
        self.__num_cycles += 1
        self.__cycletimemonitor.execute()
        return

    def on_cycletime_exceeded( self, cycletime_effective):
        """Ausführung, wenn Zykluszeit um 10% überschritten wird; zu überschreiben in Sub Classes.

        \note
            \li Ein abschließender Base-Class Call ist angezeigt.
            \li Der Laufzeitbedarf dieser Methode wird in die Berechnung der
                effektiven Zykluszeit miteinbezogen
        """
        self.__num_cycletimeexceedings += 1
#        logging.warn( "Process '%s': cycletime_effective = '%.3f'. '%4.1f' %% cycletime exceedings detected so far. " \
#                      % (self.__id, cycletime_effective, self.__num_cycletimeexceedings/self.__num_cycles*100)
#                    )
        return

    def _q_from_app_( self):
        return self.__q_from_app

    @overrides( mp.Process)
    def run( self):
        from tau4 import ipc

        self.setup()

        if self.__start_syncly:
            self._message_to_app_( ipc.StandardInterProcessMessages._AcknProcessStarted())

        self.__cycletime_effective = self.__cycletime
        tolerance_cycletime_effective = 0.2 #0.1
        ipm = None

        os.nice( self.__niceness)

        while True:
            time_cyclestart = time.time()
                                            # Startpunkt für die Berechnung der
                                            #   Cycletime.
            if self.__cycletime_effective > self.__cycletime * (1.0 + tolerance_cycletime_effective):
                                            # Cycletime-Überschreitung um mehr als 10%
                self.on_cycletime_exceeded( cycletime_effective=self.__cycletime_effective)
                                                # Ausführung von User-Code bei
                                                #   Cycletime-Überschreitung
            self.on_cyclebeg()
                                            # Ausführung von User-Code am Beginn
                                            #   eines Cycles.
            if ipm and ipm.is_instance_of( ipc.StandardInterProcessMessages.TerminationRequest):
                                            # Termination Request.
                                            #
                                            # Anmerkung: Die Prüfung isinstance
                                            #   schlägt in MP-Umgebungen fehl, weshalb
                                            #   wir hier eine Namensprüfung vornehmen.
                break

            elif ipm and ipm.__class__.__name__ == ipc.StandardInterProcessMessages.EffectiveCycletimeRequest.__name__:
                self._message_to_app_( ipm.value( self.__cycletime_effective))

            else:
                pass


            self._run_( ipm) # U S E R
                                            # Ausführung des U s e r - C o d e s
                                            #   f ü r   d i e   N u t z l a s t
            self.on_cycleend()
                                            # Ausführung von User-Code am Ende
                                            #   eines Cycles.
            timeout = self.__cycletime - (time.time() - time_cyclestart)
            ipm = self._message_from_app_( timeout=timeout)
                                            # Warten auf InterProcessMessage. Warten
                                            #   nur, wenn timeout positiv ist,
                                            #   s. _message_from_app_().
            sleeptime = max( 0, self.__cycletime - (time.time() - time_cyclestart))
            if sleeptime > self.__cycletime * tolerance_cycletime_effective:
                                            # Weil time.sleep() nicht sehr genau
                                            #   zu sein scheint: Wir gehen nur
                                            #   schlafen, wenn sich's wirklich
                                            #   rentiert.
                time.sleep( sleeptime); print( "Going to sleep for %.f s. " % sleeptime)
                                                # Warten, bis die Cycletime
                                                #   vollständig abgelaufen ist.
            self.__cycletime_effective = time.time() - time_cyclestart
                                            # Effektive Cycletime.
        _Logger.critical( "%s.%s(): Exit now.\n", self.__class__.__name__, "run")
        return

    @abc.abstractmethod
    def _run_( self, ipm):
        raise RuntimeError( "You must override tua4.multitasking.Process._run_()!")

    def setup( self):
        """Ausführung von Code in run(), bevor die Methode in die while-Schleife eintritt; zu überschreiben in Sub Classes.
        """
        pass

    def shutdown( self, syncly=False):
        from tau4 import ipc
        self.message( ipc.StandardInterProcessMessages.TerminationRequest())

        if syncly:
            self.join()

        return

    def start( self, syncly=False):
        self.__start_syncly = syncly
        super().start()

        if self.__start_syncly:
            self.message()

        return self


class CyclicProcessIdentifiable(CyclingProcess):

    def __init__( self, *, id: Id, cycletime: float=0.010, prio=CyclingProcess.Priority._PRIO_NORMAL):
        super().__init__( cycletime, prio)
        return


class CyclicProcessLogging(CyclicProcessIdentifiable):

    def __init__( self, *, id: Id, cycletime: float, loggingconfer: DefaultProcessLoggerConfiger, prio=CyclingProcess.Priority._PRIO_NORMAL):
        super().__init__( id, cycletime, prio)

        self.__loggingconfer = loggingconfer
        return

    @overrides( CyclingProcess)
    def setup( self):
        self.__loggingconfer()

        super().setup()
        return


class JobHandlingProcess(CyclingProcess):

    def __init__( self, cycletime):
        super().__init__( cycletime)
        return

    @overrides( CyclingProcess)
    def run( self):
        from tau4 import ipc

        self.setup()

        cycletime_effective = self.__cycletime
        tolerance_cycletime_effective = 0.1
        ipm = None

        os.nice( self.__niceness)

        while True:
            time_cyclestart = time.time()
                                            # Startpunkt für die Berechnung der
                                            #   Cycletime.
            if cycletime_effective > self.__cycletime * (1.0 + tolerance_cycletime_effective):
                                            # Cycletime-Überschreitung um mehr als 10%
                self.on_cycletime_exceeded( cycletime_effective=cycletime_effective)
                                                # Ausführung von User-Code bei
                                                #   Cycletime-Überschreitung
            self.on_cyclebeg()
                                            # Ausführung von User-Code am Beginn
                                            #   eines Cycles.
            if ipm and ipm.is_instance_of( ipc.StandardInterProcessMessages.TerminationRequest):
                                            # Termination Request.
                                            #
                                            # Anmerkung: Die Prüfung isinstance
                                            #   schlägt in MP-Umgebungen fehl, weshalb
                                            #   wir hier eine Namensprüfung vornehmen.
                break

            elif ipm and ipm.__class__.__name__ == ipc.StandardInterProcessMessages.EffectiveCycletimeRequest.__name__:
                self._message_to_app_( ipm.value( cycletime_effective))

            else:
                pass


            self._run_( ipm) # U S E R
                                            # Ausführung des U s e r - C o d e s
                                            #   f ü r   d i e   N u t z l a s t
            self.on_cycleend()
                                            # Ausführung von User-Code am Ende
                                            #   eines Cycles.
            timeout = self.__cycletime - (time.time() - time_cyclestart)
            ipm = self._message_from_app_( timeout=timeout)
                                            # Warten auf InterProcessMessage
            sleeptime = max( 0, self.__cycletime - (time.time() - time_cyclestart))
            if sleeptime > self.__cycletime * tolerance_cycletime_effective:
                                            # Weil time.sleep() nicht sehr genau
                                            #   zu sein scheint.
                time.sleep( sleeptime)
                                                # Warten, bis die Cycletime
                                                #   vollständig abgelaufen ist.
            cycletime_effective = time.time() - time_cyclestart
                                            # Effektive Cycletime.
        return



class Job(abc.ABC):

    def __init__( self, cycletime):
        self.__cycletime = cycletime

        self.__process = None
        return

    def cycletime( self) -> float:
        return self.__cycletime

    @abc.abstractmethod
    def execute( self):
        pass

    def _process_( self, process: JobHandlingProcess):
        self.__process = process
        return self

    def process( self) -> JobHandlingProcess:
        return self.__process



