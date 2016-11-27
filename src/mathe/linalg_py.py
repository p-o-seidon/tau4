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
from math import atan2, cos, degrees, radians, sin, sqrt
try:
    import numpy as np

except ImportError as e:
    print( "E R R O R: %s" % e)


import pyximport; pyximport.install() 
from tau4.mathe._geometry_cy import Matrix3x3MulMatrix3x3, Matrix3x3MulVector3


def _signum_( x):
    if x >= 0:
        return 1
    
    return -1


def _tuples_to_tuple_( tuples):
    t = tuple( itertools.chain.from_iterable( tuples))
    assert isinstance( t, tuple)
    return t


class Matrix3x3:
    
    @staticmethod
    def FromRows( *rows):
        return Matrix3x3( *list(itertools.chain.from_iterable( rows)))
            
    
    def __init__( self, *rows):
        if not rows:
            rows = ((0,)*3,)*3
            
        assert isinstance( rows, tuple)
        
        self.__elems = [ 0]*9
        self.__elems[ :] = [ elem for elem in _tuples_to_tuple_( rows)]
        return
    
    def __eq__( self, other):
        if len( self.__elems) != len( other.__elems):
            return False
        
        for i in range( len( self.__elems)):
            if self.__elems[ i] != other.__elems[ i]:
                return False
            
        return True
    
    def __getitem__( self, indices):
        """ACHTUNG: Wir arbeiten hier 1-basierend!!!
        """
        i, j = indices
        return self.__elems[ (i - 1)*3 + j - 1]
    
    def __lshift__( self, other):
        self.__elems[:] = other.__elems[:9]
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

    def __ne__( self, other):
        return not self == other
    
    def __neg__( self):
        return self*(-1)
    
    def __setitem__( self, indices, v):
        """ACHTUNG: Wir arbeiten hier 1-basierend!!!
        """
        i, j = indices
        self.__elems[ (i - 1)*3 + j - 1] = v
        assert self.num_elems() == 9
        
    def elems( self):
        return self.__elems
    
    def num_elems( self):
        return len( self.__elems)
        
    def inverted( self):
        raise NotImplementedError()
    
    def transposed( self):
        tM = self.__class__()
        for i in (1, 2, 3):
            for j in (1, 2, 3):
                tM[ i, j] = self[ j, i]
                
        assert tM.num_elems() == 9
        return tM
    
    
class Vector3:
    
    def __init__( self, v1=0, v2=0, v3=0):
        """Ctor.
        
        v3=0 erleichtert die Verwendung im 2D.
        """
        self.__elems = [v1, v2, v3]
        return

    def __add__( self, other):
        v1, v2, v3 = self.__elems

        if isinstance( other, tuple):
            w1, w2 = other[ :2]
            w3 = other[ 3] if len( other) == 3 else 0
        
        else:
            w1, w2, w3 = other.__elems

        return Vector3( v1 + w1, v2 + w2, v3 + w3)
    
    def __eq__( self, other):
        return self.__elems == other.__elems
    
    def __getitem__( self, i):
        return self.__elems[ i - 1]
    
    def __lshift__( self, other):
        self.__elems[:] = other.__elems[:3]
        return self

    def __ne__( self, other):
        return not self == other
    
    def __repr__( self):
        return u"[%.3f, %.3f, %.3f]" % tuple( self.__elems)
    
    def __setitem__( self, i, v):
        self.__elems[ i - 1] = v
        
    def mag( self):
        v1, v2, v3 = self.__elems
        return sqrt( v1*v1 + v2*v2 + v3*v3)
    
    def coords( self):
        return self.__elems
    
    elems = coords
            
    def x( self):
        return self[ 1]
    
    def xy( self):
        return self.__elems[ 0], self.__elems[ 1]

    def xyz( self):
        return self.__elems[ 0], self.__elems[ 1], self.__elems[ 2]

    def y( self):
        return self[ 2]
    
    def z( self):
        return self[ 3]

    
