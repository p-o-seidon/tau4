#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
#
#   This file is part of pandora.
#
#   pandora is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   pandora is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with pandora. If not, see <http://www.gnu.org/licenses/>.


import atexit
import multiprocessing as mp
import random
import threading
import time

from tau4.data import pandora
from tau4.oop import overrides, Singleton


class _BoxEssentials(object):

    """Daten, die über die Queues gehen.
    """

#    @staticmethod
#    def FromBox( box):
#        return _BoxEssentials( box.id(), box.value())


    def __init__( self, boxid, boxvalue):
        self.__items = (boxid, boxvalue)
        return

    def __repr__( self):
        return "%s( %s, %s)" % (self.__class__.__name__, *self.__items)

    def __iter__( self):
        """as_tuple().
        """
        for item in self.__items:
            yield item


class _CommandToServer(object):

    def __init__( self, command: str, boxessentails: _BoxEssentials):
        self.__command = command
        self.__boxessentials = boxessentails

        assert self.__command in ("r", "R", "w", "W")
        return

    def __repr__( self):
        return "%s( %s, %s)" % (self.__class__.__name__, self.__command, self.__boxessentials)

    def boxessentials( self):
        return self.__boxessentials

    def is_read( self):
        return self.__command in ("r", "R")

    def is_write( self):
        return self.__command in ("w", "W")


class _DictWithUniqueKeys(dict):

    """Dict aus Lists, das eine Exception wirft, wenn der Key nicht eindeutig ist.
    """

    def __setitem__( self, key, value):
        if key in self:
            raise KeyError( "_DictWithUniqueKeys::__setitem__(): Key '%s' already set!" % key)

        super().__setitem__( key, value)
        return


class _ListDictWithUniqueKeys(_DictWithUniqueKeys):

    """Dict aus Lists, das eine Exception wirft, wenn der Key nicht eindeutig ist.
    """

    def __getitem__( self, key):
        try:
            return super().__getitem__( key)

        except KeyError:
            L = []
            super().__setitem__( key, L)
            return L


class MPBoxC(pandora.Box):

    """

    Eine MPBoxS ist auf dem Server eindeutig. Jeder Prozess kann aber eine eigene
    MPBoxC anlegen, die mit der auf dem Server verbunden wird.

    Schreiben:
        Wert der MPBoxC geht über MÜ-Queue an Server-Prozess, der den Wert dann
        in die richtige MPBoxS schreibt.

    Lesen:
        MPBoxC-eigener Thread wartet an MP-Queue uf Änderungen und reagiert dann
        entsprechend.
    """

    def __init__( self, *, id, value, mpboxserver):
        super().__init__( id=id, value=value)

        self.__mpboxserver = mpboxserver

        self.__q_app_to_server = self.__mpboxserver.queue_app_to_server()
                                        # Eigentlich illegal...
        self.__q_server_to_app = self.__mpboxserver.queue_server_to_app()
                                        # Eigentlich illegal...
        self.__q_server_to_client = mp.Queue( -1)

        self.__watcherthread = threading.Thread( target=self._watching_)
        self.__watcherthread.setDaemon( True)
        self.__watcherthread.start()
        return

    def queue_server_to_client( self):
        return self.__q_server_to_client

    def reg_on_box_modified_on_server( self):
        self.__q_app_to_server = self.__mpboxserver.queue_app_to_server()
        self.__mpboxserver.reg_on_box_modified( self)
        return

    def value( self, arg=None):
        if arg is None:
            value = self._value_request_from_server_()
                                        # R-Command an Server und auf
                                        #   _BoxEssentials warten.
            super().value( value)
            return value

        self._value_to_server_( arg)
                                        # W-Command an Server
        super().value( arg)
        return self

    def _value_request_from_server_( self):
        """R-Command an Server, auf _BoxEssentials warten und Wert retournieren.
        """
        with self.__mpboxserver.lock():
            c2s = _CommandToServer( "r", _BoxEssentials( self.id(), 0.0))
            self.__q_app_to_server.put( c2s)
            boxessentials = self.__q_server_to_app.get()
            id, value = boxessentials

            return value

#    def _value_from_server_( self):
#        """
#        """
#        boxessentials = self.__q_server_to_app.get()
#        id, value = boxessentials
#
#        return value

    def _value_to_server_( self, value):
        be = _BoxEssentials( self.id(), self)
        c2s = _CommandToServer( "w", be)
        self.__q_app_to_server.put( c2s)
                                        # Server wartet an dieser Queue, nimmt Id
                                        #   und Wert und schreibt ihn in Box mit
                                        #   dieser Id.
                                        #
                                        #   Dann kommen Id und Wert in die Queue
                                        #   jener Prozesse, die sich angemeldet
                                        #   haben, um über Änderungen der Box mit
                                        #   dieser Id verständigt zu werden, und
                                        #   bei dieser Anmeldung eben auch eine
                                        #   Queue angegeben haben, an der sie
                                        #   einen Watcher-Thread warten lassen.
        return

    def _watching_( self):
        while True:
            boxessentials = self.__q_server_to_client.get()
            id, value = boxessentials
            super().value( self.__q_server_to_client.get())
                                            # Hier werden die Subscriber DIESES
                                            #   Prozesses ausgeführt.
        return


