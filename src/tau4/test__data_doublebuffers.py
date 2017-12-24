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

from tau4.data.doublebuffers import *
from tau4.timing import Timer2


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        ### Alle Images aufbauen
        #
        images = Images( ("plc", "mmi", "rc", "any"))

        ### Value in die ImageCollection einhängen
        #
        images[ "plc"].add_value( "value.1", 1.0)
        self.assertAlmostEqual( 1.0, images[ "plc"].value( "value.1"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

        ### Value schreiben
        #
        images[ "plc"].value( "value.1", 42.0)
        self.assertAlmostEqual( 42.0, images[ "plc"]._value_( "value.1"))
        self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

        ### Sender "switcht"
        #
        images[ "plc"].flush()
        images[ "plc"]._switch_( dont_flush=True)

        ### Empfänger liest Wert
        #
        value = images[ "plc"][ "mmi"].value( "value.1")
        self.assertAlmostEqual( 42.0, images[ "plc"][ "mmi"].value( "value.1"))

        return


    def test__performance( self):
        """
        """
        print()

        ### Alle Images aufbauen
        #
#        num_values = 100
#        images = Images( ("plc", "mmi", "rc", "any", "cu.1", "cu.2", "cu.3", "cu.4", "cu.5", "cu.6"))
        num_values = 100
        images = Images( ("plc", "mmi", "rc"))

        ### Values in die ImageCollection einhängen
        #
        for i in range( num_values):
            images[ "plc"].add_value( "value.%d" % i, float( i))

        ### Value schreiben
        #
        n = 1000
        with Timer2( "Writing value") as timer:
            for i in range( n):
                images[ "plc"].value( "value.1", 42.0)

        print( timer.results( n))

        ### Sender "flusht"
        #
        with Timer2( "Flushing master image") as timer:
            for i in range( n):
                images[ "plc"].flush()

        print( timer.results( n))

        ### Sender "switcht"
        #
        with Timer2( "Switching all images") as timer:
            for i in range( n):
                images[ "plc"]._switch_( dont_flush=True)

        print( timer.results( n))

        ### Empfänger "switcht"
        #
        with Timer2( "Switching one image") as timer:
            for i in range( n):
                images[ "plc"][ "mmi"].switch()

        print( timer.results( n))

        ### Empfänger liest Wert
        #
        with Timer2( "Reading value") as timer:
            for i in range( n):
                value = images[ "plc"][ "mmi"].value( "value.1")

        print( timer.results( n))

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


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



