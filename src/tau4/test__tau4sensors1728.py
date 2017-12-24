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

import ipaddress
from math import *

import tau4
from tau4 import Id
from tau4 import ios2
from tau4.ios2 import explorerhatpro as xhp
from tau4.mathe.geometry import Point, Polygon
from tau4.mathe.geometry import Point2D
from tau4.mathe.linalg import T3D, V3D
from tau4 import sensordata1728 as sensordata
from tau4 import sensors1728 as sensors
import time
import unittest


_TEST_IRS_AT_GPIO = False
_TEST_USS_AT_GPIO = False
_TEST_USS_AT_EXPLORER_HAT_PRO = False
_TEST_USS_VIA_PYMATA = True
_TEST_EMLID_REACH = False
_TEST_NAVILOCK = False

class _TESTCASE__0(unittest.TestCase):

    pass

_Testsuite = unittest.makeSuite( _TESTCASE__0)


if _TEST_USS_AT_GPIO:

    class _TESTCASE__Devantech_SRF04(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__Devantech_SRF04))


if _TEST_USS_AT_EXPLORER_HAT_PRO:

    class _TESTCASE__Devantech_SRF04_At_Explorer_HAT_Pro(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            ####################################################################
            ### IOs
            #

            ### Board
            #
            boardXHP = xhp.BoardXHP()
            ios2.MotorDrivers().board_add( board=boardXHP, id_usr="xhp", )
            boardXHP = ios2.MotorDrivers().board( "xhp")

            ### Echte IOs auf dem Explorer HAT Pro für die USS
            #
            ios2.IOSystem().dout_add( xhp.DOutXHP( board=boardXHP, id_sys=1, is_hi_active=False, label="Trigger USS 11:00"), "trigger uss 11:00")
            ios2.IOSystem().dinp_add( xhp.DInpXHP( board=boardXHP, id_sys=1, is_hi_active=True, label="Echo USS 11:00"), "echo uss 11:00")

            ios2.IOSystem().dout_add( xhp.DOutXHP( board=boardXHP, id_sys=2, is_hi_active=False, label="Trigger USS 13:00"), "trigger uss 13:00")
            ios2.IOSystem().dinp_add( xhp.DInpXHP( board=boardXHP, id_sys=2, is_hi_active=True, label="Echo USS 13:00"), "echo uss 13:00")

            ####################################################################
            ### Sensor
            #
            id = Id( "uss 11:00")
            sensor = sensors.DistancesensorUss_Devantech_SRF04_Using_Callbacks( \
                id=id,
                actuals=sensordata.ActualsDistancesensor( id=id),
                setup=sensordata.SetupDistancesensorUSS( \
                    is_setup=True,
                    dout_trigger=ios2.IOSystem().douts( "trigger uss 11:00"),
                    dinp_echo=ios2.IOSystem().dinps( "echo uss 11:00"),
                    distance_max=3.0,
                    rTs=T3D.FromEuler( -0.250, 0.350, 0, radians( 30)),
                )
            )
            sensors.Sensors().ranger_add( sensor)

            ####################################################################
            ### Und Test
            #
            while True:
                sensor.execute()
                time.sleep( 0.500)

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__Devantech_SRF04_At_Explorer_HAT_Pro))


if _TEST_USS_VIA_PYMATA:

    class _TESTCASE__Devantech_SRF04_Via_PyMata(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            ####################################################################
            ### IOs
            #

            ### Board
            #
            board = ios2.arduino.BoardPyMata()
            ios2.IOBoards().board_add( board=board, id_usr="arduino", )

            ### Echte IOs auf dem Arduino Nano
            #
            ios2.IOSystem().dout_add( \
                ios2.arduino.DOutNano( board=board, id_sys=2, is_hi_active=False, label="Trigger USS 11:00"),
                "trigger uss 11:00"
            )
            ios2.IOSystem().dinp_add( \
                ios2.arduino.DInpNano( board=boardXHP, id_sys=3, is_hi_active=True, label="Echo USS 11:00"),
                "echo uss 11:00"
            )

            ios2.IOSystem().dout_add( \
                ios2.arduino.DOutNano( board=board, id_sys=4, is_hi_active=True, label="Trigger USS 13:00"),
                "trigger uss 13:00"
            )
            ios2.IOSystem().dinp_add( \
                ios2.arduino.DInpNano( board=board, id_sys=5, is_hi_active=True, label="Echo USS 13:00"),
                "echo uss 13:00"
            )

            ####################################################################
            ### Sensor 1
            #
            id = Id( "uss 11:00")
            sensor = sensors.DistancesensorUss_Devantech_SRF04_Using_PyMata( \
                id=id,
                actuals=sensordata.ActualsDistancesensor( id=id),
                setup=sensordata.SetupDistancesensorUSS( \
                    is_setup=True,
                    dout_trigger=ios2.IOSystem().douts( "trigger uss 11:00"),
                    dinp_echo=ios2.IOSystem().dinps( "echo uss 11:00"),
                    distance_max=3.0,
                    rTs=T3D.FromEuler( -0.250, 0.350, 0, radians( 30)),
                )
            )
            sensors.Sensors().ranger_add( sensor)

            ####################################################################
            ### Sensor 2
            #
            id = Id( "uss 13:00")
            sensor = sensors.DistancesensorUss_Devantech_SRF04_Using_PyMata( \
                id=id,
                actuals=sensordata.ActualsDistancesensor( id=id),
                setup=sensordata.SetupDistancesensorUSS( \
                    is_setup=True,
                    dout_trigger=ios2.IOSystem().douts( "trigger uss 13:00"),
                    dinp_echo=ios2.IOSystem().dinps( "echo uss 13:00"),
                    distance_max=3.0,
                    rTs=T3D.FromEuler( 0.250, 0.350, 0, radians( -30)),
                )
            )
            sensors.Sensors().ranger_add( sensor)

            ####################################################################
            ### Und Test
            #
            rangers = sensors.Sensors().rangers()
            while True:
                rangers.execute()

                for ranger in rangers():
                    print( "Ranger '%s': d = '%.3f'. " % (ranger.id(), ranger.actuals().distance()))

                time.sleep( 0.500)

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__Devantech_SRF04_At_Explorer_HAT_Pro))


