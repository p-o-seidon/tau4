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
#
################################################################################

from tau4 import Id
from tau4.ios2 import AInp, AOut, DInp, DOut, IOBoard
from tau4.oop import overrides, Singleton

from pymata_aio.pymata3 import PyMata3
from pymata_aio.constants import Constants


class BoardPyMata(PyMata3, IOBoard):

    def __init__( self, *, usrid, usbport=None):
        PyMata3.__init__( self, com_port=usbport)
        IOBoard.__init__( self, usrid)
        return
    
    def ainp_value( self, id_sys):
        """Analogwert von Eingang lesen.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        """
        raise NotImplementedError()

    def aout_value( self, id_sys, value):
        """Analogwert auf Ausgang schreiben.

        Ausführung durch box2port() von AOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden solll.
        """
        raise NotImplementedError()

    def dinp_value( self, id_sys):
        """Digitalwert von Eingang lesen.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        """
        return self.dinp_read( id_sys)

    def dout_value( self, id_sys, value):
        """Digitalwert auf Ausgang schreiben.

        Ausführung durch box2port() von DOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden solll.
        """
        return dout_write( id_sys, value)

    def dinp_read( self, sysid: int) -> int:
        """Ausführung von PyMata3::digital_read().
        
        \_2DO:
            Streichen: dinp_value() tut das gleiche!
        """
        value = self.digital_read( sysid)
        return value

    def dout_write( self, sysid: int, value):
        """Ausführung von PyMata3::digital_pin_write().
        
        \_2DO:
            Streichen: dout_value() tut das gleiche!
        """
        self.digital_pin_write( sysid, value)
        return self

    def set_pinmode_DINP( self, sysid: int):
        """Ausführung von PyMata3::set_pin_mode().
        """
        self.set_pin_mode( sysid, Constants.INPUT)
        return self

    def set_pinmode_DOUT( self, sysid: int, mode=Constants.OUTPUT):
        """Ausführung von PyMata3::set_pin_mode().
        """
        self.set_pin_mode( sysid, mode)
        return self

    def set_pinmode_ENCODER( self, sysid: int, mode=Constants.ENCODER):
        """Ausführung von PyMata3::set_pin_mode().
        """
        self.set_pin_mode( sysid, mode)
        return self

    def uss_config( self, sysid_triggerpin, sysid_echopin, callback, max_distance=300):
        self.sonar_config( int( sysid_triggerpin), int( sysid_echopin), callback, max_distance=max_distance, ping_interval=100)
        return self


class DInpNano(DInp):
    
    """Digitaler Eingang auf dem Arduino Nano.
    """

    def __init__( self, *, board, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( libname=None, id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self._board = board

        board.set_pin_mode( int( id_sys), Constants.INPUT)
        return

    def id_sys( self):
        return int( super().id_sys())

    def port2box( self):
        #if self.__board.bytes_available():
        #    self.__board.iterate()
        # ##### Fahren mit einem Iterator im Board

        value = self._board.dinp_read( int( self.id_sys()))
        value = 0 if value is None else int( value)
        value = value if self._is_hi_active else 1 - value
        self.value( value)
        return


class DInpNanoEncoder(DInp):
    
    """Encoder-Eingang auf dem Arduino Nano.
    
    Dieser DInp hat so wenige Wechselwirkungen mit OSystem wie möglich, da er 
    nur auf dem Arduino relevant sein soll.
    
    Differenz zu Base Class also:
        -   Kein <c>board.set_pin_mode( int( id_sys), Constants.INPUT)</c> im Ctor.
        -   Kein port2box, also kein Update, wenn IOSystem().execute() ausgeführt wird.
    """

    def __init__( self, *, board, id_sys: Id, label: str):
        super().__init__( libname=None, id_sys=id_sys, is_hi_active=True, label=label)

        self._board = board
        return

    def id_sys( self):
        return int( super().id_sys())

    def port2box( self):
        pass


class DInpNanoInverted(DInpNano):

    """Funktioniert (noch) nicht!
    """

    def __init__( self, *, board, id_sys: Id, label: str):
        super().__init__( board=board, id_sys=id_sys, label=label)

        self._pin.mode = 0x0B # PIN_MODE_PULLUP
        self._pin.port.enable_reporting()
        for pin in self._pin.port.pins:
            if pin.mode in (0, 0x0B):
                pin.reporting = True

#        self._pin.value = 1
#        msg = bytearray( [ 0x90, self._pin.pin_number, 1])
#        self._pin.board.sp.write( msg)
        return

    def id_sys( self):
        return int( super().id_sys())

    def port2box( self):
        #if self.__board.bytes_available():
        #    self.__board.iterate()
        # ##### Fahren mit einem Iterator im Board

        value = self._pin.read()
        self.value( 1 if value is None else 1 - int( value))
        return


class DOutNano(DOut):

    """

    \_2DO
        Wenn jedes Board das hier benötigte Protokoll untertützte,
        könnten wir alleine mit der Base Class das Auslangen finden.
    """

    def __init__( self, *, board, id_sys: Id, is_hi_active: bool, label):
        super().__init__( id_sys=id_sys, is_hi_active=is_hi_active, label=label)

        self._board = board

        board.set_pinmode_DOUT( int( id_sys), Constants.OUTPUT)
        return
    
    def board( self):
        return self._board

    def box2port( self):
        value = self.value()
        value = value if self._is_hi_active else 1 - value
        self._board.dout_write( int( self.id_sys()), value)
        return

    def id_sys( self):
        return int( super().id_sys())





