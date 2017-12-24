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

### Python
#
import abc
import logging; _Logger = logging.getLogger()

### TAU4
#
from tau4 import Id
from tau4 import ios2
from tau4.ios2._common import MotorDriver
from tau4.oop import overrides, Singleton
import time

### 3RD PARTY
#
import explorerhat


class BoardXHP(MotorDriver):

    """Ein konkretes Board, das gleichzeitig auch MotorDriver ist.
    """

    def __init__( self):
        self.__sysdinps = {\
            1: explorerhat.input.one,
            2: explorerhat.input.two,
            3: explorerhat.input.three,
            4: explorerhat.input.four
        }
        self.__sysdouts = {\
            1: explorerhat.output.one,
            2: explorerhat.output.two,
            3: explorerhat.output.three,
            4: explorerhat.output.four
        }

        self.__bouncetime_ms = 1
        return

    def ainp_value( self):
        raise NotImplementedError( "2DO")

    def aout_value( self, value):
        raise NotImplementedError( "2DO")

    def callback_on_dinp_change( self, id_sys, callable):
        pin = self.__sysdinps[ id_sys]
        pin.on_changed( callback=callable, bouncetime=self.__bouncetime_ms)
        return self

    def callback_on_dinp_high( self, id_sys, callable):
        pin = self.__sysdinps[ id_sys]
        pin.on_high( callback=callable, bouncetime=self.__bouncetime_ms)
        return self

    def callback_on_dinp_low( self, id_sys, callable):
        pin = self.__sysdinps[ id_sys]
        pin.on_low( callback=callable, bouncetime=self.__bouncetime_ms)
        return self

    def callbacks_clear( self, id_sys):
        pin = self.__sysdinps[ id_sys]
        pin.clear_events()
        return self

    def dinp_value( self, id_sys):
        this_name = "BoardXHP::dinp_value"
        value = self.__sysdinps[ id_sys].read()
        _Logger.debug( "%s(): DInp '%s's value = '%d'. ", this_name, id_sys, value)
        return value

    def dout_value( self, id_sys, value):
        """Ausgang schreiben.

        \note   Ob der Ausgang hi- oder lo-aktiv ist, entscheidet DOutXHP!
        """
        this_name = "BoardXHP::dout_value"
        _Logger.debug( "%s(): DOut '%s's value = '%d'. ", this_name, id_sys, value)
        self.__sysdouts[ id_sys].write( value)
        return self

    @overrides(MotorDriver)
    def speed_100( self, lhs, rhs):
        this_name = "BoardXHP::speed_100"
        _Logger.debug( "%s(): E n t e r e d. ", this_name)
        if self.is_direction_inverted():
            lhs, rhs = -rhs, -lhs

        if lhs is not None:
            lhs = lhs/100*self.speed_max_100()
            explorerhat.motor.one.speed( lhs)
                                            # Nimmt die Speed in %
        if rhs is not None:
            rhs = rhs/100*self.speed_max_100()
            explorerhat.motor.two.speed( rhs)
                                            # Nimmt die Speed in %
        _Logger.debug( "%s(): Exit now.\n", this_name)
        return


class DInpXHP(ios2.DInp):

    """

    \param  id_sys  Id, wie sie die effektive Hardware erwartet: 1, 2, 3 oder 4.

    """

    def __init__( self, *, board: BoardXHP, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board
        return

    def add_event_detect_falling( self, callback):
        assert callable( callback)
        self.__board.callback_on_dinp_low( self.id_sys(), callback)
        return

    def add_event_detect_rising( self, callback):
        assert callable( callback)
        self.__board.callback_on_dinp_high( self.id_sys(), callback)
        return

    def clear_events( self):
        self.__board.callbacks_clear( self.id_sys())

    def port2box( self):
        """Downcall to subclass, called by DInp::execute.
        """
        this_name = "DInpXHP::port2box"
        _Logger.debug( "%s(): E n t e r e d. ", this_name)
        value = self.__board.dinp_value( self.id_sys())
        value = 0 if value is None else int( value)
        value = value if self._is_hi_active else 1 - value
        self.value( value)
        _Logger.debug( "%s(): Exit now.\n", this_name)
        return self

    def wait_for_falling_edge( self, timeout_ms):
        """Auf fallende Flanke warten.

        \returns    True    wenn die Flanke detektiert worden ist.
        \returns    False   bei Timeout

        \_2DO
            Ändern: Arbeitet jetzt noch mit Polling. Wie macht man das mit dem
            Explorer HAT Pro? -> GPIO-Lib analysieren!
        """
        this_name = "DInpXHP::wait_for_falling_edge"
        _Logger.debug( "%s(): E n t e r e d.", this_name)
        timeout = timeout_ms/1000
        id_sys = self.id_sys()
        value_last = self.__board.dinp_value( id_sys)
        t = time.time()
        while time.time() - t <= timeout:
            value = self.__board.dinp_value( id_sys)
            if value - value_last == -1:
                _Logger.debug( "%s(): Falling edge detected, exit now.\n", this_name)
                return True

            value_last = value
            time.sleep( 0.0001)

        _Logger.debug( "%s(): Timeout, exit now.\n", this_name)
        return False


class DOutXHP(ios2.DOut):

    def __init__( self, *, board: BoardXHP, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self.__board = board
        return

    def box2port( self):
        """Downcall to subclass, called by DOut::execute.
        """
        this_name = "DOutXHP::box2port"
        _Logger.debug( "%s(): E n t e r e d. ", this_name)
        value = self.value()
        _Logger.debug( "%s(): The box's value = %d. ", this_name, value)
        value = value if self._is_hi_active else 1 - value
        _Logger.debug( "%s(): The value written to the port = %d. ", this_name, value)
        self.__board.dout_value( self.id_sys(), value)
        _Logger.debug( "%s(): Exit now.\n", this_name)
        return self


def main():
    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")
