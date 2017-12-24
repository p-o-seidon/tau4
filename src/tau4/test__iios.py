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

import multiprocessing as mp
import time
import unittest

from tau4 import iios


class ProcessThis(mp.Process):

    def __init__( self, iaout):
        super().__init__()
        
        self.__iaout = iaout
        return

    def run( self):
        this_name = self.__class__.__name__ + "_run_"

        print( "mp.current_process() = %s. " % mp.current_process())

        t0 = time.time()
        while time.time() - t0 <= 1:
            self.__iaout.value( self.__iaout.value() + 1).execute()

            time.sleep( 0.001)

        return

    def start( self):
        super().start()
        return self


class _TESTCASE__MultiprocessingCapabilities(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        print( "mp.current_process() = %s. " % mp.current_process())

        id = "process_this"
        iaout = iios.iAOutMP( id, id)
        
        id = "process_that"
        iainp = iios.iAInpMP( id, id)

        iios.iAOut2iAInpConnectorMP( iaout).connect_to_ainp( iainp)

        self.assertTrue( iainp.value() == 0.0)

        process = ProcessThis( iaout).start()
        
        t0 = time.time()
        while time.time() - t0 <= 1:
            
            iainp.execute()
            print( "iainp.value() = %.3f. " % iainp.value())
            
            time.sleep( 0.01)
            
        self.assertTrue( iainp.value() > 0.0)
        
        return


_Testsuite = unittest.makeSuite( _TESTCASE__MultiprocessingCapabilities)


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



