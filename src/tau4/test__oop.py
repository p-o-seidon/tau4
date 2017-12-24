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


import time
import unittest

from tau4 import oop


class _TESTCASE__EXECUTE_CYCLICALLY(unittest.TestCase):

    class ObjectWithExecuteMethod:

        @oop.execute_cyclically( 0.1)
        def execute( self):
            print( time.time())


    def test__simple( self):
        """
        """
        print()

        o = self.ObjectWithExecuteMethod()
        t0 = time.time()
        while time.time() - t0 <= 5:
            o.execute()

        return


_Testsuite = unittest.makeSuite( _TESTCASE__EXECUTE_CYCLICALLY)


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



