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
import collections
import logging
import platform

from tau4 import Id, Object
from tau4.data import pandora
from tau4.oop import Singleton

from ._common import *


class IOBoard(metaclass=abc.ABCMeta):

    def __init__( self, id_usr):
        self.__usrid = id_usr
        return

    @abc.abstractmethod
    def ainp_value( self, id_sys):
        """Analogwert von Eingang lesen.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        """
        pass

    @abc.abstractmethod
    def aout_value( self, id_sys, value):
        """Analogwert auf Ausgang schreiben.

        Ausführung durch box2port() von AOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden solll.
        """
        pass

    @abc.abstractmethod
    def dinp_value( self, id_sys):
        """Digitalwert von Eingang lesen.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        """
        pass

    @abc.abstractmethod
    def dout_value( self, id_sys, value):
        """Digitalwert auf Ausgang schreiben.

        Ausführung durch box2port() von DOut.

        \param  id_sys  Id, unter der der Pin vom konkrteen Board angesprochen wird.
        \param  value   Wert, der auf den Pin geschrieben werden solll.
        """
        pass

    def id_usr( self):
        """Alias für usrid().
        """
        return self.__usrid

    def usrid( self):
        """Id, vom User vergeben.

        Das Board braucht und verwendet diese Id nicht.
        """
        return self.__usrid


class IOBoards(metaclass=Singleton):

    def __init__( self):
        self.__boards = {}
        return

    def as_dict( self):
        return self.__boards

    def board( self, usrid_board):
        usrid_board = str( usrid_board)
        return self.__boards[ usrid_board]

    def board_add( self, *, board, usrid_board: Id):
        usrid_board = str( usrid_board)
        if not isinstance( board, IOBoard):
            logging.warn( "IOBoards::board_add(): Board '%s' should be a subclass of IOBoard but isn't!", usrid_board)

        if usrid_board in self.__boards:
            raise NotImplementedError( "Board '%s' already added. " % usrid_board)

        self.__boards[ usrid_board] = board
        return

    def board_exists( self, usrid_board):
        return usrid_board in self.__boards

    has_board = board_exists


class IOSystem(metaclass=Singleton):

    def __init__( self):
        self.__ainps = {}
        self.__aouts = {}
        self.__dinps = collections.OrderedDict()
        self.__douts = collections.OrderedDict()

        self.__is_running_on_raspbian = platform.machine().lower().startswith( "arm")
        return

    def board( self, id):
        return IOBoards().board( id)

    def ainp_add( self, port: AInp, id_usr: Id):
        """Pin ins IOSystem aufnehmen, denn nur so wird er auch ausgeführt, wenn ios2.IOSystem().execute_inps() bzw ios2.IOSystem().execute_outs() ausgeführt wird!

        Diese Methode verfolgt zweierlei:

        \li Aufnahme des Pins, damit er vom System gelesen/geschrieben wird.
        \li Aufnahme des Pins unter einer id_usr, damit er über diese systemweit
            ansprechbar ist.
        """
        if id_usr in self.__ainps.keys():
            raise KeyError( "Port '%s' already added!" % id_usr)

        self.__ainps[ id_usr] = port
        return self

    def ainps( self, id_usr: Id = None):
        if id_usr is None:
            return self.__ainps.values()

        return self.__ainps[ id_usr]

    def aout_add( self, port: AOut, id_usr: Id):
        """Pin ins IOSystem aufnehmen, denn nur so wird er auch ausgeführt, wenn ios2.IOSystem().execute_inps() bzw ios2.IOSystem().execute_outs() ausgeführt wird!

        Diese Methode verfolgt zweierlei:

        \li Aufnahme des Pins, damit er vom System gelesen/geschrieben wird.
        \li Aufnahme des Pins unter einer id_usr, damit er über diese systemweit
            ansprechbar ist.
        """
        if id_usr in self.__aouts.keys():
            raise KeyError( "Port '%s' already added!" % id_usr)

        self.__aouts[ id_usr] = port
        return self

    def aouts( self, id_usr: Id = None):
        if id_usr is None:
            return self.__aouts.values()

        return self.__aouts[ id_usr]

    def dinp_add( self, port: DInp, id_usr: Id):
        """Pin ins IOSystem aufnehmen, denn nur so wird er auch ausgeführt, wenn ios2.IOSystem().execute_inps() bzw ios2.IOSystem().execute_outs() ausgeführt wird!

        Diese Methode verfolgt zweierlei:

        \li Aufnahme des Pins, damit er vom System gelesen/geschrieben wird.
        \li Aufnahme des Pins unter einer id_usr, damit er über diese systemweit
            ansprechbar ist.
        """
        assert isinstance( port, DInp)
        if id_usr in self.__dinps.keys():
            raise KeyError( "Port '%s' already added!" % id_usr)

        self.__dinps[ id_usr] = port
        self.__dinps = collections.OrderedDict( sorted( self.__dinps.items()))
        return self

    def dinps( self, id_usr: Id=None):
        if id_usr is None:
            return self.__dinps.values()

        return self.__dinps[ id_usr]

    def dout_add( self, port: DOut, id_usr: Id):
        """Pin ins IOSystem aufnehmen, denn nur so wird er auch ausgeführt, wenn ios2.IOSystem().execute_inps() bzw ios2.IOSystem().execute_outs() ausgeführt wird!

        Diese Methode verfolgt zweierlei:

        \li Aufnahme des Pins, damit er vom System gelesen/geschrieben wird.
        \li Aufnahme des Pins unter einer id_usr, damit er über diese systemweit
            ansprechbar ist.
        """
        assert isinstance( port, DOut)
        if id_usr in self.__douts.keys():
            raise KeyError( "Port '%s' already added!" % id_usr)

        self.__douts[ id_usr] = port
        self.__douts = collections.OrderedDict( sorted( self.__douts.items()))
        return self

    def douts( self, id_usr: Id = None):
        if id_usr is None:
            return self.__douts.values()

        return self.__douts[ id_usr]

    def execute( self):
        self.execute_inps()
        self.execute_outs()
        return self

    def execute_inps( self):
        for port in self.__ainps.values():
            port.execute()

        for port in self.__dinps.values():
            port.execute()

        return self

    def execute_outs( self):
        for port in self.__aouts.values():
            port.execute()

        for port in self.__douts.values():
            port.execute()

        return self

    def is_on_raspi( self):
        return self.__is_running_on_raspbian

    def reset( self):
        for port in self.__aouts.values():
            port.p_box().value( 0)
            port.execute()

        for port in self.__douts.values():
            port.p_box().value( 0)
            port.execute()

        return


class MDBoards(metaclass=Singleton):

    def __init__( self):
        self.__boards = {}
        return

    def board( self, id_usr):
        return self.__boards[ id_usr]

    def board_add( self, board, id_usr: Id):
        if id_usr in self.__boards:
            raise NotImplementedError( "Board '%s' already added. " % id_usr)

        self.__boards[ id_usr] = board
        return