if _TEST_IRS_AT_GPIO:

    class _TESTCASE__Sharp_GP2D12(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            ### Create and add some sensors to tau4
            #
            ###     Ranger
            #
            ios2.IOSystem().ainps_add( "irs", ios2.noios.AInpDummy( Id( "irs.distance_V"), "isr.distance_V"))

            ranger = sensors.DistancesensorIrs_Sharp_GP2D12( \
                id=Id(),
                actuals=sensordata.ActualsDistancesensorAnalog(),
                setup=sensordata.SetupDistancesensorAnalog(\
                    ainp_distance_V=ios2.IOSystem().ainps( "irs"),
                    distance_max=0.8
                )
            )

            ios2.IOSystem().execute()
            ranger.execute()
            print( ranger.actuals().distance())

            sensors.Sensors().ranger_add( ranger)
            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__Sharp_GP2D12))


if _TEST_NAVILOCK:

    class _TESTCASE__Navilock(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            ### Create and add some sensors to tau4
            #
            ###     Navi
            #
            ###         Navilock
            #
            navdev = sensors.Positionsensor_Navilock( \
                id=Id(),
                actuals=sensordata.ActualsPositionsensor_Navilock(),
                setup=sensordata.SetupPositionsensor( rTs=T3D.FromEuler())
            )

            ios2.IOSystem().execute()
            navdev.execute()
            print( navdev.actuals().xyz())

            sensors.Sensors().navdev_add( navdev)
            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__Navilock))


if _TEST_EMLID_REACH:

    class _TESTCASE__EMLID_Reach(unittest.TestCase):

        def test__simple( self):
            """
            """
            print()

            ### Create and add some sensors to tau4
            #
            ###     Navi
            #
            ###         EMLID REach
            #
            navdev = sensors.Positionsensor_EMLID_Reach( \
                id=Id(),
                actuals=sensordata.ActualsPositionsensor(),
                setup=sensordata.SetupPositionsensor_EMLID_Reach( ipaddr=ipaddress.IPv4Address( "10.0.0.42"), portnbr=1962, rTs=T3D.FromEuler())
            )

            ios2.IOSystem().execute()
            navdev.execute()
            print( navdev.actuals().xyz())

            sensors.Sensors().navdev_add( navdev)

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__EMLID_Reach))


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


def _lab_emlid_reach_():
    #ipaddr = "169.254.33.38"
    ipaddr = "10.0.0.19"
    portnbr = 6000
    navdev = sensors.Positionsensor_EMLID_Reach( \
        id=Id(),
        actuals=sensordata.ActualsPositionsensor(),
        setup=sensordata.SetupPositionsensor_EMLID_Reach( ipaddr=ipaddress.IPv4Address( ipaddr), portnbr=portnbr, rTs=T3D.FromEuler())
    )
    sensors.Sensors().navdev_add( navdev)
    while True:
        navdev.execute()
        print( navdev.actuals().xyz())

    return


def _lab_navilock_():
    navdev = sensors.Positionsensor_Navilock( \
        id=Id(),
        actuals=sensordata.ActualsPositionsensor_Navilock(),
        setup=sensordata.SetupPositionsensor( rTs=T3D.FromEuler())
    )
    sensors.Sensors().navdev_add( navdev)
    while True:
        navdev.execute()
        print( navdev.actuals().xyz())

    return


if __name__ == '__main__':
    _Test_()
    #_lab_emlid_reach_()
    #_lab_navilock_()
    input( u"Press any key to exit...")



