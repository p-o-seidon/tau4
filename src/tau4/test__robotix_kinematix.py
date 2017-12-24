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

import tau4
from tau4.robotix.mobile.kinematix import ChassisDatasheet4Tests, DifferentialWheels


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__DifferentialWheels(unittest.TestCase):

    def test( self):
        """
        """
        print()

        base = DifferentialWheels( ChassisDatasheet4Tests())

        ### Vollgasdrehung nach links
        #
        base.uck_100( v_100=100, omega_100=100)
                                        # Hier muss v_100 auf 0 reduziert werden,
                                        #   damit ein omega_100 möglich wird
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 0, v_100)
        self.assertAlmostEqual( 100, omega_100)

        ### Vollgasdrehung nach rechts
        #
        base.uck_100( v_100=100, omega_100=-100)
                        # Hier muss v_100 auf 0 reduziert werden,
                        #   damit ein omega_100 möglich wird
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 0, v_100)
        self.assertAlmostEqual( -100, omega_100)

        ### Drehung nach links mit unterschiedl. Winkel/geschwindigkeiten
        #
        base.uck_100( v_100=100, omega_100=50)
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 50, v_100)
        self.assertAlmostEqual( 50, omega_100)

        base.uck_100( v_100=49, omega_100=-50)
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 49, v_100)
        self.assertAlmostEqual( -50, omega_100)

        base.uck_100( v_100=50, omega_100=50)
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 50, v_100)
        self.assertAlmostEqual( 50, omega_100)

        base.uck_100( v_100=50, omega_100=75)
        v_100, omega_100 = base.uck_100()
        self.assertAlmostEqual( 25, v_100)
        self.assertAlmostEqual( 75, omega_100)

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__DifferentialWheels))


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



