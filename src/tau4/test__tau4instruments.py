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


from __future__ import division

import logging; _Logger = logging.getLogger()

import tau4
import time
import unittest

from tau4.instruments.oscilloscopes.models import DataBuffer, Point, ScreenBuffer


class _TESTCASE__Point(unittest.TestCase):

    def test( self):
        """
        """
        print()
        
        p = _Point()
        self.assertEqual( (0, 0), p)
        self.assertEqual( p, (0, 0))
        
        q = _Point( 1, 2)
        p << q
        self.assertEqual( q, p)
        
        p = _Point()
        p[ 0] = 11
        p[ 1] = 12
        self.assertEqual( (11, 12), p)

        p << (13, 42)
        self.assertEqual( (13, 42), p)
        return
    

_Testsuite = unittest.makeSuite( _TESTCASE__Point)


class _TESTCASE__ScreenBuffer(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        db = DataBuffer( 100, (0, 100), (0, 100), (0, 0, 0))
        sb = ScreenBuffer( 10, 10, db)

        for i in range( sb.dx() + 1):
            print( (i, i))
            db.datapoint_add( (i, i))
            
        print()

        datapoints = db.datapoints()
        self.assertEqual( (0, 0), datapoints[ 0])
        self.assertEqual( (1, 1), datapoints[ 1])
        
        datapoints = sb.datapoints()
        self.assertEqual( (10.0, 0.0), next( datapoints))
        self.assertEqual( (9.0, 0.0), next( datapoints))
        self.assertEqual( (8.0, 0.0), next( datapoints))
        self.assertEqual( (7.0, 0.0), next( datapoints))
        self.assertEqual( (6.0, 0.0), next( datapoints))
        self.assertEqual( (5.0, 0.0), next( datapoints))
        self.assertEqual( (4.0, 1.0), next( datapoints))
        self.assertEqual( (3.0, 2.0), next( datapoints))
        self.assertEqual( (2.0, 3.0), next( datapoints))
        self.assertEqual( (1.0, 4.0), next( datapoints))
        self.assertEqual( (0.0, 5.0), next( datapoints))

        datapoints = sb.datapoints()
        self.assertEqual( (10.0, 0.0), next( datapoints))
        self.assertEqual( (9.0, 0.0), next( datapoints))
        self.assertEqual( (8.0, 0.0), next( datapoints))
        self.assertEqual( (7.0, 0.0), next( datapoints))
        self.assertEqual( (6.0, 0.0), next( datapoints))
        self.assertEqual( (5.0, 0.0), next( datapoints))
        self.assertEqual( (4.0, 1.0), next( datapoints))
        self.assertEqual( (3.0, 2.0), next( datapoints))
        self.assertEqual( (2.0, 3.0), next( datapoints))
        self.assertEqual( (1.0, 4.0), next( datapoints))
        self.assertEqual( (0.0, 5.0), next( datapoints))
        return


    def test__shifting_values( self):
        """
        """
        print()

        db = DataBuffer( 100, (1, 100), (0, 100), (0, 0, 0))
        sb = ScreenBuffer( 10, 10, db)

        for i in range( sb.dx() + 5 + 1):
            print( (i, i))
            db.datapoint_add( (i, i/2))
            
        print()

        datapoints = db.datapoints()
        self.assertEqual( (0, 0), datapoints[ 0])
        self.assertEqual( (1, 0.5), datapoints[ 1])

        ### The 1st time
        #
        datapoints = sb.datapoints()
        self.assertEqual( (10.0, 0.0), next( datapoints))
        self.assertEqual( (9.0, 0.0), next( datapoints))
        self.assertEqual( (8.0, 0.0), next( datapoints))
        self.assertEqual( (7.0, 0.0), next( datapoints))
        self.assertEqual( (6.0, 0.0), next( datapoints))
        self.assertEqual( (5.0, 0.0), next( datapoints))
        self.assertEqual( (4.0, 0.5), next( datapoints))
        self.assertEqual( (3.0, 1.0), next( datapoints))
        self.assertEqual( (2.0, 1.5), next( datapoints))
        self.assertEqual( (1.0, 2.0), next( datapoints))
        self.assertEqual( (0.0, 2.5), next( datapoints))
        self.assertRaises( StopIteration, next, datapoints)

        ### The 2nd time must of course yield the same 
        #
        datapoints = sb.datapoints()
        self.assertEqual( (10.0, 0.0), next( datapoints))
        self.assertEqual( (9.0, 0.0), next( datapoints))
        self.assertEqual( (8.0, 0.0), next( datapoints))
        self.assertEqual( (7.0, 0.0), next( datapoints))
        self.assertEqual( (6.0, 0.0), next( datapoints))
        self.assertEqual( (5.0, 0.0), next( datapoints))
        self.assertEqual( (4.0, 0.5), next( datapoints))
        self.assertEqual( (3.0, 1.0), next( datapoints))
        self.assertEqual( (2.0, 1.5), next( datapoints))
        self.assertEqual( (1.0, 2.0), next( datapoints))
        self.assertEqual( (0.0, 2.5), next( datapoints))
        self.assertRaises( StopIteration, next, datapoints)
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__ScreenBuffer))


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



