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


cpdef object Matrix3x3MulMatrix3x3( object M, object N):
    cdef int    i, j, k;
    cdef double s;
    
    O = M.__class__( *(0,)*9)
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            s = 0
            for k in (1, 2, 3):
                s += M[ i, k] * N[ k, j]
            
            O[ i, j] = s
    
    return O
    

cpdef object Matrix3x3MulVector3( M, V):

    v1, v2, v3 = V.elems()
    return V.__class__( M[ 1, 1]*v1 + M[ 1, 2]*v2 + M[ 1, 3]*v3, M[ 2, 1]*v1 + M[ 2, 2]*v2 + M[ 2, 3]*v3, M[ 3, 1]*v1 + M[ 3, 2]*v2 + M[ 3, 3]*v3)
