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


_TEST_ARDUINO_VIA_PYMATA = True
_TEST_2_USS_ON_RASPI = False
_TEST_L293D_AT_RASPI = False

import tau4
from tau4.data import pandora
from tau4 import Id
from tau4 import ios2
if _TEST_ARDUINO_VIA_PYMATA:
    from tau4.ios2 import arduino

from tau4.ios2 import labjack
from tau4.ios2 import l293d
from tau4.ios2 import raspi
from tau4.mathe.linalg import T3D
from tau4 import sensordata1728 as sensordata
from tau4 import sensors1728 as sensors
import time
import unittest


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__labjack(unittest.TestCase):

    def test( self):
        """
        """
        print()

        if 0:
            board = labjack.BoardU3()
                                            # What, if there's more than one LabJack?
            ios2.IOBoards().board_add( board, "u3hv")

            for id_usr, id_sys in (("button1", "fio4"), ("button2", "fio5"), ("button3", "fio6"), ("button4", "fio7")):
                port = labjack.DInpU3( board=board, id_sys=id_sys, label=id_usr)
                ios2.IOSystem().dinp_add( port, id_usr)

                port = ios2.IOSystem().dinps( id_usr)
                port.execute()
                print( "%s: %d. " % (port.label(), port.value()))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__labjack))


if _TEST_ARDUINO_VIA_PYMATA:

    class _MotorEncoder:

        def _on_encoder_( self, D):
            return


        def __init__( self, dinpA: arduino.DInpNano, dinpB: arduino.DInpNano):
            self.__dinpA = dinpA
            self.__dinpB = dinpB

            self.__board: arduino.BoardPyMata = self.__dinpA._board

            #self.__board.set_pinmode_ENCODER( int( self.__dinpA.id_sys()))
            #self.__board.set_pinmode_ENCODER( int( self.__dinpB.id_sys()))

            self.__board.encoder_config( self.__dinpA.id_sys(), self.__dinpB.id_sys())
            return

        def valueA( self):
            #value = self.__board.encoder_read( self.__dinpA.id_sys())
            value = self.__board.dinp_read( self.__dinpA.id_sys())
            return value

        def valueB( self):
            #value = self.__board.encoder_read( self.__dinpB.id_sys())
            value = self.__board.dinp_read( self.__dinpB.id_sys())
            return value


    class _TESTCASE__arduino_pymata(unittest.TestCase):

        def __init__( self, *args, **kwargs):
            super().__init__( *args, **kwargs)

            if not ios2.IOBoards().has_board( "nano"):
#                board = arduino.BoardPyMata( "/dev/ttyUSB1")
                board = arduino.BoardPyMata( "/dev/ttyACM0")
                ios2.IOBoards().board_add( board=board, id_usr="nano")

                port = arduino.DInpNano( id_sys=Id( 12), board=board, is_hi_active=True, label="Button")
                ios2.IOSystem().dinp_add( id_usr=Id( "button"), port=port)

                port = arduino.DInpNano( id_sys=Id( 11), board=board, is_hi_active=True, label="Encoder pin B")
                ios2.IOSystem().dinp_add( id_usr=Id( "encoderB"), port=port)

                port = arduino.DOutNano( id_sys=Id( 13), board=board, is_hi_active=True, label="LED 13")
                ios2.IOSystem().dout_add( port, Id( "led"))

            return

        def _on_ussdata_( self, data):
            return

        def test__simple_use( self):
            """Blinking LED 13.
            """
            print()

            board = ios2.IOBoards().board( "nano")

            port = ios2.IOSystem().douts( "led")

            t0 = time.time()
            togglevalue = 0
            while time.time() - t0 < 3:
                port.value( togglevalue)
                port.execute()
                togglevalue = 1 - togglevalue

                time.sleep( 0.100)

            port.value( 0).execute()
            return

        def test__normal_use( self):
            """
            """
            print()

            board = ios2.IOBoards().board( "nano")

            ### USS 1
            #
            p_distance_cm = pandora.Box( value=0.0)

            port = arduino.DOutNano( id_sys=Id( 2), board=board, is_hi_active=True, label="USS 1 Triggger")
            ios2.IOSystem().dout_add( port, Id( "uss.1.trigger"))

            port = arduino.DInpNano( id_sys=Id( 3), board=board, is_hi_active=True, label="USS 1 Echo")
            ios2.IOSystem().dinp_add( port, Id( "uss.1.echo"))

            board.uss_config( 2, 3, lambda D: p_distance_cm.value( D[ 1]))

            ### LED und Button
            #
            port_button = ios2.IOSystem().dinps( id_usr="button")
            port_led = ios2.IOSystem().douts( "led")
            t = time.time()
            while time.time() - t <= 3:
                ios2.IOSystem().execute_inps()

                port_led.value( port_button.value())

                ios2.IOSystem().execute_outs()
                print( "USS 1 Distance = %.3f. " % p_distance_cm.value())

                time.sleep( 0.010)

            return

        def test__pulse_counting( self):
            """
            """
            print()

            board = ios2.IOBoards().board( "nano")

            portA = ios2.IOSystem().dinps( "button")
            portB = ios2.IOSystem().dinps( "encoderB")

            encoder = _MotorEncoder( portA, portB)
            t0 = time.time()
            while time.time() - t0 < 3:
                print( "Encoder valueA = '%.3f', encoder valueB = '%.3f'. " % (encoder.valueA(), encoder.valueB()))
                time.sleep( 0.01)

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__arduino_pymata))

