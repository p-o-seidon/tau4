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


import collections
import statistics
import sys


class Ringbuffer:

    def __init__( self, elemcount_max, elems=None):
        self.__buffer = collections.deque( iterable=elems if elems else [], maxlen=elemcount_max)
        return

    def elem( self, elem=None):
        if elem is None:
            try:
                return self.__buffer.popleft()

            except IndexError:
                return None

        self.__buffer.append( elem)
        return self

    def elemcount( self):
        return len( self.__buffer)

    def elemcount_max( self):
        return self.__buffer.maxlen

    def elems( self):
        return self.__buffer


class RingbufferTyped(Ringbuffer):

    def __init__( self, elemtype, elemcount_max, elems=None):
        super().__init__( elemcount_max, elems)

        self.__type = elemtype
        return

    def elem( self, elem=None):
        if elem is None:
            return super().elem()

        super().elem( self.__type( elem))
        return self


class RingbufferStatistix(RingbufferTyped):

    def __init__( self, elemcount_max, elems=None):
        super().__init__( float, elemcount_max, elems)
        return

    def mean( self):
        return statistics.mean( self.elems())

    def median( self):
        return statistics.median( self.elems())

    def stddev( self):
        try:
            return statistics.stdev( self.elems())

        except statistics.StatisticsError:
            return sys.float_info.max

    def stdev( self):
        try:
            return statistics.stdev( self.elems())

        except statistics.StatisticsError:
            return sys.float_info.max
