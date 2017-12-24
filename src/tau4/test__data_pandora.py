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


import time
import unittest

from tau4.timing import Timer2

from tau4.data import pandora
from tau4.data import pandora as p


class _TESTCASE__Box(unittest.TestCase):

    def _on_reference_changed_( self, publisherchannel):
        return

    def _on_reference_clipped_( self, publisherchannel):
        return


    def test__simple( self):
        """
        """
        print()

        ##  A box w/o an id
        #
        p_controlerror = p.Box( value=0.0, label="Control Error")
        p_controlerror.data( 42)
        self.assertTrue( float is type( p_controlerror.data()))
        self.assertAlmostEqual( 42.0, p_controlerror.data())

        p_controlerror.data( p_controlerror.data() + 1)
        self.assertTrue( float is type( p_controlerror.data()))
        self.assertAlmostEqual( 43.0, p_controlerror.data())

        return

    def test__monitoring( self):
        """
        """
        print()

        p_reference = p.Box( \
            label="Reference value", value=0.0, dim="U/min",
            plugins=(p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), )
            )

        p_reference.data( 42)
        return

    def test__filtering( self):
        """
        """
        print()

        class Filter(p.plugins.Plugin):

            def __init__( self, id):
                super().__init__( id)

            def process_data( self, data_new):
                data_old = self.data()
                data = data_new
                return data

        p_reference = p.Box( \
            label="Reference value", value=0.0, dim="U/min",
            plugins=(Filter( id="filter"), p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), )
            )
        return

    def test__monitoring_and_clipping( self):
        """
        """
        print()

        p.Shelf().pathname_ini( "./boxes.ini")

        p_vel = p.Box( \
            id="velocity", label="v", value=42.0, dim="m/s",
            plugins=(\
                p.plugins.Clipper4Numbers( id="clipper", callable=self._on_reference_clipped_, bounds=(-1, 1)),
                p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_)
            )
        )

        p_vel.data( -p_vel.data())
        self.assertAlmostEqual( -1, p_vel.data())

        p.Shelf().box_remove( p_vel)
        return

    def test__performance_when_creating( self):
        """
        """
        print()

        n = 10000
        with Timer2( "Creating most simple box") as t:
            for _ in range( n):
                p_aux = p.Box( value=0.0)

        print( t.results( timedivider=n))

        n = 10000
        with Timer2( "Creating monitored box") as t:
            for _ in range( n):
                p_aux = p.Box( value=0.0, plugins=(p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), ))

        print( t.results( timedivider=n))
        return

    def test__performance_when_writing( self):
        """
        """
        print()

        n = 10000
        p_aux = p.Box( value=0.0)
        with Timer2( "Writing to most simple box") as t:
            for _ in range( n):
                p_aux.data( 0.0)

        print( t.results( timedivider=n))

        i = n = 10000
        p_aux = p.Box( value=0.0, plugins=(p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), ))
        with Timer2( "Writing to monitored box") as t:
            while i:
                p_aux.data( 0.0)

                i -= 1

        print( t.results( timedivider=n))

        i = n = 10000
        p_aux = p.Box( \
            value=0.0,
            plugins=( \
                p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), p.plugins.Clipper4Numbers( id="clipper", bounds=(-1, 1), callable=self._on_reference_clipped_)
            )
        )
        with Timer2( "Writing to monitored clipping box") as t:
            while i:
                p_aux.data( i)

                i -= 1

        print( t.results( timedivider=n))
        return

    def test__performance_when_reading( self):
        """
        """
        print()

        n = 10000
        p_aux = p.Box( value=0.0)
        with Timer2( "Reading from most simple box") as t:
            for _ in range( n):
                p_aux.data()

        print( t.results( timedivider=n))

        n = 10000
        p_aux = p.Box( value=0.0, plugins=(p.plugins.Monitor( id="monitor", callable=self._on_reference_changed_), ))
        with Timer2( "Reading from monitored box") as t:
            for _ in range( n):
                p_aux.data()

        print( t.results( timedivider=n))
        return

    def test__persistence( self):
        """
        """
        print()

        pandora.Shelf().pathname_ini( "./boxes4unittest.ini")

        p_1 = pandora.Box( id="p_1", label="p_1", value=0.0)
        p_2 = pandora.Box( id="p_2", label="p_2", value=0.0)
        p_3 = pandora.Box( id="p_3", label="p_3", value=0.0)

        for p in (p_1, p_2, p_3):
            pandora.Shelf().store_box( p)

        for i, p in enumerate( (p_1, p_2, p_3)):
            p.data( i+1)
            self.assertAlmostEqual( i+1, p.data())


        self.assertAlmostEqual( 1, p_1.data())
        self.assertAlmostEqual( 2, p_2.data())
        self.assertAlmostEqual( 3, p_3.data())

        for p in (p_1, p_2, p_3):
            pandora.Shelf().store_box( p)

        self.assertAlmostEqual( 1, p_1.data())
        self.assertAlmostEqual( 2, p_2.data())
        self.assertAlmostEqual( 3, p_3.data())

        return


