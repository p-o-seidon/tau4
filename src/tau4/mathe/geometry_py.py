#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2017
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


from copy import copy
#from euclid import Line2, LineSegment2, Point2
import itertools
from math import atan2, cos, degrees, radians, sin, sqrt
import numpy as np
import shapely
from shapely.geometry import LineString, LinearRing, Point, Polygon

from tau4.mathe.linalg import T3D, V3D


import pyximport; pyximport.install()
from tau4.mathe._geometry_cy import Matrix3x3MulMatrix3x3, Matrix3x3MulVector3


def _signum_( x):
    if x >= 0:
        return 1

    return -1


class Line2d:

    @staticmethod
    def Dot2( dot1, y2, k):
        """dot2 from dot1, the ordinate of dot2, and the slope of the line, that connects the two dots.

        Usage:
            \

            ::

                line = Line2( dot_actual, Line2d.Dot2( y2=42, k=13))

        Algorithm:
            \

            ::

                    y2 - y1
                k = -------
                    x2 - x1

                     y2 - y1
                x2 = ------- + x1
                        k
        """
        x1, y1 = dot1
        #k *= cmp( y2 - y1, 0)
        k *= _signum_( y2 - y1)
        x2 = (y2 - y1)/k + x1
        #assert x2 > x1
        # ##### 2013-12-27: Müsste doch erlaubt sein?
        return x2, y2


    def __init__( self, dot1, dot2):
        assert isinstance( dot1, (list, tuple))
        assert isinstance( dot2, (list, tuple))
        self.__dots = [list( dot1), list( dot2)]
        return

    def dot1( self, dot=None):
        if not dot:
            return self.__dots[ 0]

        self.__dots[ 0] = tuple( dot)
        return self

    def dot2( self, dot=None):
        if not dot:
            return self.__dots[ 1]

        self.__dots[ 1] = tuple( dot)
        return self

    def dots( self):
        return tuple( self.__dots)

    def dx( self):
        (x1, y1), (x2, y2) = self.__dots
        return x2 - x1

    def dy( self):
        (x1, y1), (x2, y2) = self.__dots
        return y2 - y1

    def k_sgn( self):
        (x1, y1), (x2, y2) = self.__dots
        k = (y2 - y1)/(x2 - x1)
        return k < 0

    def y( self, x):
        (x1, y1), (x2, y2) = self.__dots
        if not x1 <= x <= x2:
            return None

        k = (y2 - y1)/(x2 - x1)
        y = k*(x - x1) + y1
        return y


class Circle:

    """Kreis.

    Verwendung als Umkreis zur schnellen Prüfung auf Nearness.

    \param  T   Frame of the centre. All figures in mm.
    \param  r   Radius in mm

    Note::
        This works for spheres as well!
    """

    def __init__( self, T, r):
        self._T = T
        self._r = r
        return

    def is_intersecting( self, other):
        T = self._T.inverted() * other._T
                                        # This transform connects the two centre
                                        #   points. If its lebgth is smaller than
                                        #   the sum of the two radii, then the circles intersect
        return T.vnorm() <= self._r + other._r

    def r( self, dim="m"):
        return self._r if dim == "mm" else self._r/1000.0
    radius = r

    def x( self, dim="m"):
        return self._T.x() if dim == "mm" else self._T.x()/1000.0

    def y( self, dim="m"):
        return self._T.y() if dim == "mm" else self._T.y()/1000.0


class Circle2:

    """Kreis.

    Verwendung als Umkreis zur schnellen Prüfung auf Nearness.

    \param  T   Frame of the centre.
    \param  r   Radius.

    Note::
        This works for spheres as well!
    """

    def __init__( self, T, r):
        self._T = T
        self._r = r
        return

    def is_intersecting( self, other):
        T = self._T.inverted() * other._T
                                        # This transform connects the two centre
                                        #   points. If its lebgth is smaller than
                                        #   the sum of the two radii, then the circles intersect
        return T.vnorm() <= self._r + other._r

    def r( self, dim="m"):
        if dim == "m":
            return self._r

        if dim == "mm":
            return self._r*1000

        raise ValueError( "Unknown dim = '%s'. " % dim)
    radius = r

    def x( self, dim="m"):
        if dim == "m":
            return self._T.x()

        if dim == "mm":
            return self._T.x()*1000

        raise ValueError( "Unknown dim = '%s'. " % dim)

    def y( self, dim="m"):
        if dim == "m":
            return self._T.y()

        if dim == "mm":
            return self._T.y()*1000

        raise ValueError( "Unknown dim = '%s'. " % dim)


class Point2D:

    """2DO: Derive from V3D!
    """

    @staticmethod
    def FromOther( other, T3=T3D.FromEuler(), scale_x=1, scale_y=1):
        x, y = other
        x *= scale_x
        y *= scale_y
        x, y = (T3 * V3D( x, y)).xy()
        this = Point( x, y)
        return this


    def __init__( self, x=0, y=0):
        self.__coords = [ x, y]
        return

    def __eq__( self, other):
        """Compare the Point with a tuple.
        """
        if isinstance( other, (tuple, list)):
            return tuple( self.__coords) == tuple( other)

        return self.__coords == other.__coords

    def __getitem__( self, i):
        return self.__coords[ i]

    def __repr__( self):
        return "Point2D( %f, %f)" % tuple( self.__coords)

    def __setitem__( self, i, v):
        self.__coords[ i] = v
        return

    def __lshift__( self, other):
        if isinstance( other, (tuple, list)):
            self.__coords[ :] = other
            return self

        self.__coords[ :] = other.__coords
        return self

    def clipped( self, y_limits):
        x, y = self
        return self.__class__( x, y_limits.clipped( y))

    def x( self):
        return self.__coords[ 0]

    def y( self):
        return self.__coords[ 1]


