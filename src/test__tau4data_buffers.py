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
import time
import unittest

from tau4.data import buffers


class _TESTCASE__Ringbuffer(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        rb = buffers.Ringbuffer( 5)
        self.assertAlmostEqual( 0, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())
        
        rb.elem( 42)
        rb.elem( "Hollodrio")
        self.assertAlmostEqual( 2, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())
        
        self.assertEqual( 42, rb.elem())
        self.assertAlmostEqual( 1, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())

        self.assertEqual( "Hollodrio", rb.elem())
        self.assertAlmostEqual( 0, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())

        for i in range( rb.elemcount_max()*2):
            rb.elem( i)
            
        self.assertEqual( rb.elemcount_max(), rb.elem())
        self.assertAlmostEqual( rb.elemcount_max() - 1, rb.elemcount())
        return


_Testsuite = unittest.makeSuite( _TESTCASE__Ringbuffer)


class _TESTCASE__RingbufferTyped(unittest.TestCase):

    def test_simple( self):
        """
        """
        print()

        rb = buffers.RingbufferTyped( float, 5)
        self.assertAlmostEqual( 0, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())
        
        rb.elem( 42)
        self.assertRaises( ValueError, rb.elem, "Hollodrio")
        self.assertAlmostEqual( 1, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())
        
        self.assertEqual( 42, rb.elem())
        self.assertAlmostEqual( 0, rb.elemcount())
        self.assertAlmostEqual( 5, rb.elemcount_max())

        for i in range( rb.elemcount_max()*2):
            rb.elem( i)
            
        self.assertEqual( rb.elemcount_max(), rb.elem())
        self.assertAlmostEqual( rb.elemcount_max() - 1, rb.elemcount())
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__RingbufferTyped))


class _TESTCASE__RingbufferStatistix(unittest.TestCase):

    def test_simple( self):
        """
        """
        print()
        
        rb = buffers.RinbufferStatistix( 5)
        
        rb.elem( 1)
        self.assertAlmostEqual( 1, rb.mean())
        
        rb.elem( 1)
        self.assertAlmostEqual( 1, rb.mean())

        rb.elem( 42)
        self.assertAlmostEqual( 14.66666667, rb.mean())

        return
    
    def test_mean_and_median( self):
        """
        """
        print()
        
        elems = [1]*4 + [2]*6 + [3]*4 + [4]*4 +[5]*3 + [6, 6, 7, 8]
        elemcount_max = len( elems)
        rb = buffers.RinbufferStatistix( elemcount_max, elems=elems)
        
        print( "Median = %f; mean = %f. " % (rb.median(), rb.mean()))
        self.assertTrue( rb.median() < rb.mean())
        
        
        elems = [1, 4, 6, 6, 8, 8, 8] + [9]*4 + [10]*4 + [11]*5 + [12]*5
        elemcount_max = len( elems)
        rb = buffers.RinbufferStatistix( elemcount_max, elems=elems)
        
        median = rb.median()
        mean = rb.mean()
        print( "Median = %f; mean = %f. " % (rb.median(), rb.mean()))
        self.assertTrue( rb.median() > rb.mean())
        
        for i in range( rb.elemcount_max()):
            rb.elem( rb.elem())
            self.assertAlmostEqual( mean, rb.mean())
            self.assertAlmostEqual( median, rb.median())
        
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__RingbufferStatistix))


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