_Testsuite = unittest.makeSuite( _TESTCASE__Box)


class _TESTCASE__Plugin(unittest.TestCase):

    class Mapper4Joystick(p.plugins.Plugin):

        def __init__( self, id="mapper4joystick"):
            super().__init__( id=id)

            x1 = -100; y1 = -100; x2 = -10; y2 = 0
            self.__clipperLHS = p.plugins.Clipper4Numbers( id=id+".clipper.lhs", bounds=(x1, x2))
            self.__mapperLHS = p.plugins.Mapper4Numbers( id=id+".lhs", x1=x1, y1=y1, x2=x2, y2=y2)

            x1 = 10; y1 = 0; x2 = 100; y2 = 100
            self.__clipperRHS = p.plugins.Clipper4Numbers( id=id+".clipper.rhs", bounds=(x1, x2))
            self.__mapperRHS = p.plugins.Mapper4Numbers( id=id+".rhs", x1=x1, y1=y1, x2=x2, y2=y2)
            return

        def process_data( self, data):
            if data >= 0:
                if data < self.__clipperRHS.min():
                    data = 0.0
                    self.data( data)
                    return data

                data = self.__clipperRHS.process_data( data)
                data = self.__mapperRHS.process_data( data)
                self.data( data)
                return data

            if data > self.__clipperLHS.max():
                data = 0.0
                self.data( data)
                return data

            data = self.__clipperLHS.process_data( data)
            data = self.__mapperLHS.process_data( data)
            self.data( data)
            return data


    def test( self):
        """
        """
        print()

        mapper = self.Mapper4Joystick( "mapper4joystick")
        p.Shelf().plugin_add( mapper)
        self.assertRaises( KeyError, p.Shelf().plugin_add, mapper)
        box = p.Box( value=0.0, plugins=(mapper,))
        boxS = p.Box( value=0.0, plugins=(mapper,))

        with Timer2( "writing to mapping box") as timer:
            box.data( 50)

        print( timer.results())

        with Timer2( "writing to mapping box") as timer:
            box.data( 1)

        print( timer.results())

        self.assertAlmostEqual( 0, box.data())
        self.assertAlmostEqual( box.data(), p.Shelf().plugin( "mapper4joystick").data())

        box.data( 20)
        self.assertAlmostEqual( 11.11111111, box.data())
        self.assertAlmostEqual( box.data(), p.Shelf().plugin( "mapper4joystick").data())

        box.data( -20)
        self.assertAlmostEqual( -11.11111111, box.data())
        self.assertAlmostEqual( box.data(), p.Shelf().plugin( "mapper4joystick").data())

        with Timer2( "writing to vanilla box (no plugins)") as timer:
            box.data( 1)

        print( timer.results())

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Plugin))


class _TESTCASE__BoxServer(unittest.TestCase):

    def test( self):
        """
        """
        print()

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__BoxServer))


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