class Point(shapely.geometry.Point):

    @staticmethod
    def FromT3D( t3d: T3D):
        return Point.FromV3D( t3d.P())


    @staticmethod
    def FromV3D( v3d: V3D):
        return Point( *v3d.coords())


    def __init__( self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        return

    def __getitem__( self, i):
        return self.comps()[ i]

    def __len__( self): # 2DO: Wieso müssen WIR das implementieren?
        return len( self.comps())

    def comps( self):
        """Components ofthe vector.
        """
        return self.coords[ 0]


class Polyline(LineString):

    pass


class Polygon(shapely.geometry.Polygon):

    def contains( self, other):
        if isinstance( other, T3D):
            return super().contains( Point.FromT3D( other))

        if isinstance( other, V3D):
            return super().contains( Point.FromV3D( other))

        return super().contains( other)

    def intersection( self, other):
        r = self.exterior.intersection( other)
        if isinstance( r, shapely.geometry.Point):
            return [ r]

        return r.geoms


class Rectangle:

    def __init__( self, Tr, w, h):
        self.__Tr = Tr
        self.__w = w
        self.__h = h

##        p = Tr.p()
##        self.__segments = ( \
##            ((p + (w/2, h/2)).xy(), (p + (-w/2, h/2)).xy()),
##            ((p + (-w/2, h/2)).xy(), (p + (-w/2, -h/2)).xy()),
##            ((p + (-w/2, -h/2)).xy(), (p + (w/2, -h/2)).xy()),
##            ((p + (w/2, -h/2)).xy(), (p + (w/2, h/2)).xy())
##        )
#        p = Tr.xyz()
#        self.__segments = ( \
#            (self._add_tuple_elemwise_( p, (w/2, h/2, 0)), self._add_tuple_elemwise_( p, (-w/2, h/2, 0))),
#            (self._add_tuple_elemwise_( p, (-w/2, h/2, 0)), self._add_tuple_elemwise_( p, (-w/2, -h/2, 0))),
#            (self._add_tuple_elemwise_( p, (-w/2, -h/2, 0)), self._add_tuple_elemwise_( p, (w/2, -h/2, 0))),
#            (self._add_tuple_elemwise_( p, (w/2, -h/2, 0)), self._add_tuple_elemwise_( p, (w/2, h/2, 0)))
#        )
        self.__segments = []

        P = Tr * V3D( w/2, h/2)
        Q = Tr * V3D( -w/2, h/2)
        self.__segments.append( (P.xyz(), Q.xyz()))

        P = Tr * V3D( -w/2, h/2)
        Q = Tr * V3D( -w/2, -h/2)
        self.__segments.append( (P.xyz(), Q.xyz()))

        P = Tr * V3D( -w/2, -h/2)
        Q = Tr * V3D( w/2, -h/2)
        self.__segments.append( (P.xyz(), Q.xyz()))

        P = Tr * V3D( w/2, -h/2)
        Q = Tr * V3D( w/2, h/2)
        self.__segments.append( (P.xyz(), Q.xyz()))

        return

    def __repr__( self):
        return u"Rectangle( T=%s; w=%.3f, h=%.3f)" % (self.__Tr, self.__w, self.__h)

    def _add_tuple_elemwise_( self, t1, t2):
        return tuple( map( lambda tt: sum( tt), zip( t1, t2)))

    def segments( self):
        return self.__segments


class Segment(LineString):

    @staticmethod
    def FromT3D( T1, T2):
        return Segment( (T1.P().coords(), T2.P().coords()))


class Intersection2D:

    @staticmethod
    def Segments( x1, y1, x2, y2, x3, y3, x4, y4):
        """Schneidet zwei Strecken im 2D und liefert den Schnittpunkt als Tuple.

        \note   Eine Strecke ist eine durch zwei Punkte begrenzte Gerade.
        """
        a = np.array( [[x2 - x1, x3 - x4], [y2 - y1, y3 - y4]])
        b = np.array( [x3 - x1, y3 - y1])
        try:
            x = np.linalg.solve( a, b)
            s, t = x
            if not (0 <= s <= 1 and 0 <= t <= 1):
                return None

            x = x1 + s*(x2 - x1)
            y = y1 + s*(y2 - y1)
            return (x, y)

        except np.linalg.LinAlgError:
            return None


    @staticmethod
    def SegmentRectangle( rectangle, x1, y1, x2, y2):
        """Liefert die Schnittpunkte.
        """
        intersections = []
        for (x3, y3, z3), (x4, y4, z4) in rectangle.segments():
            intersection = Intersection2D.Segments( x1, y1, x2, y2, x3, y3, x4, y4)
            if intersection:
                intersections.append( intersection)

        return intersections


class Sphere(Circle):

    def z( self, dim="m"):
        return self._T.z() if dim == "mm" else self._T.z()/1000.0


