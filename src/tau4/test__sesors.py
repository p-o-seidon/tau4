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
from tau4.data import pandora
from tau4 import sensors
from tau4.ios.hal.ios import DInpSpec, DOutSpec, IOSpecPool
from tau4.ios.hil.arduino import ArduinoDINP, ArduinoDOUT, ArduinoNano
from tau4.ios.hil.raspi import RasPiDINP, RasPiDOUT, RasPi
from tau4.mathe.linalg import T3D
import time
import unittest


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__DistanceSensor_ContourDetector(unittest.TestCase):

    class Rack(sensors.SensorOwner):

        def __init__( self):
            self.__bT = T3D.FromEuler()
            return

        def bT( self):
            return self.__bT


    def test( self):
        """
        """
        print()

        rack = self.Rack()
        sensor = sensors.DistanceSensor_ContourDetector.SymPyVersion( owner=rack, id=None, bContourpoints=[(-100, 0), (100, 0), (100, 100), (-100, 100)], rTs=T3D.FromEuler())
        sensor.p_distance().label( "Distance").dim( "m")
        sensor.execute()
                                        # Wir stehen auf (0, 0) und schauen nach
                                        #   "oben" = in Richtung Y-Achse. Wir sehen
                                        #   also 3 m weit.
        p = sensor.p_distance()
        print( "%s: %.3f %s" % (p.label(), p.value(), p.dim()))
        self.assertAlmostEqual( 3, p.value())

        rack.bT() << T3D.FromEuler( 0, 98, 0)
        sensor.execute()
                                        # Wir stehen 2 m avor der Contour, der Strahl
                                        #   schneidet also die Contour.
        print( "%s: %.3f %s" % (p.label(), p.value(), p.dim()))
        self.assertAlmostEqual( 2, p.value())

        rack.bT() << T3D.FromEuler( 0, 110, 0)
        sensor.execute()
                        # Wir stehen 10 m außerhalb der Contour!
        print( "%s: %.3f %s" % (p.label(), p.value(), p.dim()))
        self.assertAlmostEqual( 0, p.value())
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__DistanceSensor_ContourDetector))


class _TESTCASE__DistanceSensor_DevantechSRF04__Polling_Version(unittest.TestCase):

    def test( self):
        """
        """
        print()

        if 0:
            nano1 = ArduinoNano( "/dev/ttyUSB0")
    
            dout_trigger = DOutSpec( p_raw=pandora.BoxClippingMonitored( id="uss.trigger.1", value=0, label="Trigger USS 1", dim="", bounds=(0, 1)))
            pin_impl = ArduinoDOUT( nano1, "d2")
            dout_trigger.connect( pin_impl)
            IOSpecPool().douts().add( dout_trigger)
                                            # Im IOSpecPool können auch Pins sein,
                                            #   die zum LabJack usw. gehören.
            dinp_echo = DInpSpec( p_raw=pandora.BoxClippingMonitored( id="uss.echo.1", value=0, label="Echo USS 1", dim="", bounds=(0, 1)))
            pin_impl = ArduinoDINP( nano1, "d3")
            dinp_echo.connect( pin_impl)
            IOSpecPool().dinps().add( dinp_echo)
                                            # Im IOSpecPool können auch Pins sein,
                                            #   die zum LabJack usw. gehören.
            uss_setup = sensors.DistanceSensorSetup_DevantechSRF04( dout_trigger=dout_trigger, dinp_echo=dinp_echo, rTs=T3D.FromEuler())
            uss_data = sensors.DistanceSensorData_DevantechSRF04( sensors.SensorStatus())
            uss = sensors.DistanceSensor_DevantechSRF04__Polling_Version( id="uss.1", sensordata=uss_data, sensorsetup=uss_setup)
            while True:
                uss.execute()
                print( "Distance by uss = '%.3f'. " % uss.distance())
                #time.sleep( 1.0)

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__DistanceSensor_DevantechSRF04__Polling_Version))


class _TESTCASE__DistanceSensor_DevantechSRF04(unittest.TestCase):

    def test( self):
        """
        """
        print()

        raspi = RasPi()
        
        dout_trigger = DOutSpec( p_raw=pandora.BoxClippingMonitored( id="uss.1.trigger", value=0, label="Trigger USS 1", dim="", bounds=(0, 1)))
        pin_impl = RasPiDOUT( raspi, "11")
        dout_trigger.connect( pin_impl)
                                        # Diesen IO nicht zum IOSpecPool() hinzufügen, 
                                        # da er vom Sensor direkt behandelt werden 
                                        # muss!
        dinp_echo = DInpSpec( p_raw=pandora.BoxClippingMonitored( id="uss.1.echo", value=0, label="Echo USS 1", dim="", bounds=(0, 1)))
        pin_impl = RasPiDINP( raspi, "12")
        dinp_echo.connect( pin_impl)
                                        # Diesen IO nicht zum IOSpecPool() hinzufügen, 
                                        # da er vom Sensor direkt behandelt werden 
                                        # muss!
        uss_setup = sensors.DistanceSensorSetup_DevantechSRF04( dout_trigger=dout_trigger, dinp_echo=dinp_echo, rTs=T3D.FromEuler())
        uss_data = sensors.DistanceSensorData_DevantechSRF04( sensors.SensorStatus())
        uss = sensors.DistanceSensor_DevantechSRF04( id="uss.1", sensordata=uss_data, sensorsetup=uss_setup)
        while True:
            uss.execute()
            print( "Distance by uss = '%.3f'. " % uss.distance())
            time.sleep( 0.5)

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__DistanceSensor_DevantechSRF04))


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