class MPBoxServer(mp.Process):

    """Server, der Box Instances verwaltet, um Zugriff füer Threads und Prozesse zu ermöglichen.
    """

    def __init__( self, q_app_to_server: mp.Queue, q_server_to_app: mp.Queue):
        super().__init__()

        queue_to_process = q_app_to_server
        queue_to_app = q_server_to_app
        self.__q_app_to_server = queue_to_process
        self.__q_server_to_app = queue_to_app

        self.__lock = mp.Lock()

        self.__boxes = _DictWithUniqueKeys()
        self.__queues_to_subscribers = _ListDictWithUniqueKeys()
        return

    def lock( self):
        return self.__lock

    def queue_app_to_server( self):
        return self.__q_app_to_server

    def queue_server_to_app( self):
        return self.__q_server_to_app

    def reg_on_box_modified( self, box):
        boxid = box.id()
        q = box.queue_server_to_client()
                                        # Eigentlich illegal...
        self.__queues_to_subscribers[ boxid].append( q)
        return

    def unreg_on_box_modified( self, boxid, queue):
        self.__queues_to_subscribers[ boxid].remove( queue)
        return

    def run( self):
        while True:
            command = self.__q_app_to_server.get()
            if command is None:
                break

            id, value = command.boxessentials()
            if command.is_read():
                if not id in self.__boxes:
                    box = pandora.Box( id=id, value=value)
                    self.__boxes[ id] = box

                value = self.__boxes[ id].value()
                self.__q_server_to_app.put( _BoxEssentials( id, value))

            elif command.is_write():
                if id in self.__boxes:
                    self.__boxes[ id].value( value)
                    queues = self.__queues_to_subscribers[ id]
                    for queue in queues:
                        queue.put( _BoxEssentials( id, value))

                else:
                    box = pandora.Box( id=id, value=value)
                    self.__boxes[ id] = box

            else:
                self.__q_server_to_app.put( None)

        return

    def start( self):
        super().start()
        return self

################################################################################
### Test
#
class ProcessOne(mp.Process):

    def __init__( self, bs: MPBoxServer):
        super().__init__()

        self.__mpboxserver = bs
        print( "ProcessOne::__init__(): mp.current_process() = %s. " % mp.current_process())
        return

    def run( self):
        this_name = self.__class__.__name__ + "_run_"

        print( "mp.current_process() = %s. " % mp.current_process())
        print( "id( pandora.Shelf() = %s. " % id( pandora.Shelf()))

        b = MPBoxC( id="box 1", value=0.0, mpboxserver=self.__mpboxserver)
        b.reg_on_box_modified_on_server()
        self.__mpboxserver.reg_on_box_modified( b)
        while True:
            print( this_name + "(): value = %s. " % b.value())
            b.value( b.value() + 1)

            time.sleep( 1.0)

        return

    def start( self):
        super().start()
        return self


class P1(mp.Process):

    def __init__( self, d):
        super().__init__()

        self.__d = d
        self.__shelf = self.__d[ "pandora.Shelf()"]
        return

    def run( self):
        this_name = self.__class__.__name__ + "_run_"

        print( "mp.current_process() = %s. " % mp.current_process())
        print( "id( pandora.Shelf() = %s. " % id( pandora.Shelf()))

        b1 = self.__shelf.box( "b1")
        while True:
            b1.value( b1.value() + 1)
                                            # Geht nicht
            time.sleep( 1.0)

        return

    def start( self):
        super().start()
        return self


class P2(mp.Process):

    def __init__( self, d):
        super().__init__()

        self.__d = d
        self.__shelf = self.__d[ "pandora.Shelf()"]
        return

    def run( self):
        this_name = self.__class__.__name__ + "_run_"

        print( "mp.current_process() = %s. " % mp.current_process())
        print( "id( pandora.Shelf() = %s. " % id( pandora.Shelf()))

        while True:
            self.__d[ "L"].append( "Hollodrio")
                                            # Geht auch nicht
            i = random.randint( 0, 1000)
            self.__d[ i] = i
                                            # Geht - ROFL
            time.sleep( 1.0)

        return

    def start( self):
        super().start()
        return self


class P3(mp.Process):

    def __init__( self, iaout):
        super().__init__()

        self.__iaout = iaout
        return

    def run( self):
        this_name = self.__class__.__name__ + "_run_"

        print( "mp.current_process() = %s. " % mp.current_process())
        print( "id( pandora.Shelf() = %s. " % id( pandora.Shelf()))

        while True:
            self.__iaout.value( self.__iaout.value() + 1).execute()

            time.sleep( 1.0)

        return

    def start( self):
        super().start()
        return self


def _lab_1_():
    q_app_to_server = mp.Queue()
    q_server_to_app = mp.Queue()

    bs = MPBoxServer( q_app_to_server, q_server_to_app).start()

    b = MPBoxC( id="box 1", value=42.0, mpboxserver=bs)
    print( "mp.current_process() = %s. " % mp.current_process())
    print( "id( pandora.Shelf() = %s. " % id( pandora.Shelf()))


    p = ProcessOne( bs).start()

    while True:
        value = b.value()
        if value % 5:
            b.value( b.value() * 5)

        print( "main(): value = %s. " % b.value())
        time.sleep( 1.0)


def _lab_2_():
    man = mp.Manager()
    shelf = pandora.Shelf()
    d = man.dict( {"pandora.Shelf()": shelf, "L": [1, 2, 3]})
    b1 = pandora.Box( id="b1", value=1.0)
    p2 = P2( d).start()

    while True:
        print( repr( b1))
                                        # Hier sollten wir sehen, wie der Wert
                                        #   wächst. Tut er aber nicht :-(((
        print( d)
                                        # Hier geht auch nicht alles :-((( Siehe P1.
        time.sleep( 1.0)

    return


def _lab_3_():
    from tau4.iios import iAOutMP

    iaout = iAOutMP( "aout 1", 1.0)

    p3 = P3( iaout).start()

    while True:
        iaout.execute()
        print( "iaout = %f. "% iaout.p_pin().value())

        time.sleep( 1.0)

    return


if __name__ == "__main__":

    mp.set_start_method( "spawn")

    _lab_1_()
#    _lab_2_()
#    _lab_3_()
