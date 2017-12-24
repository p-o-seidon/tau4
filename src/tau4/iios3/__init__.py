#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
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
#
################################################################################

import abc
import threading

from tau4 import DictWithUniqueKeys
from tau4.data import pandora
from tau4.oop import overrides, Singleton


################################################################################
class IOutBox(pandora.Box):

    def __init__( self, *, value, id=None, label="", dim="", infos=""):
        super().__init__( id=id, value=value, label=label, dim=dim, infos=infos)

        self.__value_in_cache = self.value()
        return

    def bid( self): return self.id()

    def validate( self):
        """Schreibt den Cache in die Realdaten
        """
        self.value( self.__value_in_cache)
        return self

    def _value_( self, value=None):
        """Schreibt in den Cache bzw liest von dort.
        """
        if value is None:
            return self.__value_in_cache

        value = self._typecast_( value)

        self.__value_in_cache = value
        return self


class IInpBox(pandora.BoxMonitored):

    def __init__( self, ioutbox: IOutBox):
        super().__init__( id=None, value=ioutbox.value(), label=ioutbox.label(), dim=ioutbox.dim())

        self.__ioutbox = ioutbox
        return

    def bid( self):
        return self.__ioutbox.bid()

    def transfer_if_needed( self):
        if self.value() != self.__ioutbox.value():
            self.value( self.__ioutbox.value())

        return


################################################################################
class IInpShelf:

    def __init__( self, sid):
        self._sid = sid
        self._iinpboxes_by_sid_and_bid = DictWithUniqueKeys()
        return

    def iinpbox_add( self, sid, bid, iinpbox: IInpBox):
        if not sid in self._iinpboxes_by_sid_and_bid:
            self._iinpboxes_by_sid_and_bid[ sid] = DictWithUniqueKeys()

        self._iinpboxes_by_sid_and_bid[ sid][ bid] = iinpbox
        return self

    def iinpboxes( self, sid, bid=None):
        if bid is None:
            return self._iinpboxes_by_sid_and_bid[ sid].values()

        return self._iinpboxes_by_sid_and_bid[ sid][ bid]

    def iinp_value( self, sid, bid):
        return self._iinpboxes_by_sid_and_bid[ sid][ bid].value()

    def transfer( self):
        """Kopiert die Boxen aus den einzelnen IOutShelf ins IInpShelf.

        Hierzu wird das Shelf gelockt.

        Das Locking gestaltet sich schwierig, denn das IOutShelf wird nicht an
        Stück kopiert und es geht nicht nur um EIN IOutShelf. Welches Shelf
        betroffen wird, stellt sich erst beim Zugriff auf jede der Boxen des
        IInpShelf heraus.

        Die Transfer-Vorgänge müssen also sortiert und "geblockt" werden, was
        über die sid, die mitgespeichert wird, möglich ist.
        """
        for sid in self._iinpboxes_by_sid_and_bid:
            with IOutShelves( sid).lock():
                for iiobox in self._iinpboxes_by_sid_and_bid[ sid].values():
                    iiobox.transfer_if_needed()
                                                    # Macht einen Vergleich, etwa so:
                                                    #   if self.value() != self.box_connected().value(): ...
        return

    def iinpbox_create_from_ioutbox( self, sid, ioutbox: IOutBox):
        iinpbox = IInpBox( ioutbox)
        self.iinpbox_add( sid, iinpbox.bid(), iinpbox)
        return


class IOutShelf:

    def __init__( self, sid):
        self._sid = sid

        self._ioutboxes_by_bid = DictWithUniqueKeys()
        self.__lock = threading.Lock()
        return

    def ioutboxes( self):
        return self._ioutboxes_by_bid.values()

    def ioutbox_create( self, bid, value, label, dim):
        self._ioutboxes_by_bid[ bid] = IOutBox( id=bid, value=value, label=label, dim=dim)
        return

    def iout_value( self, bid, value=None):
        """Ausgang schreiben.

        \param  bid Box-Id.

        Usage:
            \code{.py}
                IOutShelves( "mmi").iout_value( IIoIds.MMI._COMMAND_TO_PLC, value)
            \endcode
        """
        if value is None:
            return self._ioutboxes_by_bid[ bid]._value_()

        self._ioutboxes_by_bid[ bid]._value_( value)
        return

    def lock( self):
        return self.__lock

    def validate( self):
        """Kopiert den Cache jeder Box in den Value jeder Box; Ausführung am Ende jedes Zyklus.

        Hierzu wird das Shelf gelockt.
        """
        with self.lock():
            for ioutbox in self._ioutboxes_by_bid.values():
                ioutbox.validate()

        return


class _IIoShelves(metaclass=Singleton):

    def __init__( self):
        self._shelves_inp = DictWithUniqueKeys()
        self._shelves_out = DictWithUniqueKeys()
        return

    def iinpshelf_create( self, sid):
        self._shelves_inp[ sid] = IInpShelf( sid)
        return self

    def ioutshelf_create( self, sid):
        self._shelves_out[ sid] = IOutShelf( sid)
        return self


def IInpShelves( sid=None) -> IInpShelf:
    if sid is None:
        return _IIoShelves()

    return _IIoShelves()._shelves_inp[ sid]


def IOutShelves( sid=None) -> IOutShelf:
    """Liefert den Shelf zu einer ControlUnit: mmi, plc, rc.
    """
    if sid is None:
        return _IIoShelves()

    return _IIoShelves()._shelves_out[ sid]


