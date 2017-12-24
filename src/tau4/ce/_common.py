#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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

from tau4 import Id
from tau4.data import pandora


class _AlgorithmDigital(metaclass=abc.ABCMeta):

    """Basisklasse für alle Algorithmen.

    \param  id      Id des Algorithmus. Das ist ganz praktisch, wenn es mehr als
                    einen Regler im System gibt.
    \param  p_Ts    Abstastzeit. Die Box wird nicht direkt verwendet, sondern kopiert.
                    Änderungen werden aber wirksam, weil wir uns dafür registrieren.
                    Die nicht direkte Verwendeung der Box p_Ts erlaubt uns die
                    Verwendung einer einfachen und daher schnellen Box. p_Ts
                    könnte eine Box mit wer weiß wie vielen Plugins sein.
    """

    def __init__( self, *, id, p_Ts: pandora.BoxMonitored, p_e: pandora.Box, p_u: pandora.Box):
        if not isinstance( p_Ts, (pandora.BoxMonitored, pandora.BoxClippingMonitored)):
            raise TypeError( "p_Ts needs to be a monitored Box, but is of type '%s'. " % type( p_Ts))

        self.__id = id
        self.__p_Ts = pandora.Box( value=p_Ts.value())
        self.__p_e = p_e
        self.__p_u = p_u

        p_Ts.reg_tau4s_on_modified( lambda pc, self=self: self.__p_Ts.value( pc.client().value()))
        return

    @abc.abstractclassmethod
    def configure( self, p_Ts):
        """Konfigurieren des Algorithmus.

        Kann dazu verwendet werden, die Koeffizienten neu zu berechnen, während
        Instanzen schon ausgeführt werden.

        Beispielsweise wird der Algorithmus hier die Koeffizienten der
        Differenzengleichung berechnen wollen.

        :param  FlexVarblLL p_Ts:  Abtastzeit.
        """
        pass

    def p_e( self):
        """Eingangssignal.
        """
        return self.__p_e

    def p_Ts( self):
        """Abstatszeit.
        """
        return self.__p_Ts

    def p_u( self):
        """Ausgangssignal.
        """
        return self.__p_u

    def id( self):
        """Eindeutige Id.
        """
        return self.__id

    @abc.abstractclassmethod
    def execute( self):
        """Ausführung des Regelalgorithmus.
        """
        pass

    @abc.abstractclassmethod
    def info( self):
        """Info zum Algorithmus (z.B. Name).
        """
        pass

    @abc.abstractclassmethod
    def name( self):
        """Name des Algorithmus.
        """
        pass

    @abc.abstractclassmethod
    def reset( self):
        """Reset des Algorithmus, also seiner Daten.
        """
        pass


