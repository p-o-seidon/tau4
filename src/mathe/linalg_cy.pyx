#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2015
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
import itertools
from math import atan2, cos, degrees, pi, radians, sin, sqrt
import numpy as np


cdef _signum_( double x):
    if x >= 0:
        return 1
    
    return -1


cdef _tuples_to_tuple_( tuples):
    t = tuple( itertools.chain.from_iterable( tuples))
    assert isinstance( t, tuple)
    return t


cdef class Matrix3x3:

    cdef:
        object  __elems
    
    
    def __init__( self, *rows):
        if not rows:
            rows = ((0,)*3,)*3
            
        assert isinstance( rows, tuple)
        
        self.__elems = [ 0]*9
        self.__elems[ :] = [ elem for elem in _tuples_to_tuple_( rows)]
        return
    
    def __richcmp__( self, Matrix3x3 other, int op):
        if op == 2: # ==
            if len( self.elems()) != len( other.elems()):
                return False
                
            for i in range( len( self.elems())):
                if self.elems()[ i] != other.elems()[ i]:
                    return False
                    
            return True
                
        elif op == 3: # !=
            return not self == other
            
        raise ValueError( u"Unknown op = %d. " % op)
    
    def __getitem__( self, ij):
        i, j = ij
        return self.__elems[ (i - 1)*3 + j - 1]
    
    def __lshift__( self, other):
        self.elems()[:] = other.elems()[:9]
        assert self.num_elems() == 9
        return self
    
    def __mul__( self, other):
        if isinstance( other, Matrix3x3):
            M = self.__class__( *((0,)*3,)*3)
            for i in (1, 2, 3):
                for j in (1, 2, 3):
                    s = 0
                    for k in (1, 2, 3):
                        s += self[ i, k] * other[ k, j]
                    
                    M[ i, j] = s
            
            return M
        
        if isinstance( other, Vector3):
            v1, v2, v3 = other.elems()
            return Vector3( self[ 1, 1]*v1 + self[ 1, 2]*v2 + self[ 1, 3]*v3, self[ 2, 1]*v1 + self[ 2, 2]*v2 + self[ 2, 3]*v3, self[ 3, 1]*v1 + self[ 3, 2]*v2 + self[ 3, 3]*v3)
        
        elems = [elem*other for elem in self.elems()]
        return self.__class__( *zip( *[ iter( elems)] * 3))

    def __neg__( self):
        return self*(-1)
    
    def __setitem__( self, ij, v):
        i, j = ij
        self.__elems[ (i - 1)*3 + j - 1] = v
        assert self.num_elems() == 9
        
    cpdef elems( self):
        return self.__elems
    
    cpdef int num_elems( self):
        return len( self.__elems)
        
    cpdef inverted( self):
        raise NotImplementedError()
    
    cpdef Matrix3x3 transposed( self):
        cdef:
            int i, j
            Matrix3x3 tM
        
        tM = self.__class__()
        for i in (1, 2, 3):
            for j in (1, 2, 3):
                tM[ i, j] = self[ j, i]
                
        return tM
    
    
