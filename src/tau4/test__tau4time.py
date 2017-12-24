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


from __future__ import division

import statistics
import tau4
import time
import unittest

from tau4.time import Scheduler


class _TESTCASE__Scheduler(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        def fun():
            pass

        sch = Scheduler( id=-1, resolution_ms=1)
        sch.job_add( fun, 10)

        sch.start()
        dt = time.time()
        while time.time() - dt <= 1:
            sch.execute()
            time.sleep( sch.resolution_ms() / 1000)

        return

    def test__accuracy( self):
        """
        """
        print()

        class Functor:

            def __init__( self):
                self.__time_last_execed = 0
                self.__dt_time_execed_ = []
                self._call_ = self._call_1_

            def __call__( self):
                self._call_()

            def _call_1_( self):
                self.__time_last_execed = time.time()
                self._call_ = self._call_k_

            def _call_k_( self):
                now = time.time()
                self.__dt_time_execed_.append( now - self.__time_last_execed)
                self.__time_last_execed = now

            def dt_time_execed_( self):
                return self.__dt_time_execed_

            def dt_time_execed_ms_( self):
                return [ x*1000 for x in self.__dt_time_execed_]


        functor = Functor()
        sch = Scheduler( id=-1, resolution_ms=0.01)
        sch.job_add( functor, 10)

        sch.start()
        dt = time.time()
        while time.time() - dt <= 1:
            sch.execute()
            time.sleep( sch.resolution_ms() / 1000)

        print( "Mittelw. = %.3f ms. " % statistics.mean( functor.dt_time_execed_ms_()))
        print( "Stdabw. = %.3f ms." % statistics.pstdev( functor.dt_time_execed_ms_()))
        return


_Testsuite = unittest.makeSuite( _TESTCASE__Scheduler)


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