if _TEST_2_USS_ON_RASPI:

    class _TESTCASE__raspi_uss(unittest.TestCase):

        """Dieser Testcase läuft nur auf CRUISER.ROVER.
        """

        def test__normal_use( self):
            """
            """
            print()

            rpi = raspi.BoardPi( "raspi")
            ios2.IOBoards().board_add( board=rpi, id_usr="raspi", )
            rpi = ios2.IOBoards().board( "raspi")

            ios2.IOSystem().dout_add( raspi.DOutPi( board=rpi, id_sys=Id( 13), label="Trigger USS 11:00"), "trigger uss 11:00")
            ios2.IOSystem().dinp_add( raspi.DInpPi( board=rpi, id_sys=Id( 15), label="Echo USS 11:00"), "echo uss 11:00")

            ios2.IOSystem().dout_add( raspi.DOutPi( board=rpi, id_sys=Id( 11), label="Trigger USS 13:00"), "trigger uss 13:00")
            ios2.IOSystem().dinp_add( raspi.DInpPi( board=rpi, id_sys=Id( 12), label="Echo USS 13:00"), "echo uss 13:00")

            sensor = sensors.DistancesensorUss_Devantech_SRF04( \
                id=Id( "uss 11:00"),
                actuals=sensordata.ActualsDistancesensor(),
                setup=sensordata.SetupDistancesensorUSS( \
                    is_setup=True,
                    dout_trigger=ios2.IOSystem().douts( "trigger uss 11:00"),
                    dinp_echo=ios2.IOSystem().dinps( "echo uss 11:00"),
                    distance_max=3.0,
                    rTs=T3D.FromEuler()
                )
            )
            sensors.Sensors().ranger_add( sensor)

            sensor = sensors.DistancesensorUss_Devantech_SRF04( \
                id=Id( "uss 13:00"),
                actuals=sensordata.ActualsDistancesensor(),
                setup=sensordata.SetupDistancesensorUSS( \
                    is_setup=True,
                    dout_trigger=ios2.IOSystem().douts( "trigger uss 13:00"),
                    dinp_echo=ios2.IOSystem().dinps( "echo uss 13:00"),
                    distance_max=3.0,
                    rTs=T3D.FromEuler()
                )
            )
            sensors.Sensors().ranger_add( sensor)

            while True:
                ios2.IOSystem().execute_inps()

                sensors.Sensors().execute()

                for sensor in sensors.Sensors().rangers_available():
                    actuals = sensor.actuals()
                    print( "%s: d = %.3f. " % (sensor.id(), actuals.distance()))

                ios2.IOSystem().execute_outs()


            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__raspi_uss))


if _TEST_L293D_AT_RASPI:

    class _TESTCASE__raspi_l293d(unittest.TestCase):

        """Dieser Testcase läuft nur auf CRUISER.ROVER.
        """

        def test__normal_use( self):
            """
            """
            print()

            rpi = raspi.BoardPi( "raspi")
            ios2.IOBoards().board_add( board=rpi, id_usr="raspi", )
            rpi = ios2.IOBoards().board( "raspi")

            enable_1 = raspi.AOutPi( board=rpi, id_sys=Id( 32), label="Motor 1: Enable")
            ios2.IOSystem().aout_add( enable_1, "enable_1")
            input_1 = raspi.DOutPi( board=rpi, id_sys=Id( 19), is_hi_active=True, label="Motor 1: Input 1")
            ios2.IOSystem().dout_add( input_1, "input_1")
            input_2 = raspi.DOutPi( board=rpi, id_sys=Id( 21), is_hi_active=True, label="Motor 1: Input 2")
            ios2.IOSystem().dout_add( input_2, "input_2")

            enable_2 = raspi.AOutPi( board=rpi, id_sys=Id( 33), label="Motor 2: Enable")
            ios2.IOSystem().aout_add( enable_2, "enable_2")
            input_3 = raspi.DOutPi( board=rpi, id_sys=Id( 23), is_hi_active=True, label="Motor 2: Input 1")
            ios2.IOSystem().dout_add( input_3, "input_3")
            input_4 = raspi.DOutPi( board=rpi, id_sys=Id( 24), is_hi_active=True, label="Motor 2: Input 2")
            ios2.IOSystem().dout_add( input_4, "input_4")

            md = l293d.BoardL293D(
                id=Id( "l293d"),
                aout_enable_1=enable_1,
                dout_input_1=input_1,
                dout_input_2=input_2,
                aout_enable_2=enable_2,
                dout_input_3=input_3,
                dout_input_4=input_4
            )
            ios2.MDBoards().board_add( board=md, id_usr="md")
            md = ios2.MDBoards().board( md.id_usr())

#            md.speed_100( 100, 100)
#            ios2.IOSystem().execute_outs()
#            self._wait_( 10.0)

            for speed_100 in range( 0, 101, 10):
                ios2.IOSystem().execute_inps()

                md.speed_100( speed_100, speed_100)
                print( "speed_100 = %d. " % speed_100)

                ios2.IOSystem().execute_outs()

                time.sleep( 1)

            ios2.IOSystem().reset()
            return

        def _wait_( self, secs):
            t0 = time.time()
            while time.time() - t0 <= secs:
                time.sleep( 0.100)

            return


    _Testsuite.addTest( unittest.makeSuite( _TESTCASE__raspi_l293d))


class _TESTCASE__devantech(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__devantech))


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



