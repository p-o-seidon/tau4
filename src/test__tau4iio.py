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

from tau4 import iio


class _TESTCASE__DOUT2DINP(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()
        
        id = "iDOUT 1"
        idout = iio.iDOUT( id, id)
        
        id = "iDINP 1"
        idinp = iio.iDINP( id, id, True)
        
        iio.iDOUT2iDINPConnector( idout).connect_to_dinp( idinp)

        idinps = iio.iDINPs()
        idinps.ipin_add( idinp)
        
        idouts = iio.iDOUTs()
        idouts.ipin_add( idout)
        
        idout.value( 1)
        self.assertEqual( 0, idinp.value())
        
        idouts.execute()
        self.assertEqual( 0, idinp.value())
        
        idinps.execute()        
        self.assertEqual( 1, idinp.value())
        
        idinps.execute()        
        self.assertEqual( 1, idout.value())
        self.assertEqual( 0, idinp.value())
        
        return


_Testsuite = unittest.makeSuite( _TESTCASE__DOUT2DINP)


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
    raw_input( u"Press any key to exit...")



