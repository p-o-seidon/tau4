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
from tau4.data import pandora
from tau4.ios2 import AInp, AOut, DInp, DOut
from tau4.oop import Singleton

from tau4.ios2.labjack import u3


class Boards(metaclass=Singleton):

    def __init__( self):
        self.__boards = {}
        return

    def board_add( self, board, id_usr: Id):
        if id_usr in self.__boards.keys():
            raise KeyError( "LabJack '%s' was already created! Use Boards().board( id_usr='%s') to get at it!" % (id_usr, id_usr))

        self.__boards[ id_usr] = board
        return self

    def board( self, id_usr: Id):
        return self.__boards[ id_usr]


class BoardU3:

    def __init__( self, labjack=None):
        """Create a LabJack, but don't add it to the pool of LabJacks.
        """
        super().__init__()

        self.__id = id

        self.__board = labjack if labjack else u3.U3()
        self.__board.getCalibrationData()

        self.__ionmbrs = {\
            "dac0": 0,
            "dac1": 1,

            "ain0": 0,
            "ain1": 1,
            "ain2": 2,
            "ain3": 3,

            "fio0": 0,
            "fio1": 1,
            "fio2": 2,
            "fio3": 3,
            "fio4": 4,
            "fio5": 5,
            "fio6": 6,
            "fio7": 7,

            "eio0": 8,
            "eio1": 9,
            "eio2": 10,
            "eio3": 11,
            "eio4": 12,
            "eio5": 13,
            "eio6": 14,
            "eio7": 15,

            "cio1": 16,
            "cio2": 17,
            "cio3": 18,
            "cio4": 19,
            }

        return


    def ainp_value( self, id_sys: Id):
        value = self.__board.getFIOState( id_sys)
        #value = self.getAIN( id_sys)
        # ##### Nehmen das hier, wenn obiges nicht funzt.
        return value

    def aout_value( self, id_sys, value):
        #self.__device.setFIOState( self.ionmbr( self.ionmbr( id_sys)), value)
        value4dac = self.__board.voltageToDACBits( value, self.ionmbr( id_sys), is16Bits=False)
        self.__board.getFeedback( u3.DAC0_8( value4dac))
        return self

    def configAnalog( self, id_sys=None):
        """Configure this pin as a digital IO or get its config.

        id_sys is one of
        "FIO0", "FIO1", "FIO2", "FIO3", "FIO4", "FIO5", "FIO6", "FIO7", \
        "EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", \
        "CIO0", "CIO1", "CIO2", "CIO3"
        """
        if id_sys is None:
            return self.__board.configAnalog()

        return self.__board.configAnalog( self.ionmbr( id_sys))
        #return self.__board.configAnalog( id_sys)

    def configDigital( self, id_sys=None):
        """Configure this pin as a digital IO or get its config.

        id_sys is one of
        "FIO0", "FIO1", "FIO2", "FIO3", "FIO4", "FIO5", "FIO6", "FIO7", \
        "EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", \
        "CIO0", "CIO1", "CIO2", "CIO3"
        """
        if id_sys is None:
            return self.__board.configDigital()

        return self.__board.configDigital( self.ionmbr( id_sys))
        #return self.__board.configDigital( id_sys)

    def dinp_value( self, id_sys):
        value = self.__board.getFIOState( self.ionmbr( id_sys))
        return value

    def dout_value( self, id_sys, value):
        self.__board.setFIOState( self.ionmbr( id_sys), 1 if value else 0)
        return self

    def ionmbr( self, ioname):
        """Returns the ionmbr belonging to the ioname.

        ioname is one of
        "FIO0", "FIO1", "FIO2", "FIO3", "FIO4", "FIO5", "FIO6", "FIO7", \
        "EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", \
        "CIO0", "CIO1", "CIO2", "CIO3"

        and returns one of
        FIO0, FIO1, FIO2, FIO3, FIO4, FIO5, FIO6, FIO7, \
        EIO0, EIO1, EIO2, EIO3, EIO4, EIO5, EIO6, EIO7, \
        CIO0, CIO1, CIO2, CIO3 = range( 20)
        """
        return self.__ionmbrs[ str( ioname).lower()]


class DInpU3(DInp):

    def __init__( self, *, board, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self._board = board
        self._board.configDigital( id_sys)
        return

    def port2box( self):
        value = self._board.dinp_value( self.id_sys())
        value = 0 if value is None else int( value)
        value = value if self._is_hi_active else 1 - value
        self.value( value)
        return


class DOutU3(DOut):

    """2DO: Testen!
    """

    def __init__( self, *, board, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self._board = board
        self._board.configDigital( id_sys)
        return

    def box2port( self):
        value = self.value()
        value = value if self._is_hi_active else 1 - value
        self._board.dout_value( self.id_sys(), value)
        return


class AInpU3(DInp):

    """2DO: Testen!
    """

    def __init__( self, *, board, id_sys: Id, label: str):
        super().__init__( id_sys=id_sys, label=label)

        self._board = board
        self._board.configAnalog( id_sys)
        return

    def port2box( self):
        value = self._board.ainp_value( self.id_sys())
        self.value( 0 if value is None else int( value))
        return


class AOutU3(DInp):

    """2DO: Testen!
    """

    def __init__( self, *, board, id_sys: Id, label: str):
        super().__init__( id_sys=id_sys, label=label)

        self._board = board
        self._board.configAnalog( id_sys)
        return

    def box2port( self):
        value = self.value()
        self._board.aout_value( self.id_sys(), value)
        return