class T3D:
    
    @staticmethod
    def FromEuler( x=0, y=0, z=0, alpha=0, beta=0, gamma=0):
        return T3D( R3D.FromEuler( alpha, beta, gamma), p3D( x, y, z))
    
    def __init__( self, R, p):
        self.__R3D = R 
                                        # Rotationsmatrix
        self.__p3D = p 
                                        # Verschiebevektor        
        assert isinstance( self.__R3D, R3D)
        return
    
    def clone( self):
        return self.__class__.FromEuler() << self
    
    def __eq__( self, other):
        return self.__p3D == other.__p3D and self.__R3D == other.__R3D
    
    def __mul__( self, other):
        if isinstance( other, (p3D, Vector3)):
            return p3D( *(self.__R3D*other + self.__p3D).elems())
        
        return T3D( self.__R3D*other.__R3D, self.__R3D*other.__p3D + self.__p3D)
    
    def __ne__( self, other):
        return not self == other
    
    def __lshift__( self, other):
        self.__R3D << other.__R3D
        self.__p3D << other.__p3D
        return self
    
    def __repr__( self):
        return u"x=%.3f, y=%.3f, z=%.3f, a=%.3f, b=%.3f, c=%.3f" % self.euler()
    
    def a( self, deg=False):
        return self.euler( deg)[ 3]

    def b( self, deg=False):
        return self.euler( deg)[ 4]

    def c( self, deg=False):
        return self.euler( deg)[ 5]

    def abc( self, deg=False):
        return self.euler( deg)[ 3:]

    def euler( self, deg=False):
        alpha, beta, gamma = self.__R3D.euler()
        x, y, z = self.__p3D.coords()
        if deg:
            return x, y, z, degrees( alpha), degrees( beta), degrees( gamma)

        return x, y, z, alpha, beta, gamma
    euler_coords = euler
    
    def inverted( self):
        transposedR = self.__R3D.transposed()
        invertedT = T3D( transposedR, -transposedR*self.__p3D)
        return invertedT
    
    def _P_( self):
        return self.__p3D
    
    def P( self):
        return self.__p3D

    def pose2D( self, dim=u"mm"):
        """2D-Teil der Pose.
        
        \param  dim Dimension der Ausgabe, mm oder m.
        
        \returns    (x, y, alpha) in (<dim>, <dim>, rad)
        """
        x, y, z, alpha, beta, gamma = self.euler()
        return (x/1000., y/1000., alpha) if dim == u"m" else (x, y, alpha)
 
    def _R_( self):
        return self.__R3D
        
    def vnorm( self):
        return self.__p3D.mag()
    
    def x( self):
        return self.__p3D.y()
    
    def xy( self):
        return self.__p3D.xy()

    def xyz( self):
        return self.__p3D.xyz()

    
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
                

class e3D:
    
    def __init__( self, alpha, beta, gamma):
        self.__elems = [ alpha, beta, gamma]
        return
    
    def __eq__( self, other):
        for i in (0, 1, 2):
            if self.__elems[ i] != other.__elems[ i]:
                return False
            
        return True
    
    def __ne__( self, other):
        return not self == other
    
    def __lshift__( self, other):
        self.__elems[ :] = other.__elems[ :]
        return self
    
    def __repr__( self):
        return u"(alpha = %.3f°, beta = %.3f°, gamma = %.3f°)" % tuple( map( degrees, self.__elems))
    
    def alpha( self):
        return self.__elems[ 0]
    
    def elems( self):
        return self.__elems
    
    
class p3D(Vector3):
    
    def __init__( self, x=0, y=0, z=0):
        Vector3.__init__( self, x, y, z)
    

class R3D(Matrix3x3):
    
    @staticmethod
    def FromEuler( alpha=0, beta=0, gamma=0):
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
    
        
    def __init__( self, *rows):
        Matrix3x3.__init__( self, *rows)
        if not len( rows):
            self << R3D.FromEuler()
            
        self.__euler = None
        return
    
    def euler( self):
        if not self.__euler:
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
    
            self.__euler = alpha, beta, gamma
            
        return self.__euler
        