cdef class Vector3:
    
    cdef:
        object  __elems
        
        
    def __init__( self, double v1=0, double v2=0, double v3=0):
        """Ctor.
        
        v3=0 erleichtert die Verwendung im 2D.
        """
        self.__elems = [v1, v2, v3]
        return

    def __add__( self, other):
        v1, v2, v3 = self.elems()

        if isinstance( other, tuple):
            w1, w2 = other[ :2]
            w3 = other[ 3] if len( other) == 3 else 0
            return Vector3( v1 + w1, v2 + w2, v3 + w3)
        
        if isinstance( other, (float, int)):
            return Vector3( v1 + other, v2 + other, v3 + other)
            
        try:
            w1, w2, w3 = other.elems()
            
        except AttributeError:
            raise TypeError( "Adding a '%s' to a Vector3 doesn't seem to make sense!" % type( other))
            
        return Vector3( v1 + w1, v2 + w2, v3 + w3)
        
    def __div__( self, k):
        if not isinstance( k, (int, float)):
            raise TypeError( "Can only divide '%s' by a number, but got a '%s'!" % (self.__class__.__name__, type( k)))
            
        x, y, z = self.elems()
        return Vector3( x/k, y/k, z/k)
    
    def __richcmp__( self, other, op):
        if not isinstance( other, Vector3):
            raise TypeError( "Can only compare two Vector3, but other is a '%s' (value: '%s')!" % (type( other), other))
            
        if op == 2: # ==
            return self.elems() == other.elems()
    
        elif op == 3: # !=
            return not self == other
            
        raise ValueError( u"Unknown op = %d. " % op)
    
    def __getitem__( self, i):
        """ACHTUNG: Wir arbeiten hier 1-basierend!!!
        """
        return self.__elems[ i - 1]
    
    def __lshift__( self, other):
        self.elems()[:] = other.elems()[:3]
        return self

    def __repr__( self):
        return u"[%.3f, %.3f, %.3f]" % tuple( self.__elems)
    
    def __setitem__( self, i, v):
        """ACHTUNG: Wir arbeiten hier 1-basierend!!!
        """
        self.__elems[ i - 1] = v
        
    def __sub__( self, other):
        v1, v2, v3 = self.elems()

        if isinstance( other, tuple):
            w1, w2 = other[ :2]
            w3 = other[ 3] if len( other) == 3 else 0
            return Vector3( v1 - w1, v2 - w2, v3 - w3)
        
        if isinstance( other, (float, int)):
            return Vector3( v1 - other, v2 - other, v3 - other)
            
        w1, w2, w3 = other.elems()
        return Vector3( v1 - w1, v2 - w2, v3 - w3)
        
    cpdef double    a( self):
        """Winkel um Z-Achse.
        """
        cdef:
            double  x, y, z, a
        
        x, y, z = self.__elems
        a = atan2( y, x)
        if a < 0:
            a += 2*pi
            
        return a
    
    cpdef           coords( self):
        return self.__elems
    
    elems = coords
            
    cpdef double    dot( self, other):
        if not isinstance( other, Vector3):
            raise TypeError( "Can only dot two Vector3, but other is a '%s' (value: '%s')!" % (type( other), other))
            
        x, y, z = self.__elems
        u, v, w = other.elems()
        return x*u + y*v + z*w
        
    cpdef Vector3   ex( self, other):
        a1, a2, a3 = self.__elems
        b1, b2, b3 = other.elems()        
        return Vector3( a2*b3 - a3*b2, a3*b1 - a1*b3, a1*b2 - a2*b1)

    cpdef double    mag( self):
        cdef:
            double  v1, v2, v3
        
        v1, v2, v3 = self.__elems
        return sqrt( v1*v1 + v2*v2 + v3*v3)
    
    cpdef double    magnitude( self):
        cdef:
            double  v1, v2, v3
        
        v1, v2, v3 = self.__elems
        return sqrt( v1*v1 + v2*v2 + v3*v3)
    
    cpdef           normalize( self):
        k = self.mag()
        for i in (0, 1, 2):
            self.__elems[ i] /= k
            
        return None
        
    cpdef Vector3   normalized( self):
        x, y, z = self.__elems
        k = self.mag()
        return Vector3( x/k, y/k, z/k)
        
    cpdef double    x( self):
        return self[ 1]
    
    cpdef tuple     xy( self):
        return self.__elems[ 0], self.__elems[ 1]

    cpdef tuple     xyz( self):
        return self.__elems[ 0], self.__elems[ 1], self.__elems[ 2]

    cpdef double    y( self):
        return self[ 2]
    
    cpdef double    z( self):
        return self[ 3]
    
    
