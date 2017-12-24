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


class BoardNoMD(MotorDriver):

    """Ein konkretes Board.

    IOs sind nicht notwendig, weil die Kommunikation über I2C erfolgt.
    """

    def __init__( self, *, id, address=0x58, mode=1, debug=False, is_setup=True):
        MotorDriver.__init__( self, id=id)
        return


    @overrides(MotorDriver)
    def speed_100( self, lhs, rhs):
        pass

