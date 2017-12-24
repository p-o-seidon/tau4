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


import logging

from tau4.threads import Cycler
import time
import unittest


class _TESTCASE__Cycler(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        class MyCycler(Cycler):

            class _Buffer:

                _Counter = 0

                def __init__( self):
                    self.__time = time.time()
                    return

                def dt( self):
                    dt = time.time() - self.__time
                    self.__time = time.time()
                    return dt


            def __init__( self):
                super().__init__( cycletime=0.100, udata=self._Buffer(), is_daemon=True)

            def _run_( self, *, udata):
                udata._Counter += 1
                print( "Counter: %d. dt: %.3f." % (udata._Counter, udata.dt())),
                return


        c = MyCycler()

        print( "Start Cycler. ")
        c.start( syncly=True)
        time.sleep( 1.0)
        print( "Stop Cycler. ")
        c.stop( syncly=True)
        print( "Cycler stopped. ")

        time.sleep( 1.0)

        print( "Start Cycler again. ")
        c.start( syncly=True)
        time.sleep( 1.0)
        print( "Stop Cycler. ")
        c.stop( syncly=True)
        print( "Cycler stopped. ")

        time.sleep( 1.0)

        print( "Shutdown Cycler. ")
        c.shutdown( syncly=True)
        print( "Cycler shut down. ")

        return


_Testsuite = unittest.makeSuite( _TESTCASE__Cycler)


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



