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
import time

from tau4 import Id
from tau4 import ios2
from tau4.ios2._common import MotorDriver
from tau4.oop import overrides, Singleton


def _Signum_( x):
    return 1 if x >= 0 else -1


class BoardL293D(MotorDriver):

    """Kein konkretes Board, sondern eher ein virtuelles: Der nackte L293D.

    \param  is_setup    Nicht nicht belegt.
    """

    def __init__( self, *,
            id: Id,
            aout_enable_1: ios2.AOut,
            dout_input_1: ios2.DOut,
            dout_input_2: ios2.DOut,
            aout_enable_2: ios2.AOut,
            dout_input_3: ios2.DOut,
            dout_input_4: ios2.DOut,
            is_setup=True
        ):
        super().__init__( id=id)
        self.__aout_enable_1 = aout_enable_1
        self.__dout_input_1 = dout_input_1
        self.__dout_input_2 = dout_input_2
        self.__aout_enable_2 = aout_enable_2
        self.__dout_input_3 = dout_input_3
        self.__dout_input_4 = dout_input_4
        return

    def _enable_1_100_( self, speed_100):
        """Speed in %.

        Rechnet die % in Echtwerte um und schreibt sie auf den Ausgang.
        """
        speed = speed_100
                                        # Angeg, werden %. Wenn 100% auf den
                                        #   Ausgang gehen, entspricht das VSS
                                        #   des L293D und damit Full Speed etc.
        _Logger.debug( "%s::%s(): Write speed = '%.3f' to ENABLE 1. ", self.__class__.__name__, "_enable_1_100_", speed)
        self.__aout_enable_1.value( speed)
                                        # Dieser Wert wird nicht instantan auf
                                        #   den Ausgang gelegt. Das erfolg erst,
                                        #   wenn ios2.IOSystem().execute_outs()
                                        #   ausgeführt wird!
        return

    def _enable_2_100_( self, speed_100):
        """Speed in %.

        Rechnet die % in Echtwerte um und schreibt sie auf den Ausgang.
        """
        speed = speed_100
                                        # Angeg, werden %. Wenn 100% auf den
                                        #   Ausgang gehen, entspricht das VSS
                                        #   des L293D und damit Full Speed etc.
        _Logger.debug( "%s::%s(): Write speed = '%.3f' to ENABLE 2. ", self.__class__.__name__, "_enable_2_100_", speed)
        self.__aout_enable_2.value( speed)
                                        # Dieser Wert wird nicht instantan auf
                                        #   den Ausgang gelegt. Das erfolg erst,
                                        #   wenn ios2.IOSystem().execute_outs()
                                        #   ausgeführt wird!
        return

    def _input12_bwd_( self):
        _Logger.debug( "%s::%s(): Write (1, 0) to (INPUT 1, INPUT 2). ", self.__class__.__name__, "_input12_bwd_")
        self.__dout_input_1.value( 1)
        self.__dout_input_2.value( 0)
        return

    def _input12_fwd_( self):
        _Logger.debug( "%s::%s(): Write (0, 1) to (INPUT 1, INPUT 2). ", self.__class__.__name__, "_input12_fwd_")
        self.__dout_input_1.value( 0)
        self.__dout_input_2.value( 1)
        return

    def _input34_bwd_( self):
        _Logger.debug( "%s::%s(): Write (1, 0) to (INPUT 3, INPUT 4). ", self.__class__.__name__, "_input34_bwd_")
        self.__dout_input_3.value( 1)
        self.__dout_input_4.value( 0)
        return

    def _input34_fwd_( self):
        _Logger.debug( "%s::%s(): Write (0, 1) to (INPUT 3, INPUT 4). ", self.__class__.__name__, "_input34_fwd_")
        self.__dout_input_3.value( 0)
        self.__dout_input_4.value( 1)
        return

#    def _map_x2y_( self, x, x0=10, y0=80):
#        """Bildet den Bereich [x0, 100] auf den Bereich [y0, 100] ab.
#        """
#        y = 0
#        if abs( x) >= x0:
#            y = (100 - y0)/(100 - x0)*(x - x0*_Signum_( x)) + y0*_Signum_( x)
#
#        return y
    def _map_x2y_( self, x, x0=10, y0=20):
        """Bildet den Bereich [x0, 100] auf den Bereich [y0, 100] ab.
        """
        x = abs( x)
        y = 0
        if x >= x0:
            y = (100 - y0)/(100 - x0)*(x - x0) + y0

        return y

    @overrides(MotorDriver)
    def speed_100( self, lhs, rhs):
        _Logger.debug( "%s::%s(): (lhs, rhs) = (%.3f, %.3f). ", self.__class__.__name__, "speed_100", lhs, rhs)
        if self.is_direction_inverted():
                                            # Falls das Motorpaar verkehrt herum
                                            #   eingebaut worden ist.
            lhs, rhs = -rhs, -lhs

        if lhs is not None:
            if lhs >= 0:
                self._input12_fwd_()

            else:
                self._input12_bwd_()

            lhs = lhs/100*self.speed_max_100()
            LHS = self._map_x2y_( lhs)
            _Logger.debug( "%s::%s(): LHS = %.3f. ", self.__class__.__name__, "speed_100", LHS)
            self._enable_1_100_( LHS)

        if rhs is not None:
            if rhs >= 0:
                self._input34_fwd_()

            else:
                self._input34_bwd_()

            rhs = rhs/100*self.speed_max_100()
            RHS = self._map_x2y_( rhs)
            _Logger.debug( "%s::%s(): RHS = %.3f. ", self.__class__.__name__, "speed_100", RHS)
            self._enable_2_100_( RHS)

        return


def main():
    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")
