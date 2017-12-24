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

from math import degrees, radians
import time
import unittest

import tau4
from tau4.mathe.linalg import T3D
from tau4.setup.setup4app import Setup4


class Setup4TAU(Setup4):

    def cycletime_rc( self, platformname, arg=None):
        if arg is None:
            return self.paramvalue( platformname, "cycletimes", "rc")

        self.paramvalue_change( platformname, "cycletimes", "rc", arg)
        return self

    def uss_postures( self, platformname, arg=None):
        if arg is None:
            postures = self.paramvalue( platformname, "uss", "poses")
            postures = eval( postures)
            return postures

        self.paramvalue_change( platformname, "uss", "poses", arg)
        return self


class _TESTCASE__Setup(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        Setup4TAU().appname( "tau4")
        Setup4TAU().filecontent_default( """
all:
    cycletimes: &cycletimes
        mmi:    0.500
        plc:    0.01
        rc:     0.1
        positionsensor:     0.25
        goalcontrollers:    1.0

    distances: &distances
        escapedistance_if_obstacles: 0.5

    speeds: &speeds
        v_avoiding_100: 60
        v_escaping_100: 60
        v_goaling_100:  30

arielle:
    cycletimes: *cycletimes

rovercpu01:
    cycletimes: *cycletimes

rovercpu02:
    cycletimes: *cycletimes

rovercpu03:
    basename: lunchbox

    cycletimes: *cycletimes

    distances:  *distances

    iosystemname: raspi # One of 'arduino', 'explorerhatpro', 'labjack', 'noios', 'raspi'
    is_distancesensors_available: 1
    is_md_available: 1
    is_positionsensor_available: 1
    mdname: l293d   # One of 'l293d', 'explorerhatpro', 'md25'.
    positionsensor_ipaddr: 10.0.0.103
    positionsensor_name: navilock   # One of 'navilock', 'emlid'.
    positionsensor_portnbr: 6000

    speeds:     *speeds

    uss:
        count: 2
        distance_max: 2.0
        poses: (T3D.FromEuler( -0.025, 0.070, 0, radians( 20)), T3D.FromEuler( 0.025, 0.070, 0, radians( -20)))

triton:
    cycletimes: *cycletimes

    distances:  *distances

    speeds:     *speeds
"""
        )
        Setup4TAU().sync()
                                        # Jetzt ist das File geladen
        self.assertAlmostEqual( 0.100, Setup4TAU().cycletime_rc( "rovercpu01"))

        Setup4TAU().cycletime_rc( "rovercpu01", 0.101)
        self.assertAlmostEqual( 0.101, Setup4TAU().cycletime_rc( "rovercpu02"))

        Setup4TAU().sync()
        self.assertAlmostEqual( 0.101, Setup4TAU().cycletime_rc( "rovercpu02"))

        Setup4TAU().cycletime_rc( "rovercpu01", 0.100)
        self.assertAlmostEqual( 0.100, Setup4TAU().cycletime_rc( "rovercpu03"))

        Setup4TAU().sync()

        platformname = "rovercpu03"
        postures = Setup4TAU().uss_postures( platformname)

        return


_Testsuite = unittest.makeSuite( _TESTCASE__Setup)


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



