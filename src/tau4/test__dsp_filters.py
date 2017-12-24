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

import tau4
from tau4 import dsp
from tau4 import timing
import time
import unittest


class _TESTCASE__MovingAverageFilter(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        f1 = dsp.filters.MovingAverageFilter( None, "", "", 5)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        for input, output in zip( inputs, outputs):
            f1.value( input)
            f1.execute()
            self.assertAlmostEqual( output, f1.value())

        return

    def test__variants( self):
        """
        """
        print()

        f1 = dsp.filters.MovingAverageFilter( None, "", "", 5)
        f2 = dsp.filters.MovingAverageFilter( None, "", "", 5)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        for input, output in zip( inputs, outputs):
            f1.value( input)
            f2.value( input)
            f1.execute()
            f2.execute()
            self.assertAlmostEqual( output, f1.value())
            self.assertAlmostEqual( f1.value(), f2.value())

        return

    def test__performance( self):
        """
        """
        print()

        depth = 1000

        f = dsp.filters.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing recursive variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_working_recursively_being_fast_for_large_depths()

        print( timer.results())

        f = dsp.filters.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing summing variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_using_SUM_being_fast_for_small_depths()

        print( timer.results())
        return

    def test__cy_py_performance( self):
        """
        """
        print()

        depth = 1000

        f = dsp.filters.cy.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing recursive CY variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_working_recursively_being_fast_for_large_depths()

        print( timer.results())

        f = dsp.filters.py.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing recursive PY variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_working_recursively_being_fast_for_large_depths()

        print( timer.results())


        f = dsp.filters.cy.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing summing CY variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_using_SUM_being_fast_for_small_depths()

        print( timer.results())

        f = dsp.filters.py.MovingAverageFilter( None, "", "", depth)
        inputs = (1, 2, 3, 4, 5, 6)
        outputs = (1/5, 3/5, 6/5, 10/5, 15/5, 20/5)
        with timing.Timer2( "Testing summing PY variant") as timer:
            for input, output in zip( inputs, outputs):
                f.value( input)
                f.execute_using_SUM_being_fast_for_small_depths()

        print( timer.results())
        return


_Testsuite = unittest.makeSuite( _TESTCASE__MovingAverageFilter)


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



