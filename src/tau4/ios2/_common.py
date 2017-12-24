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

from tau4 import Id, Object
from tau4.data import pandora


class Port(Object, metaclass=abc.ABCMeta):

    """

    \_2DO
        Umbennen in Pin oder sowas, denn ein Port ist  was Anderes.
    """

    def __init__( self, id_sys: Id, p_box: pandora.Box):
        super().__init__( id=id_sys)

        self.__p_box = p_box
        return

    def dim( self):
        return self.__p_box.dim()

    @abc.abstractmethod
    def execute( self):
        pass

    def id_sys( self):
        return self.id()
    sysid = id_sys

    def label( self):
        return self.__p_box.label()

    def p_box( self):
        """DEPRECATED, p_value() verwenden!
        """
        return self.__p_box

    def p_value( self):
        return self.__p_box

    def value( self, arg=None):
        if arg is None:
            return self.p_box().value()

        self.p_box().value( arg)
        return self


class AInp(Port):

    def __init__( self, id_sys: Id, label: str):
        super().__init__( id_sys, pandora.BoxClippingMonitored( value=0.0, bounds=(0, 1), label=label, dim="V"))
        return

    def execute( self):
        self.port2box()
        return self

    @abc.abstractmethod
    def port2box( self):
        pass


class AOut(Port):

    """Abstract Base Class für analoge Ausgänge.

    \_2DO
        Optimierungsmöglicheit:
            Wir könnten uns bei der Box für Änderungen registrieren. Bei Änderugen
            setzen wir ein Dirty Flag. Nur wenn dieses Flag gesetzt ist, führt
            execute() box2port() auch wirklich aus (und resettet das Dirty Flag).

    \warning    Kein Clipping!
    """

    def __init__( self, id_sys: Id, label: str):
        super().__init__( id_sys, pandora.BoxMonitored( value=0.0, label=label, dim="V"))
        return

    @abc.abstractmethod
    def box2port( self):
        """Effektiver Schreibvorgang auf die Hardware.
        """
        pass

    def execute( self):
        """Effektiver Schreibvorgang auf die Hardware.
        """
        self.box2port()
        return self


class DInp(Port):

    """Digital Input.

    \param
        libname
            Gültige Werte: None, pigpio. Hat nur bedeutung, wenn der IO auf dem
            RasPi liegt. Findet Verwendung in DistancesensorUss_Devantech_SRF04_Using_CallbackChainer.

    \_2DO:
        Param libname rausnehmen.
    """

    def __init__( self, libname: str, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys, pandora.BoxClippingMonitored( value=0, bounds=(0, 1), label=label))

        self.__libname = libname
        self._is_hi_active = is_hi_active
        return

    def execute( self):
        self.port2box()
        return self

    def is_hi( self):
        return self.value() == 1

    def is_lo( self):
        return not self.is_hi()

    def libname( self):
        return self.__libname

    @abc.abstractmethod
    def port2box( self):
        """Downcall to subclass, called by DInp::execute.
        """
        pass


class DOut(Port):

    """Abstract Base Class für digitale Ausgänge.

    \_2DO
        Optimierungsmöglicheit:
            Wir könnten uns bei der Box für Änderungen registrieren. Bei Änderugen
            setzen wir ein Dirty Flag. Nur wenn dieses Flag gesetzt ist, führt
            execute() box2port() auch wirklich aus (und resettet das Dirty Flag).
    """

    def __init__( self, id_sys: Id, is_hi_active: bool, label: str):
        super().__init__( id_sys, pandora.BoxClippingMonitored( value=0, bounds=(0, 1), label=label))

        self._is_hi_active = is_hi_active
        return

    @abc.abstractmethod
    def box2port( self):
        """Effektiver Schreibvorgang auf die Hardware.
        """
        pass

    def execute( self):
        """Effektiver Schreibvorgang auf die Hardware.
        """
        self.box2port()
        return self

    def is_hi( self):
        return self.value() == 1

    def is_lo( self):
        return not self.is_hi()


class MotorDriver(metaclass=abc.ABCMeta):

    """Base Class aller Motortreiber.

    EIn MD25 ist hierbei das Maß der Dinge. Er hat eingebaute Regler und Liefert
    eine Unzahl von Daten.

    Konzeptionell leistet ein ThnderBorg auf eiem RasPi dasselbe, ist aber keine
    Motortreiber-Einheit. Gleichwohl kann er als solche behandelt werden - siehe
    MotorDriverCAM2000.
    """

    _STATUS_OFF = "off"
    _STATUS_ON = "on"
    _STATUS_RUNNING = "running"


    def __init__( self, id, is_direction_inverted=False):
        self.__id = id
        self.__is_direction_inverted = is_direction_inverted
        self.__speed_max_100 = 100

        self.__status = self._STATUS_OFF
        return

    def _assert_invariants_( self):
        assert self.__status in self.__valid_status
        return

    def id( self):
        return self.__id
    id_usr = id
    usrid = id

    def is_direction_inverted( self):
        return self.__is_direction_inverted

    @abc.abstractmethod
    def speed_100( self, lhs: float, rhs: float) -> None:
        pass

    def speed_max_100( self, max=None):
        """Maximalgeschwindigkeit in %.

        \note
            Sub Classes, die Encoder abfragen können, müssen diese Methode
            überschreiben, sodass sie die wirliche Geschwindigkeit liefern.

        Usage:
            \code{.py}
                lhs_100 *= (self.speed_max_100() / 100)
            \endcode
        """
        if max is None:
            return self.__speed_max_100

        self.__speed_max_100 = max
        self._assert_invariants_()
        return self

    def status_as_str( self):
        return str( self.__status)

    @abc.abstractmethod
    def status_change( self, status):
        pass

    def status_is_off( self):
        return self.__status == self._STATUS_OFF

    def status_is_on( self):
        return self.__status == self._STATUS_ON

    def status_is_running( self):
        return self.__status == self._STATUS_RUNNING

    def status_is_valid( self, status):
        return status in ( self._STATUS_OFF, self._STATUS_ON, self._STATUS_RUNNING)

    def status_to_off( self):
        self.__status = self._STATUS_OFF
        return self

    def status_to_on( self):
        self.__status = self._STATUS_ON
        return self

    def status_to_running( self):
        self.__status = self._STATUS_RUNNING
        return self


class MotorEncoder(abc.ABC):

    """Single-Signal Encoder.
    """

    @abc.abstractmethod
    def encoderticks( self):
        """Encoder-Ticks seit Einschalten
        """
        v = self.__dinp.p_tickcount().value()
        return v

    @abc.abstractmethod
    def encoderticks_per_second( self):
        """Encoder-Ticks pro Sekunde.
        """
        v = self.__dinp.p_ticks_per_second().value()
        return v




