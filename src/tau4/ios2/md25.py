#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2017
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

import abc
from tau4 import Id
from tau4 import ios2
from tau4.ios2._common import MotorDriver
from tau4.oop import overrides, Singleton
import time


class _MD25 :
    """Originally written by Paul Payne (see https://github.com/payneio/md25_motor_controller_library/blob/master/MD25.py) and copied here to be extended so that my needs are met.
    """

    i2c = None

    # Operating Modes
    __MD25_STANDARD                 = 0
    __MD25_NEGATIVE_SPEEDS          = 1
    __MD25_SPEED_AND_TURN           = 2
    __MD25_NEGATIVE_SPEEDS_AND_TURN = 3

    # MD25 Registers
    _MD25_SPEED_1 = 0
    _MD25_SPEED_2 = 1
    __MD25_ENC_1A = 2
    __MD25_ENC_1B = 3
    __MD25_ENC_1C = 4
    __MD25_ENC_1D = 5
    __MD25_ENC_2A = 6
    __MD25_ENC_2B = 7
    __MD25_ENC_2C = 8
    __MD25_ENC_2D = 9
    __MD25_BATTERY_VOLTAGE = 10
    __MD25_MOTOR_1_CURRENT = 11
    __MD25_MOTOR_2_CURRENT = 12
    __MD25_SOFTWARE_VERSION = 13
    __MD25_ACCELERATION = 14
    __MD25_MODE = 15
    __MD25_COMMAND = 16

    __MD25_RESET_ENCODER_REGISTERS = 0x20
    __MD25_DISABLE_AUTO_SPEED_REGULATION = 0x30
    __MD25_ENABLE_AUTO_SPEED_REGULATION = 0x31
    __MD25_DISABLE_2_SECOND_TIMEOUT = 0x32
    __MD25_ENABLE_2_SECOND_TIMEOUT = 0x33
    __MD25_CHANGE_I2C_ADDRESS_1 = 0xA0
    __MD25_CHANGE_I2C_ADDRESS_2 = 0xAA
    __MD25_CHANGE_I2C_ADDRESS_3 = 0xA5


    # Private Fields
    _enc_1a = 0
    _enc_1b = 0
    _enc_1c = 0
    _enc_1d = 0
    _enc_2a = 0
    _enc_2b = 0
    _enc_2c = 0
    _enc_2d = 0
    _battery_voltage = 0
    _motor_1_current = 0
    _motor_2_current = 0
    _software_revision = 0


    # Constructor
    def __init__( self, address=0x58, mode=1, debug=False):
        from tau4.ios2._devantech.Adafruit_I2C import Adafruit_I2C
        self.i2c = Adafruit_I2C( address)

        self.address = address
        self.debug = debug # Make sure the specified mode is in the appropriate range
        if ((mode < 0) | (mode > 3)):
            if (self.debug):
                print( "Invalid Mode: Using STANDARD by default")

            self.mode = self.__MD25_STANDARD
        else:
            self.mode = mode
        self.showBatteryVoltage()
        self.readData()

    def forward(self, speed=255):
        self.i2c.write8(self._MD25_SPEED_1, speed)
        self.i2c.write8(self._MD25_SPEED_2, speed)

    def stop(self):
        self.i2c.write8(self._MD25_SPEED_1, 128)
        self.i2c.write8(self._MD25_SPEED_2, 128)

    def turn(self, speed1=255, speed2=1):
        self.i2c.write8(self._MD25_SPEED_1, speed1)
        self.i2c.write8(self._MD25_SPEED_2, speed2)

    def showBatteryVoltage(self):
        "Reads the battery voltage"
        print( "DBG: BATTERY_VOLTAGE = %6d" % (self._battery_voltage))

    def readData(self):
        "Reads the data from the MD25"
        self._enc_1a = self.i2c.readS8(self.__MD25_ENC_1A)
        if (self.debug):
            self.showData()

    def showData(self):
        "Displays the calibration values for debugging purposes"
        print( "DBG: ENC_1A = %6d" % (self._enc_1a))

    def readTemperature(self):
        "Gets the compensated temperature in degrees celcius"
        UT = 0
        X1 = 0
        X2 = 0
        B5 = 0
        temp = 0.0

        # Read raw temp before aligning it with the calibration values
        UT = self.readRawTemp()
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) >> 15
        X2 = (self._cal_MC << 11) / (X1 + self._cal_MD)
        B5 = X1 + X2
        temp = ((B5 + 8) >> 4) / 10.0
        if (self.debug):
            print( "DBG: Calibrated temperature = %f C" % temp)

        return temp

    def readPressure(self):
        "Gets the compensated pressure in pascal"
        UT = 0
        UP = 0
        B3 = 0
        B5 = 0
        B6 = 0
        X1 = 0
        X2 = 0
        X3 = 0
        p = 0
        B4 = 0
        B7 = 0

        UT = self.readRawTemp()
        UP = self.readRawPressure()

        # You can use the datasheet values to test the conversion results
        # dsValues = True
        dsValues = False

        if (dsValues):
            UT = 27898
            UP = 23843
            self._cal_AC6 = 23153
            self._cal_AC5 = 32757
            self._cal_MC = -8711
            self._cal_MD = 2868
            self._cal_B1 = 6190
            self._cal_B2 = 4
            self._cal_AC3 = -14383
            self._cal_AC2 = -72
            self._cal_AC1 = 408
            self._cal_AC4 = 32741
            self.mode = self.__MD25_ULTRALOWPOWER
            if (self.debug):
                self.showCalibrationData()

        # True Temperature Calculations
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) >> 15
        X2 = (self._cal_MC << 11) / (X1 + self._cal_MD)
        B5 = X1 + X2
        if (self.debug):
            print( "DBG: X1 = %d" % (X1))
            print( "DBG: X2 = %d" % (X2))
            print( "DBG: B5 = %d" % (B5))
            print( "DBG: True Temperature = %.2f C" % (((B5 + 8) >> 4) / 10.0))

        # Pressure Calculations
        B6 = B5 - 4000
        X1 = (self._cal_B2 * (B6 * B6) >> 12) >> 11
        X2 = (self._cal_AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = (((self._cal_AC1 * 4 + X3) << self.mode) + 2) / 4
        if (self.debug):
            print( "DBG: B6 = %d" % (B6))
            print( "DBG: X1 = %d" % (X1))
            print( "DBG: X2 = %d" % (X2))
            print( "DBG: B3 = %d" % (B3))

        X1 = (self._cal_AC3 * B6) >> 13
        X2 = (self._cal_B1 * ((B6 * B6) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self._cal_AC4 * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self.mode)
        if (self.debug):
            print( "DBG: X1 = %d" % (X1))
            print( "DBG: X2 = %d" % (X2))
            print( "DBG: B4 = %d" % (B4))
            print( "DBG: B7 = %d" % (B7))

        if (B7 < 0x80000000):
            p = (B7 * 2) / B4
        else:
            p = (B7 / B4) * 2

        X1 = (p >> 8) * (p >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7375 * p) >> 16
        if (self.debug):
            print( "DBG: p  = %d" % (p))
            print( "DBG: X1 = %d" % (X1))
            print( "DBG: X2 = %d" % (X2))

        p = p + ((X1 + X2 + 3791) >> 4)
        if (self.debug):
            print( "DBG: Pressure = %d Pa" % (p))

        return p

    def readAltitude(self, seaLevelPressure=101325):
        "Calculates the altitude in meters"
        altitude = 0.0
        pressure = float(self.readPressure())
        altitude = 44330.0 * (1.0 - pow(pressure / seaLevelPressure, 0.1903))
        if (self.debug):
            print( "DBG: Altitude = %d" % (altitude))

        return altitude


class BoardMD25(_MD25, MotorDriver):

    """Ein konkretes Board.

    IOs sind nicht notwendig, weil die Kommunikation über I2C erfolgt.
    """

    def __init__( self, *, id, address=0x58, mode=1, debug=False, is_setup=True):
        try:
            _MD25.__init__( self, address, mode, debug)

        except FileNotFoundError:
            if is_setup:
                raise

            self._i2c_write8_ = self._i2c_write8_dummy_

        MotorDriver.__init__( self, id=id)
        return

    def _i2c_write8_( self, reg, value):
        self.i2c.write8( reg, value)
        return self

    def _i2c_write8_dummy_( self, reg, value):
        return self

    @overrides(MotorDriver)
    def speed_100( self, lhs, rhs):
        if self.is_direction_inverted():
            lhs, rhs = -rhs, -lhs

        if lhs is not None:
            lhs = lhs/100*self.speed_max_100()
            LHS = int( 255/200*lhs + 127.5)
            self._i2c_write8_( self._MD25_SPEED_1, LHS)

        if rhs is not None:
            rhs = rhs/100*self.speed_max_100()
            RHS = int( 255/200*rhs + 127.5)
            self._i2c_write8_( self._MD25_SPEED_2, RHS)

        return


def main():
    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")