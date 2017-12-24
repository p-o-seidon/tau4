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
from tau4.data import flex
from tau4.data import pandora
from tau4.ios.hal.ios import IOSpecPool
from tau4.ios.hal.ios import DInpSpec, DOutSpec
from tau4.ios.hil.arduino import Arduino
from tau4.ios.hil.arduino import ArduinoMega
from tau4.ios.hil.arduino import ArduinoDINP
from tau4.ios.hil.arduino import ArduinoDOUT
from tau4.ios.hil.labjack import LabJackU3HV
from tau4.ios.hil.labjack import LabJackFIOAsDInp
from tau4.ios.hil.labjack import LabJackFIOAsDOut
import time
import unittest


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__hil_lj3uv(unittest.TestCase):

    def test( self):
        """
        """
        print()

        if 1:
            daq = LabJackU3HV()
                                            # What, if there's more than one LabJack?
            pinspec = DOutSpec( p_raw=pandora.BoxClippingMonitored( value=0, id="led11", label="LED 1 on a LabJack", dim="", bounds=(0, 1)))
            pinspec.connect( pindef=LabJackFIOAsDOut( daq, "fio4"))
                                            # led1 now lies on fio4.
            IOSpecPool().douts().add( pinspec)

            pinspec = DOutSpec( p_raw=pandora.BoxClippingMonitored( value=0, id="led12", label="LED 2 on a LabJack", dim="", bounds=(0, 1)))
            pinspec.connect( pindef=LabJackFIOAsDOut( daq, "fio5"))
                                            # led2 now lies on fio5.
            IOSpecPool().douts().add( pinspec)


            togglevalue = 0
            dt = 0.100
            for i in range( 10):
                IOSpecPool().douts( "led11").value( togglevalue)
                IOSpecPool().douts( "led12").value( togglevalue)
                IOSpecPool().execute_outs()
                time.sleep( dt)

                togglevalue = 1 - togglevalue
                dt -= 0.010

            IOSpecPool().douts( "led11").value( 0)
            IOSpecPool().douts( "led12").value( 0)
            IOSpecPool().douts().execute()

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__hil_lj3uv))


class _TESTCASE__hil_arduino(unittest.TestCase):

    def test__normal_use( self):
        """
        """
        print()

        if 0:
            nano1 = Arduino( "/dev/ttyUSB0")
            pin = DOutSpec( p_raw=pandora.BoxClippingMonitored( id="led1", value=0, label="LED 1", dim="", bounds=(0, 1)))
            pin.connect( ArduinoDOUT( nano1, "d2"))
            IOSpecPool().douts().add( pin)

            pin = DOutSpec( p_raw=pandora.BoxClippingMonitored( id="led2", value=0, label="LED 2", dim="", bounds=(0, 1)))
            pin.connect( ArduinoDOUT( nano1, "d13"))
            IOSpecPool().douts().add( pin)

            togglevalue = 0
            for i in range( 10):
                IOSpecPool().douts( "led1").value( togglevalue)
                IOSpecPool().douts( "led2").value( togglevalue)
                IOSpecPool().execute_outs()
                time.sleep( 0.100)

                togglevalue = 1 - togglevalue

        if 0:
            mega = ArduinoMega( "/dev/ttyACM0")
            fv = flex.VariableDeClMo( id="led3", value=0, label="LED 3", dim="", value_min=0, value_max=1)
            pin = DOutSpec( p_raw=pandora.BoxClippingMonitored( id="led3", value=0, label="LED 3", dim="", bounds=(0, 1)))
            pin.connect( ArduinoDOUT( mega, "d2"))
            IOSpecPool().douts().add( pin)

            togglevalue = 0
            dt = 0.100
            for i in range( 10):
                IOSpecPool().douts( "led3").value( togglevalue)
                IOSpecPool().execute_outs()
                time.sleep( dt)

                togglevalue = 1 - togglevalue
                dt -= 0.010

            IOSpecPool().douts( "led3").value( 0)
            IOSpecPool().douts().execute()

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__hil_arduino))


class _TESTCASE__hil_devantech(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__hil_devantech))


class _TESTCASE__hil_mixed(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__hil_mixed))


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



