#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
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

import abc, collections

from tau4 import Object
from tau4.data.pandora import BoxMonitored


#class Filter(Object, metaclass=abc.ABCMeta): # Geht wegen Object und abc niht
#cdef class Filter(Object): # Geht wegen Objects nicht: Müsste auch cythonisiert sein.
cdef class Filter:

    cdef:
        object  __p_value
        object  __p_Ts

    def __init__( self, id, str label, str dim, p_Ts):
        #super().__init__( id=id)

        self.__p_value = BoxMonitored( id=id, value=0.0, label=label, dim=dim)
        self.__p_Ts = p_Ts
        return

#    @abc.abstractmethod
    cpdef       execute( self):
        pass

    cpdef       reg_tau4s_on_modified( self, tau4s):
        return self.__p_value.reg_tau4s_on_modified( tau4s)

    cpdef       ureg_tau4s_on_modified( self, tau4s):
        return self.__p_value.ureg_tau4s_on_modified( tau4s)

    cpdef value( self, arg=None):
        if arg is None:
            return self.__p_value.value()

        self.__p_value.value( arg)
        return self


cdef class MovingAverageFilter(Filter):

    """Moving average filter.

    \_2DO
        StrategyChooser implementieren, der zur Laufzeit bestimmt, was schneller
        ist und entsprechend wählt.
    """

    cdef:
        object  __buffer
        int     __depth
        float   __value

        object  _execute_


    def __init__( self, id, label, dim, int depth):
        super().__init__( id, label, dim, BoxMonitored( value=0.0))

        self.__depth = depth
        self.__buffer = collections.deque( [ 0]*self.__depth, self.__depth)
        self.__value = 0.0

        if depth <= 10000:
            self._execute_ = self.execute_using_SUM_being_fast_for_small_depths

        else:
            self._execute_ = self.execute_working_recursively_being_fast_for_large_depths

        return

    cpdef execute( self):
        return self._execute_()

    cpdef execute_using_SUM_being_fast_for_small_depths( self):
        """Implementation by calculating a sum devided by the depth of the flter.
        """
        self.__buffer.rotate( -1)
        self.__buffer.append( self.__value)
        Filter.value( self, sum( self.__buffer)/self.__depth)
        return self

    cpdef execute_working_recursively_being_fast_for_large_depths( self):
        """Implementation variant avoiding the calculation of a sum.
        """
        cdef float  m = Filter.value( self)
        m -= self.__buffer[ 0]/self.__depth
        self.__buffer.rotate( -1)
        self.__buffer[ self.__depth - 1] = self.__value
        m += self.__value/self.__depth
        Filter.value( self, m)
        return self

    cpdef value( self, arg=None):
        if arg is None:
            return Filter.value( self)

        self.__value = arg
        return self