cdef class R3D(Matrix3x3):

    """Rotationsmatrix.
    
    Wir nennen diese Klasse R3D und nicht R3, um anzuzeigen, dass es sich um die 
    Beschreibung im Raum handelt. R3 wäre ohnehin falsch, es müsste R3x3 heißen.
    """

    cdef:
        tuple __euler

    
    @staticmethod
    def FromEuler( alpha=0, beta=0, gamma=0):
        return R3DFromEuler( alpha, beta, gamma)
    
    @staticmethod
    def FromVectors( Vector3 ex, Vector3 ey, Vector3 ez):
        return R3DFromVectors( ex, ey, ez)
    
    def __init__( self, *rows):
        Matrix3x3.__init__( self, *rows)
        if not rows:
            self << R3D.FromEuler( 0, 0, 0)
            
        self.__euler = None
        return
    
    cpdef tuple euler( self):
        cdef:
            double r11, r12, r13, r21, r22, r23, r31, r32, r33
            double alpha, beta, gamma
            double cb
        
        if self.__euler is None:
            r11, r12, r13, r21, r22, r23, r31, r32, r33 = self.elems()
            beta = atan2( -r31, sqrt( r11*r11 + r21*r21))
            cb = cos( beta)
            if cb != 0:
                alpha = atan2( r21/cb, r11/cb)
                gamma = atan2( r32/cb, r33/cb)
                
            else:
                if beta > 0:
                    alpha = 0
                    gamma = atan2( r12, r22)
                    
                else:
                    alpha = 0
                    gamma = -atan2( r12, r22)
                    
            self.__euler = (alpha, beta, gamma)

        return self.__euler
        

cpdef R3D   R3DFromEuler( double alpha=0, double beta=0, double gamma=0):
    cdef:
        double  ca, cb, cg, sa, sb, sg, r11, r12, r13, r21, r22, r23, r31, r32, r33
        
    ca = cos( alpha)
    cb = cos( beta)
    cg = cos( gamma)
    sa = sin( alpha)
    sb = sin( beta)
    sg = sin( gamma)
    r11 = ca*cb
    r12 = ca*sb*sg - sa*cg
    r13 = ca*sb*cg + sa*sg
    r21 = sa*cb
    r22 = sa*sb*sg + ca*cg
    r23 = sa*sb*cg - ca*sg
    r31 = -sb
    r32 = cb*sg
    r33 = cb*cg
    return R3D( (r11, r12, r13), (r21, r22, r23), (r31, r32, r33))


cpdef R3D   R3DFromVectors( Vector3 ex, Vector3 ey, Vector3 ez):
    cdef:
        double  r11, r12, r13, r21, r22, r23, r31, r32, r33
        
    if round( ex.magnitude(), 5) != 1 or round( ey.magnitude(), 5) != 1 or round( ez.magnitude(), 5) != 1:
        raise ValueError( "All vectors need to be unity vectors, but |ex| = %f, |ey| = %f, |ez| = %f!" % (ex.mag(), ey.mag(), ez.mag()))
        
        
    r11, r21, r31 = ex.xyz()
    r12, r22, r32 = ey.xyz()
    r13, r23, r33 = ez.xyz()
    
    return R3D( (r11, r12, r13), (r21, r22, r23), (r31, r32, r33))


