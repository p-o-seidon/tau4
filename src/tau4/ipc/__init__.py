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

import pickle
import time

from tau4.data import pandora
from tau4.multitasking.processes import CyclingProcess
from tau4.oop import overrides


class _ANotTooComplicatedClassForTests:

    def __init__( self, value):
        self.__value = value
        return

    def __repr__( self):
        return "%s( %s)" % (self.__class__.__name__, self.__value)


class _ProcessForTests(CyclingProcess):

    @overrides( CyclingProcess)
    def _run_( self, ipm):
        if ipm:
            print( "We got an IPM: '%s'. " % repr( ipm))

            if isinstance( ipm, StandardInterProcessMessages.TerminationRequest):
                print( "We got a termonation request!")

        else:
            pass

        return


def BoxesListToDict( boxeslist):
    d = {}
    for box in boxeslist:
        d[ str( box.id())] = box.value()

    return d

def DictToBoxesDict( d):
    boxesdict = {}
    for id in d:
        boxesdict[ str( id)] = pandora.Box( id=id, value=d[ str( id)])

    return boxesdict


class InterProcessMessage:

    """Base Class für alle Messages, die zwischen Prozessen ausgetauscht werden.
    """

    @staticmethod
    def FromPickle( objectpickle):
        return picle.loads( objectpickle)

    @staticmethod
    def FromRepr( objectrepr):
        return eval( objectrepr)


    def __init__( self, command: str=None):
        self.__command = command if command else self.__class__.__name__

        self.__data = None
        return

    def __repr__( self):
        return "%s( command='%s')" % (self.__class__.__name__, self.__command)

    def command( self):
        return self.__command

    def data( self, arg=None):
        if arg is None:
            return self.__data

        self.__data = arg
        return self

    def is_instance_of( self, cls):
        """Die Prüfung isinstance schlägt in MP-Umgebungen unter Umständen fehl, weshalb wir hier eine Namensprüfung vornehmen.
        """
        return self.__class__.__name__ == cls.__name__

    def _is_reprable_( self):
        return self == self.FromRepr( repr( self))

    def pickle( self):
        return pickle.dumps( self)


class StandardInterProcessMessages:

    class _AcknProcessStarted(InterProcessMessage):

        """Process veranlassen, den Start zu quittieren; INTERNAL USE ONLY.
        """

        pass


    class BoxesDict(InterProcessMessage):

        def __init__( self, dict):
            self.__dict = dict
            return

        def dict( self):
            return self.__dict


    class TerminationRequest(InterProcessMessage):

        """Process veranlassen, sich zu **geordnet** beenden (also ohne terminate() auszuführen).

        Usage:
            \code{.py}
                p = Process()
                p.start()
                :
                :
                :
                p.shutdown()
                p.join()

            \endcode
        """

        def __init__( self):
            super().__init__( "request for termination")
            return


    class EffectiveCycletimeRequest(InterProcessMessage):

        """Aufforderung an Process, die effektive Zykluszeit zu liefern und zwar direkt in dieser Message.

        Usage auf Process-Seite, was standardmäßig in tau4.multitasking.processes.Process eingebaut ist:
            \code{.py}
                def run( self):
                    from tau4 import ipc

                    time_message_got = time_loop_end = time.time()
                    cycletime_effective = self.__cycletime

                    while True:
                        time_loop_beg = time.time()

                        timeout = max( 0, self.__cycletime - (time_loop_end - time_message_got))
                        ipm = self._message_from_app_( timeout)

                        time_message_got = time.time()

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


                        self._run_( ipm)


                        time_loop_end = time.time()
                        cycletime_effective = time_loop_beg - time_loop_end

                    return
            \endcode
        """
        def __init__( self):
            super().__init__( "request for effective cycletime")

            self.__value = -1
            return

        def value( self, value=None):
            if value is None:
                return self.__value

            self.__value = value

            return self

    class ReadActualsRequest(InterProcessMessage):

        pass


    class WriteActuals(InterProcessMessage):

        pass


class InterProcessContainerMessage(InterProcessMessage):

    """Message, die zwischen Prozessen ausgetauscht werden kann.

    \param  command     Command an den Prozess, der an einer mp.Queue nicht
                        blockierend wartet.

    \param  objectlist  Liste von Objekten, die die Message enthält.
    """

    @staticmethod
    def FromRepr( repr):
        return eval( repr)


    def __init__( self, command, objectlist: list):
        assert isinstance( objectlist, (tuple, list))

        super().__init__( command)
        self.__objectlist = objectlist
        return

    def __iter__( self):
        for each in (self.command(), self.__objectlist):
            yield each

    def __repr__( self):
        return "%s( '%s', %s)" % (self.__class__.__name__, self.command(), repr( self.__objectlist))


def _lab_1_():
    def _wait_( secs):
        t = time.time()
        while time.time() - t <= secs:
            time.sleep( 0.100)

        return


    message = InterProcessContainerMessage( "read", (_ANotTooComplicatedClassForTests( 42), ))
    repr_from_message = repr( message)
    print( repr_from_message)

    message_from_repr = InterProcessContainerMessage.FromRepr( repr_from_message)
    assert repr( message) == repr( message_from_repr)

    process = _ProcessForTests( cycletime=0.010)
    process.start()

    process_2 = _ProcessForTests( cycletime=0.010)
    process_2.start()

    t = time.time()
    while time.time() - t <= 1.0:
        process.message( InterProcessContainerMessage( "some command", [_ANotTooComplicatedClassForTests( time.time())]))
        time.sleep( 0.005)

    process.message( StandardInterProcessMessages.EffectiveCycletimeRequest())
    ipm = process.message()
    print( "Cycletime of 'process' = %.3f s." % ipm.value())

    process.message( StandardInterProcessMessages.TerminationRequest())
    process.join()

    process_2.message( StandardInterProcessMessages.TerminationRequest())
    process_2.join()
    return


if __name__ == "__main__":
    import multiprocessing as mp

    mp.set_start_method( 'spawn')
    _lab_1_()
    input( "Press any key to exit...")