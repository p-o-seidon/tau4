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
import logging; _Logger = logging.getLogger()
import os
import platform
import threading

from tau4 import Id
from tau4 import ios2
from tau4.data import pandora
from tau4.oop import Singleton
import time

if platform.uname()[ 4].startswith( "x86"):
    pass

else:
    import pigpio
    import wiringpi


class PinoutTranslator:

    def __init__( self):
        self.__pn_bcm = { \
            3: 2,
            5: 3,
            7: 4,
            8: 14,
            10: 15,
            11: 17,
            12: 18,
            13: 27,
            15: 22,
            16: 23,
            18: 24,
            19: 10,
            21: 9,
            22: 25,
            23: 11,
            24: 8,
            26: 7,
            27: 0,
            28: 1,
            29: 5,
            31: 6,
            32: 12,
            33: 13,
            35: 19,
            36: 16,
            37: 26,
            38: 20,
            40: 21,
        }

        self.__pn_wpi = { \
            3: 8,
            5: 9,
            7: 7,
            8: 15,
            10: 16,
            11: 0,
            12: 1,
            13: 2,
            15: 3,
            16: 4,
            18: 5,
            19: 12,
            21: 13,
            22: 6,
            23: 14,
            24: 10,
            26: 11,
            27: 30,
            28: 31,
            29: 21,
            31: 22,
            32: 26,
            33: 23,
            35: 24,
            36: 27,
            37: 25,
            38: 28,
            40: 29,
        }

        self.__pinnmbr_physical_by_bcm = {}
        for pinnmbr_physical, pinnmbr_bcm in self.__pn_bcm.items():
            self.__pinnmbr_physical_by_bcm[ pinnmbr_bcm] = pinnmbr_physical

        return

    def pn_bcm( self, pn_physical):
        return self.__pn_bcm[ int( pn_physical)]

    def pn_physical_from_bcm( self, pn_bcm):
        return self.__pinnmbr_physical_by_bcm[ int( pn_bcm)]

    def pn_wpi( self, pn_physical):
        return self.__pn_wpi[ int( pn_physical)]


################################################################################
###
#
class BoardWPi(ios2.IOBoard):

    def __init__( self, id_usr):
        super().__init__( id_usr)

        wiringpi.wiringPiSetupPhys()

        _Logger.info( "BoardPi::__init__(): Exit now.\n")
        return

    def ainp_value( self, id_sys):
        raise NotImplementedError( "2DO")

    def aout_value( self, id_sys, value: float):
        """Analogwert auf Ausgang schreiben.

        Ausführung durch box2port() von AOut.

        \param  id_sys  Id, unter der der Pin vom konkreten Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden soll. <b>Der Wert ist in % anzugeben.</b>
        """
        assert isinstance( value, (int, float)), "type( value) == '%s' != one of (int, float)!" % type( value)

        id_sys = int( id_sys)
        wiringpi.softPwmWrite( int( id_sys), int( value))
        return self

    def dinp_value( self, id_sys):
        value = wiringpi.digitalRead( int( id_sys))
        value = int( value)
        return value

    def dout_value( self, id_sys, value):
        """Digital auf Ausgang schreiben.

        Ausführung durch box2port() von DOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden soll. <b>Der Wert ist in % anzugeben.</b>
        """
        wiringpi.digitalWrite( int( id_sys), value)
        return self


class AOutWPi(ios2.AOut):

    def __init__( self, *, board: BoardWPi, id_sys: Id, label: str):
        super().__init__( id_sys=id_sys, label=label)

        self.__board = board
        wiringpi.pinMode( int( id_sys), wiringpi.OUTPUT)
        wiringpi.softPwmCreate( int( id_sys), 0, 100)
                                        # # 0..100%
        return

    def box2port( self):
        value = self.value()
        self.__board.aout_value( self.id_sys(), value)
        return self