cdef class T3D:

    """Trasformationsmatrix.
    
    Wir nennen diese Klasse T3D und nicht T3, um anzuzeigen, dass es sich um die 
    Beschreibung im Raum handelt. T3 wäre ohnehin falsch, es müsste T4x4 heißen.
    """

    cdef:
        Matrix3x3   __R3D
        Vector3     __p3D
    
    @staticmethod
    def FromEuler( x=0, y=0, z=0, alpha=0, beta=0, gamma=0):
        return T3D( R3DFromEuler( alpha, beta, gamma), Vector3( x, y, z))
    
    def __init__( self, Matrix3x3 R, Vector3 P):
        self.__R3D = R 
                                        # Rotationsmatrix
        self.__p3D = P 
                                        # Verschiebevektor
        assert isinstance( self.__R3D, R3D)
        return
    
    def clone( self):
        return self.__class__.FromEuler() << self
    
    def __richcmp__( self, other, op):
        if op == 2: # ==
            return self.__p3D == other.__p3D and self.__R3D == other.__R3D
    
        elif op == 3: # !=
            return not self == other
            
        raise ValueError( u"Unknown op = %d. " % op)

    def __mul__( self, other):
        if isinstance( other, Vector3):
            return Vector3( *(self._R_() * other + self._P_()).elems())
        
        return T3D( self._R_() * other._R_(), self._R_() * other._P_() + self._P_())
    
    def __lshift__( self, other):
        self._R_() << other._R_()
        self._P_() << other._P_()
        return self
    
    def __repr__( self):
        return u"x=%.3f, y=%.3f, z=%.3f, a=%.3f, b=%.3f, c=%.3f" % self.euler()
    
    cpdef double    a( self, deg=False, no_neg=False):
        cdef:   
            double a
            
        a = self.euler( deg)[ 3]
        if no_neg:
            if a < 0:
                a += 360.0 if deg else 2*pi

        return a

    cpdef double    b( self, deg=False):
        return self.euler( deg)[ 4]

    cpdef double    c( self, deg=False):
        return self.euler( deg)[ 5]

    cpdef tuple     abc( self, deg=False):
        return self.euler( deg)[ 3:]

    cpdef euler( self, deg=False):
        cdef:
            double  alpha, beta, gamma
            double  x, y, z
        
        x, y, z = self.__p3D.coords()
        alpha, beta, gamma = self.__R3D.euler()
        
        if deg:
            return x, y, z, degrees( alpha), degrees( beta), degrees( gamma)

        return x, y, z, alpha, beta, gamma
    
    cpdef T3D inverted( self):
        cdef R3D transposedR = self.__R3D.transposed()
        cdef T3D invertedT = T3D( transposedR, -transposedR * self.__p3D)
        return invertedT
    
    def _P_( self):
        return self.__p3D

    def P( self):
        return self.__p3D

    cpdef pose2D( self, dim=u"mm"):
        """2D-Teil der Pose.
        
        \param  dim Dimension der Ausgabe, mm oder m.
        
        \returns    (x, y, alpha) in (<dim>, <dim>, rad)
        """
        cdef:
            double  x, y, z, alpha, beta, gamma
            
        x, y, z, alpha, beta, gamma = self.euler()
        return (x/1000., y/1000., alpha) if dim == u"m" else (x, y, alpha)
 
    def _R_( self):
        return self.__R3D

    cpdef double    vnorm( self):
        return self.__p3D.mag()
        
    cpdef double    x( self):
        return self.euler()[ 0]

    cpdef tuple     xy( self):
        return self.euler()[ :2]

    cpdef tuple     xya( self):
        x, y, z, a = self.euler()[:4]
        return x, y, a
        
    cpdef tuple     xyz( self):
        return self.euler()[ :3]
        
    cpdef double    y( self):
        return self.euler()[ 1]

    cpdef double    z( self):
        return self.euler()[ 2]


cpdef T3D T3DFromEuler( double x=0, double y=0, double z=0, double alpha=0, double beta=0, double gamma=0):
    return T3D( R3DFromEuler( alpha, beta, gamma), Vector3( x, y, z))


