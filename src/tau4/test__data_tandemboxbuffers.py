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


import tau4
import time
import unittest

from tau4.data.tandemboxbuffers import *
from tau4.multitasking import threads as mtt
from tau4.timing import Timer2


class MMI(mtt.CyclingThread):

    def __init__( self, cycletime):
        super().__init__( id="mmi", cycletime=cycletime, udata=None)

        self.__images = Images()

        self.__counter = 0
        return

    def couter( self):
        return self.__counter

    def on_cyclebeg( self):
        self.__images[ "plc"][ self.id()].inboxes_to_outboxes()
        self.__images[ "rc"][ self.id()].inboxes_to_outboxes()
        return

    def on_cycleend( self):
        self.__images[ self.id()].inboxes_to_outboxes()
        return

    def _run_( self, udata):
        self.__counter = self.__images[ "plc"][ self.id()].value( "counter@plc")
        return


class PLC(mtt.CyclingThread):

    def __init__( self, cycletime):
        super().__init__( id="plc", cycletime=cycletime, udata=None)

        self.__images = Images()

        self.__counter = 0
        return

    def couter( self):
        return self.__counter

    def on_cyclebeg( self):
        self.__images[ "mmi"][ self.id()].inboxes_to_outboxes()
        self.__images[ "rc"][ self.id()].inboxes_to_outboxes()
        return

    def on_cycleend( self):
        self.__images[ "plc"].inboxes_to_outboxes()
        return

    def _run_( self, udata):
        self.__counter += 1
        self.__images[ "plc"].value( "counter@plc", self.__counter)
        return


class RC(mtt.CyclingThread):

    def __init__( self, cycletime):
        super().__init__( id="rc", cycletime=cycletime, udata=None)

        self.__images = Images()

        self.__counter = 0
        return

    def couter( self):
        return self.__counter

    def on_cyclebeg( self):
        self.__images[ "plc"][ self.id()].inboxes_to_outboxes()
        return

    def on_cycleend( self):
        self.__images[ self.id()].inboxes_to_outboxes()
        return

    def _run_( self, udata):
        self.__counter = self.__images[ "plc"][ self.id()].value( "counter@plc")
        return


class _TESTCASE__Images(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        ### Alle Images aufbauen
        #
        images = Images( ("plc", "mmi", "rc", "any"))

        ### Value in die ImageCollection einhängen
        #
        images[ "plc"].value_add( "value.1", 1.0)
        self.assertAlmostEqual( 1.0, images[ "plc"].value( "value.1"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

        ### Value schreiben
        #
        images[ "plc"].value( "value.1", 42.0)
        self.assertAlmostEqual( 42.0, images[ "plc"].value( "value.1"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

        ### Sender "switcht"
        #
        images[ "plc"].inboxes_to_outboxes()

        ### Empfänger "switcht"
        #
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))
        images[ "plc"]["mmi"].inboxes_to_outboxes()

        ### Empfänger liest Wert
        #
        value = images[ "plc"][ "mmi"].value( "value.1")
        self.assertAlmostEqual( 42.0, images[ "plc"][ "mmi"].value( "value.1"))

        return


    def test__multithreaded_use( self):
        """
        """
        print()

        ### Alle Images aufbauen
        #
        images = Images( ("plc", "mmi", "rc", "any"))

        ### Value in die ImageCollection einhängen
        #
        images[ "plc"].value_add( "counter@plc", 1.0)
        self.assertAlmostEqual( 1.0, images[ "plc"].value( "counter@plc"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "counter@plc"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "rc"].value( "counter@plc"))

        ### Threads kreieren
        #
        mmi = MMI( cycletime=0.500)
        plc = PLC( cycletime=0.005)
        rc = RC( cycletime=0.010)

        ### Threads starten
        #
        mmi.start( syncly=True)
        plc.start( syncly=True)
        rc.start( syncly=True)

        ### Warten
        #
        t0 = time.time()
        while time.time() - t0 <= 5.0:
            time.sleep( 0.001)

        ### Threads stoppen
        #
        mmi.shutdown( syncly=True)
        plc.shutdown( syncly=True)
        rc.shutdown( syncly=True)

        ### Prüfen, wie weit wir gekommen sinnd
        #
        print( "MMI: counter = %d. " % mmi.couter())
        print( "PLC: counter = %d. " % plc.couter())
        print( "RC: counter = %d. " % rc.couter())

        return


    def test__performance( self):
        """
        """
        print()

        ### Alle Images aufbauen
        #
#        num_values = 10
#        images = Images( ("plc", "mmi", "rc"))

#        num_values = 100
#        images = Images( ("plc", "mmi", "rc"))

#        num_values = 100
#        images = Images( ("plc", "mmi", "rc", "any", "cu.1", "cu.2", "cu.3", "cu.4", "cu.5", "cu.6"))

        num_values = 100
        images = Images( ("plc", "mmi", "rc", "any", "cu.1", "cu.2", "cu.3", "cu.4", "cu.5", "cu.6") + tuple( ["cu.%d" % i for i in range( 7, 7+10)]))

        s = "%d images with %d values each." % (len( images), num_values)
        print( s); print( "-" * len( s))

        ### Values in den Sender aufnehmen
        #
        for i in range( num_values):
            images[ "plc"].value_add( "value.%d" % i, float( i))

        ### Sender schreibt Value
        #
        n = 1000
        with Timer2( "Writing value") as timer:
            for i in range( n):
                images[ "plc"].value( "value.1", 42.0)

        print( timer.results( n))

        ### Sender publisht Image
        #
        with Timer2( "Publishing image") as timer:
            for i in range( n):
                images[ "plc"].inboxes_to_outboxes()

        print( timer.results( n))

        ### Empfänger kopiert
        #
        with Timer2( "Copying image") as timer:
            for i in range( n):
                images[ "plc"][ "mmi"].inboxes_to_outboxes()

        print( timer.results( n))

        ### Empfänger liest Wert
        #
        with Timer2( "Reading value") as timer:
            for i in range( n):
                value = images[ "plc"][ "mmi"].value( "value.1")

        print( timer.results( n))

        return


_Testsuite = unittest.makeSuite( _TESTCASE__Images)


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


def _lab_():
    return


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


if __name__ == '__main__':
    _Test_()
    _lab_()
    input( u"Press any key to exit...")



