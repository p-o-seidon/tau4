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

from PyQt5.QtCore import QPoint
from random import randint
import time
import unittest

import tau4
from tau4.time import Timer2


class _TESTCASE__Point2D_tau4_gemetry_py(unittest.TestCase):

    def test__performance( self):
        """
        """
        from tau4.mathe.geometry_py import Point2D
        print()

        ii = range( 1000)
        with Timer2( "Create tau4.geometry_py.Point2D.") as timer:
            points = [ Point2D( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite = unittest.makeSuite( _TESTCASE__Point2D_tau4_gemetry_py)


class _TESTCASE__Point2D_tau4_gemetry_cy(unittest.TestCase):

    def test__performance( self):
        """Slightly faster than the Python version.
        """
        from tau4.mathe.geometry_cy import Point2D
        print()

        ii = range( 1000)
        with Timer2( "Create tau4.geometry_cy.Point2D.") as timer:
            points = [ Point2D( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Point2D_tau4_gemetry_cy))


class _TESTCASE__Point2D_sympy(unittest.TestCase):

    def test__performance( self):
        """10 to 15 times slower than the tau4 version!
        """
        from sympy.geometry import Point2D
        print()

        ii = range( 1000)
        with Timer2( "Create sympy.geometry.Point2D.") as timer:
            points = [ Point2D( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Point2D_sympy))


class _TESTCASE__Point2_pyeuclid(unittest.TestCase):

    def test__performance( self):
        """As fast as tau4's variant, that is we  c o u l d  derive from tau4's Point2D from Point2.
        """
        from euclid import Point2
        print()

        ii = range( 1000)
        with Timer2( "Create pyeuclid.Point2.") as timer:
            points = [ Point2( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Point2_pyeuclid))


class _TESTCASE__QPoint(unittest.TestCase):

    def test__performance( self):
        """Slightly slower than tau4's Point2D
        """
        from tau4.mathe.geometry_cy import Point2D
        print()

        ii = range( 1000)
        with Timer2( "Create QtCore.QPoint.") as timer:
            points = [ QPoint( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__QPoint))


class _TESTCASE__Point_shapely(unittest.TestCase):

    def test__performance( self):
        """5 times slower than tau4's Point2D.
        """
        from shapely.geometry import Point
        print()

        ii = range( 1000)
        with Timer2( "Create shapely.geometry.Point.") as timer:
            points = [ Point( randint( -100, 100), randint( -100, 100)) for i in ii]

        print( timer.results( len( ii)))
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Point_shapely))


class _TESTCASE__pyeuclid(unittest.TestCase):

    def test__Line2( self):
        """
        """
        from euclid import Line2, Point2
        print()

        line1 = Line2( Point2( 0, 0), Point2( 0, 100))
        line2 = Line2( Point2( -100, 50), Point2( 100, 50))
        point = line1.intersect( line2)
        self.assertEqual( Point2( 0, 50), point)

        point = Line2( Point2( 0, 0), Point2( 0, 100)).intersect( Line2( Point2( 0, 50), Point2( 100, 50)))
        self.assertEqual( Point2( 0, 50), point)

        point = Line2( Point2( 0, 0), Point2( 0, 100)).intersect( Line2( Point2( 1, 50), Point2( 100, 50)))
        self.assertEqual( Point2( 0, 50), point)
                                        # This works, because it's a line and
                                        #   not a segment

        return

    def test__LineSegment2( self):
        """
        """
        from euclid import Line2, LineSegment2, Point2
        print()

        line1 = LineSegment2( Point2( 0, 0), Point2( 0, 100))
        line2 = LineSegment2( Point2( -100, 50), Point2( 100, 50))
        point = line1.intersect( line2)
        self.assertEqual( Point2( 0, 50), point)

        point = LineSegment2( Point2( 0, 0), Point2( 0, 100)).intersect( LineSegment2( Point2( 0, 50), Point2( 100, 50)))
        self.assertEqual( Point2( 0, 50), point)

        point = LineSegment2( Point2( 0, 0), Point2( 0, 100)).intersect( LineSegment2( Point2( 1, 50), Point2( 100, 50)))
        self.assertIsNone( point)

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__pyeuclid))


class _TESTCASE__shapely(unittest.TestCase):

    def test__polygon( self):
        """
        """
        from shapely.geometry import LinearRing, LineString
        from shapely.geometry import Point, Polygon
        print()

        polygon = LinearRing( ((0, 0), (100, 0), (100, 100), (0, 100)))

        ### Line intersects polygone
        #
        self.assertEqual( Point( 0, 50), polygon.intersection( LineString( ((-50, 50), (50, 50)))))
        self.assertTrue( polygon.intersection( LineString( ((-50, 50), (-5, 50)))).is_empty)
        points = polygon.intersection( LineString( ((-50, 50), (150, 50))))
        self.assertAlmostEqual( 2, len( points))
        self.assertEqual( Point( 0, 50), points[ 0])
        self.assertEqual( Point( 100, 50), points[ 1])
        self.assertAlmostEqual( 10, polygon.distance( Point( 10, 10)))
        self.assertAlmostEqual( 11, polygon.distance( Point( 10, -11)))

        ### LinearRing enclosed by polygon
        #
        self.assertFalse( polygon.contains( Point(10, 10)))
                                        # Liegt nicht auf dem Polygon
        self.assertFalse( Point( 10, 10).within( polygon))
                                        # Liegt nicht auf dem Polygon

        ### Polygon enclosed by polygon
        #
        polygon = Polygon( ((0, 0), (100, 0), (100, 100), (0, 100)))
        self.assertTrue( polygon.contains( Point(10, 10)))
                        # Liegt nicht auf dem Polygon
        self.assertTrue( Point( 10, 10).within( polygon))
                        # Liegt nicht auf dem Polygon

        return

    def test__polygon_assignment( self):
        """
        """
        from shapely.geometry import LinearRing, LineString
        from shapely.geometry import Point, Polygon
        print()

        p = Polygon( ((0, 0), (10, 0), (10, 10), (0, 10)))
        self.assertTrue( p.contains( Point( 9, 9)))
        q = Polygon( ((0, 0), (11, 0), (11, 11), (0, 11)))
        p.exterior._set_coords( q.exterior._get_coords())
        #self.assertTrue( p.contains( Point( 10, 10)))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__shapely))


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