class T3Dnp:
    
    """Wie T3D, verwendet aber numpy.
    
    Entäuschenderweise aber nur(!) bei der Multiplikation schneller.
    """
    
    @staticmethod
    def FromEuler( x=0, y=0, z=0, alpha=0, beta=0, gamma=0):
        
        ### R
        #
        ca = cos( alpha)
        cb = cos( beta)
        cg = cos( gamma)
        sa = sin( alpha)
        sb = sin( beta)
        sg = sin( gamma)
        r11 = ca*cb
        r12 = ca*sb*sg - sa*cg
        r13 = ca*sb*cg + sa*sg
        r21 = sa*cb
        r22 = sa*sb*sg + ca*cg
        r23 = sa*sb*cg - ca*sg
        r31 = -sb
        r32 = cb*sg
        r33 = cb*cg        
        R = (( r11, r12, r13), ( r21, r22, r23), (r31, r32, r33))
        
        ### P
        #
        P = ( x, y, z)
        
        return T3Dnp( R, P)
    
    def __init__( self, R, P):
        self.__R = np.matrix( R) # Rotationsmatrix
        self.__P = np.array( P) # Verschiebevektor
        assert isinstance( self.__P, (np.ndarray, tuple))
        
        self.__euler = None
        return
    
    def clone( self):
        return self.__class__.FromEuler() << self
    
    def __eq__( self, other):
        return self.__P == other.__P and np.squeeze( np.asarray( self.__R)).tolist() == np.squeeze( np.asarray( other.__R)).tolist()
    
    def __mul__( self, other):
        if isinstance( other, (list, tuple)):
            P = np.dot( self.__R, other) + self.__P
            P = tuple( np.squeeze( np.asarray( P)).tolist())
            return P
            
        T = T3Dnp( np.dot( self.__R, other.__R), tuple( np.squeeze( np.asarray( np.dot( self.__R, other.__P) + self.__P)).tolist()))
        return T
    
    def __ne__( self, other):
        return not self == other
    
    def __lshift__( self, other):
        self.__R[:, :] = other.__R
        self.__P = copy( other.__P)
        
        self.__euler = None
        return self
    
    def __repr__( self):
        return u"T3Dnp( x=%.3f, y=%.3f, z=%.3f, a=%.3f, b=%.3f, c=%.3f)" % self.euler()
    
    def a( self):
        return self.euler()[ 3]
        
    def b( self):
        return self.euler()[ 4]
        
    def c( self):
        return self.euler()[ 5]
        
    def abc( self):
        return self.euler()[ 3:]
    
    def euler( self, deg=False):
        if not self.__euler:
            ### R
            #
            R = self.__R
            r11, r12, r13, r21, r22, r23, r31, r32, r33 = R.flatten().tolist()[ 0]
            beta = atan2( -r31, sqrt( r11*r11 + r21*r21))
            cb = cos( beta)
            if cb != 0:
                alpha = atan2( r21/cb, r11/cb)
                gamma = atan2( r32/cb, r33/cb)
                
            else:
                if beta > 0:
                    alpha = 0
                    gamma = atan2( r12, r22)
                    
                else:
                    alpha = 0
                    gamma = -atan2( r12, r22)
    
            ### P
            #
            assert isinstance( self.__P, (np.ndarray, tuple))
            x, y, z = self.__P
            if not deg:
                self.__euler = x, y, z, alpha, beta, gamma
                
            else:
                self.__euler = x, y, z, degrees( alpha), degrees( beta), degrees( gamma)

        return self.__euler
    euler_coords = euler
    
    def inverted( self):
        transposedR = self.__R.getT()
        #invedT = T3Dnp( transposedR, tuple( np.squeeze( np.asarray( np.dot( -transposedR, self.__P))).tolist()))
        invedT = T3Dnp( transposedR, np.squeeze( np.asarray( np.dot( -transposedR, self.__P))))
        return invedT
    
    def _P_( self):
        return self.__P
    
    def pose2D( self, dim=u"mm"):
        """2D-Teil der Pose.
        
        \param  dim Dimension der Ausgabe, mm oder m.
        
        \returns    (x, y, alpha) in (<dim>, <dim>, rad)
        """
        x, y, z, alpha, beta, gamma = self.euler()
        return (x/1000., y/1000., alpha) if dim == u"m" else (x, y, alpha)
 
    def _R_( self):
        return self.__R
    
    def vnorm( self):
        return np.sqrt( np.dot( self.__P, self.__P))
        
    def x( self):
        return self.euler()[ 0]
        
    def xy( self):
        return self.euler()[ :2]

    def xyz( self):
        return self.euler()[ :3]

    def y( self):
        return self.euler()[ 1]
        
    def z( self):
        return self.euler()[ 2]
                