class DInpWPi(ios2.DInp):

    def __init__( self, *, board: BoardWPi, id_sys: Id, is_hi_active: bool, activate_pulldown: bool, label: str):
        super().__init__( "wiringpi", id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board
        if activate_pulldown:
            wiringpi.pinMode( int( id_sys), 0)
            wiringpi.pullUpDnControl( int( id_sys), wiringpi.PUD_DOWN)

        else:
            wiringpi.pinMode( int( id_sys), 0)

        self.__is_prepared_for_waiting_for_falling_edge = False

        return

    def add_event_detect_falling( self, callable):
        wiringpi.wiringPiISR( int( self.id_sys()), wiringpi.INT_EDGE_FALLING, callable)
        return self

    def add_event_detect_rising( self, callable):
        wiringpi.wiringPiISR( int( self.id_sys()), wiringpi.INT_EDGE_RISING, callable)
        return self

    def port2box( self):
        value = self.__board.dinp_value( self.id_sys())
        value = 0 if value is None else int( value)
        value = value if self._is_hi_active else 1 - value
        self.value( value)
        return self

    def wait_for_falling_edge( self, timeout_ms):
        """Auf falende Flanke warten.

        Verwendet waitForInterrupt, das -1 für Fehler, 0 für Timeout und 1 für
        Erfolg retourniert. Per 2017-09-14 wird allerdings ein undokumentiertes
        -2 retourniert.

        Es wird nicht mehr empfohlen, die Funktion zu verwenden, sondern wiringPiISR.
        """
        if not self.__is_prepared_for_waiting_for_falling_edge:
            os.system( "gpio edge %d falling" % self.id_sys())
            self.__is_prepared_for_waiting_for_falling_edge = True

        return wiringpi.waitForInterrupt( int( self.id_sys()), timeout_ms)


class DOutWPi(ios2.DOut):

    def __init__( self, *, board: BoardWPi, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board
        wiringpi.pinMode( int( id_sys), 1)
        return

    def box2port( self):
        value = self.value()
        value = value if self._is_hi_active else 1 - value
        self.__board.dout_value( self.id_sys(), value)
        return self


################################################################################
###
#
class BoardPi(ios2.IOBoard):

    def __init__( self, id_usr):
        super().__init__( id_usr)

        this_name = "__init__"

        self.__pigpio = pigpio.pi()
        if self.__pigpio.connected:
            _Logger.info( "%s.%s(): Connected to pigpio. ", self.__class__.__name__, this_name)

        else:
            _Logger.critical( "%s.%s(): E R R O R   connecting to pigpio. ", self.__class__.__name__, this_name)

        self.__pnt = PinoutTranslator()

        _Logger.info( "%s.%s(): Exit now.\n", self.__class__.__name__, this_name)
        return

    def _add_event_detect_falling_( self, id_sys, callable):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.callback( id_sys, pigpio.FALLING_EDGE, callable)
        return

    def _add_event_detect_rising_( self, id_sys, callable):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.callback( id_sys, pigpio.RISING_EDGE, callable)
        return

    def ainp_value( self, id_sys):
        raise NotImplementedError( "2DO")

    def aout_value( self, id_sys, value_100: float):
        """Analogwert in % auf Ausgang schreiben.

        Ausführung durch box2port() von AOut.

        \param  id_sys      Id, unter der der Pin vom konkreten Board angesprochen wird.
        \param  value_100   Wert, der auf den Pin geschrieben werden soll.
                <b>Der Wert ist in % anzugeben.</b>
        """
        assert isinstance( value_100, (int, float)), "type( value_100) == '%s' != one of (int, float)!" % type( value_100)

        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.set_PWM_dutycycle( id_sys, value_100/100*255)
        return self

    def dinp_value( self, id_sys):
        id_sys = self.__pnt.pn_bcm( id_sys)
        value = self.__pigpio.read( id_sys)
        value = int( value)
        return value

    def dout_value( self, id_sys, value):
        """Digital auf Ausgang schreiben.

        Ausführung durch box2port() von DOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden soll. <b>Der Wert ist in % anzugeben.</b>
        """
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.write( id_sys, int( value))
        return self

    def _pinmode_to_input_( self, id_sys):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.set_mode( id_sys, pigpio.INPUT)
        return

    def _pinmode_to_output_( self, id_sys):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.set_mode( id_sys, pigpio.OUTPUT)
        return

    def _pinmode_to_pulldown_( self, id_sys):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.set_pull_up_down( id_sys, pigpio.PUD_DOWN)
        return

    def _pinmode_to_pullup_( self, id_sys):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.set_pull_up_down( id_sys, pigpio.PUD_UP)
        return

    def _wait_for_falling_edge_( self, id_sys, timeout_ms):
        id_sys = self.__pnt.pn_bcm( id_sys)
        self.__pigpio.wait_for_edge( id_sys, pigpio.FALLING_EDGE, timeout_ms/1000)
        return


class AOutPi(ios2.AOut):

    def __init__( self, *, board: BoardPi, id_sys: Id, label: str):
        super().__init__( id_sys=id_sys, label=label)

        self.__board = board
        self.__board._pinmode_to_output_( id_sys)
        return

    def box2port( self):
        value = self.value()
        self.__board.aout_value( self.id_sys(), value)
        return self


class DInpPi(ios2.DInp):

    def __init__( self, *, board: BoardPi, id_sys: Id, is_hi_active: bool, activate_pulldown: bool, label: str):
        super().__init__( "pigpio", id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board

        self.__board._pinmode_to_input_( id_sys)
        if activate_pulldown:
            self.__board._pinmode_to_pulldown_( id_sys)

        return

    def add_event_detect_falling( self, callable):
        self.__board._add_event_detect_falling_( self.id_sys(), callable)
        return self

    def add_event_detect_rising( self, callable):
        self.__board._add_event_detect_rising_( self.id_sys(), callable)
        return self

    def port2box( self):
        value = self.__board.dinp_value( self.id_sys())
        value = 0 if value is None else int( value)
        value = value if self._is_hi_active else 1 - value
        self.value( value)
        return self

    def wait_for_falling_edge( self, timeout_ms):
        """Auf fallende Flanke warten.

        Verwendet waitForInterrupt, das -1 für Fehler, 0 für Timeout und 1 für
        Erfolg retourniert. Per 2017-09-14 wird allerdings ein undokumentiertes
        -2 retourniert.

        Es wird nicht mehr empfohlen, die Funktion zu verwenden, sondern wiringPiISR.
        """
        success = 0 != self.__board._wait_for_falling_edge_( self.id_sys(), timeout_ms)
        return success


class DInpPiEncoder(ios2.DInp):

    """DInp, dessen Status überwacht wird; bei Statusänderungen erfolgt die Ausführung eines Callbacks, der den Tick Count entsprechend erhöht, der wiederum per DInpPiEncoder.p_value() abgefragt werden kann.

    \param  board

    \param  id_sys
        Id, wie sie die Hardware versteht, wobei das Schema "Board" ist und nicht
        "Broadcom" ("BCM")!

    \param  pulldirection
        -1...Pull-down aktivieren; 0...Weder Pull-down noch Pull-up aktivieren; 1...Pull-up aktivieren.

    \param  label   Für Anzeigen.
    """

    class CallbackFunctor:

        def __init__( self):
            self.__pinouttranslator = PinoutTranslator()

            self.__p_tickcount = pandora.Box( value=0)
            self.__p_tickcount_last = pandora.Box( value=0)
            self.__p_ticks_per_second = pandora.Box( value=0)
            self.__time_last = 0
            return

        def __call__( self, pinnmbr_bcm, level, tickcount):
            if level == 1:
                pinnmbr_physical = self.__pinouttranslator.pn_physical_from_bcm( pinnmbr_bcm)
                self.__p_tickcount.value( tickcount)

            return

        def p_tickcount( self):
            """pandora.Box: Ticks seit Einschalten.
            """
            return self.__p_tickcount

        def p_ticks_per_second( self):
            """pandora.Box: Ticks pro Sekunde; Neueberechnung bei jeder Ausführung.
            """
            di = pigpio.tickDiff( self.__p_tickcount_last.value(), self.__p_tickcount.value())
            t = time.time()
            dt = t - self.__time_last
            self.__p_ticks_per_second.value( di/dt)

            self.__time_last = t
            self.__p_tickcount_last.value( self.__p_tickcount.value())
            return self.__p_ticks_per_second

        def tickcount( self):
            """Ticks seit Einschalten.
            """
            return self.__p_tickcount.value()

        def ticks_per_second( self):
            """Ticks pro Sekunde; Neuberechnung bei jeder Ausführung.
            """
            return self.__p_ticks_per_second.value()




    def __init__( self, *, board: BoardPi, id_sys: Id, pulldirection: int, label: str):
        super().__init__( "pigpio", id_sys=id_sys, is_hi_active=True, label=label)

        self.__board = board

        self.__board._pinmode_to_input_( id_sys)
        if pulldirection < 0:
            self.__board._pinmode_to_pulldown_( id_sys)

        elif pulldirection > 0:
            self.__board._pinmode_to_pullup_( id_sys)

        else:
            pass

        self.__callbackfunctor = DInpPiEncoder.CallbackFunctor()
        self.__board._add_event_detect_rising_( id_sys, self.__callbackfunctor)
        return

    def p_tickcount( self):
        """pandora.Box: Ticks seit Einschalten.
        """
        return self.__callbackfunctor.p_tickcount()

    def p_ticks_per_second( self):
        """pandora.Box: Ticks pro Sekunde; Neueberechnung bei jeder Ausführung.
        """
        return self.__callbackfunctor.p_ticks_per_second()

    def port2box( self):
        """Kopiert den Tick Count in die pandora.Box (Abruf durch self.p_value()); Ausführung durch IOSystem().execute_inps(), das hierzu von der App auszuführen ist.
        """
        value = self.__callbackfunctor.tickcount()
        self.value( value)
        return self


class DOutPi(ios2.DOut):

    def __init__( self, *, board: BoardPi, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board

        self.__board._pinmode_to_output_( id_sys)
        return

    def box2port( self):
        value = self.value()
        value = value if self._is_hi_active else 1 - value
        self.__board.dout_value( self.id_sys(), value)
        return self


BoardPi = BoardPi
AInpPi = None  # 2DO
AOutPi = AOutPi
DInpPi = DInpPi
DOutPi = DOutPi


################################################################################
###
#
class MotorEncoder(ios2.MotorEncoder):

    """Single-Signal Encoder.

    \param  dinp    Encoder-DInp auf dem RasPi.
    """

    def __init__( self, dinp: DInpPiEncoder):
        self.__dinp = dinp
        return

    def encoderticks( self):
        """Encoder-Ticks seit Einschalten
        """
        v = self.__dinp.p_tickcount().value()
        return v

    def encoderticks_per_second( self):
        """Encoder-Ticks pro Sekunde.
        """
        v = self.__dinp.p_ticks_per_second().value()
        return v




################################################################################
###
#
def main():
    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")
