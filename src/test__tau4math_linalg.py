#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by F. Geiger, 1998 - 2016
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

from math import *
from tau4.mathe.linalg import Vector3, T3D
import time
import unittest


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__Vector3(unittest.TestCase):

    def test__add( self):
        """
        """
        print()
        
        u = Vector3( 1, 2, 3)
        v = Vector3( -7, 8, 9)
        w = u + v
        self.assertAlmostEqual( Vector3( -6, 10, 12), w)
        return

    def test__ex( self):
        """
        """
        print()
        
        u = Vector3( 1, 2, 3)
        v = Vector3( -7, 8, 9)
        w = u.ex( v)
        self.assertAlmostEqual( Vector3( -6, -30, 22), w)
        return

    def test__dot( self):
        """
        """
        print()
        
        u = Vector3( 1, 2, 3)
        v = Vector3( -7, 8, 9)
        w = u.dot( v)
        self.assertAlmostEqual( 36, w)
        return

    def test__normalize( self):
        """
        """
        print()
        
        u = Vector3( 1, 2, 3)
        self.assertGreater( u.magnitude(), 1)
        self.assertAlmostEqual( 1, u.normalized().magnitude())

        v = Vector3( -7, 8, 9)
        self.assertGreater( v.magnitude(), 1)
        v.normalize()
        self.assertAlmostEqual( 1, v.magnitude())
        return

    def test__sub( self):
        """
        """
        print()
        
        u = Vector3( 1, 2, 3)
        v = Vector3( -7, 8, 9)
        w = u - v
        self.assertAlmostEqual( Vector3( 8, -6, -6), w)
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Vector3))


class _TESTCASE__T3D(unittest.TestCase):

    def test__alpha( self):
        """
        """
        print()
        
        wTb = T3D.FromEuler( 1000, 0, 0, radians( 90), 0, 0)
                                        # Eine BASE in der WORLD
        bTr = T3D.FromEuler( 1000, 0, 0, 0, 0, 0)
                                        # Ein ROBOT in der BASE
        wTr = wTb * bTr
                                        # Ein ROBOT in der WORLD
        self.assertAlmostEqual( 1000, wTr.x())
        self.assertAlmostEqual( 1000, wTr.y())
        self.assertAlmostEqual( 90, wTr.a( deg=True))
        self.assertAlmostEqual( pi/2, wTr.a())

        wTb = T3D.FromEuler( 1000, 0, 0, radians( -90), 0, 0)
                                        # Eine BASE in der WORLD
        bTr = T3D.FromEuler( 1000, 0, 0, 0, 0, 0)
                                        # Ein ROBOT in der BASE
        wTr = wTb * bTr
                                        # Ein ROBOT in der WORLD
        self.assertAlmostEqual( 1000, wTr.x())
        self.assertAlmostEqual( -1000, wTr.y())
        self.assertAlmostEqual( -90, wTr.a( deg=True))
        self.assertAlmostEqual( -pi/2, wTr.a())
        self.assertAlmostEqual( 270, wTr.a( deg=True, no_neg=True))
        self.assertAlmostEqual( 3*(2*pi)/4, wTr.a( no_neg=True))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__T3D))


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print
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



