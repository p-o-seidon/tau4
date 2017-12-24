#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2015
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

"""\package mobile2 Alles für die Realisierung mobiler Roboter: Kinematiken.

\par    Diary
-   2017-11-28: Erstellt. Noch nicht einsatzbereit!

"""

from tau4 import Object
from tau4.mathe.linalg import T3D


class UCKBodyDatasheet:

    def __init__( self, *, wheeldistance, wheeldiameter, wheelspeed_rpm):
        self.__wheeldistance = wheeldistance

        n = wheelspeed_rpm/60
        self.__omega_max_wheel = 2*pi*n

        rW = wheeldiameter/2
        self.__v_max_wheel = self.__omega_max_wheel * rW

        rC = self.wheeldistance()/2
        self.__omega_max_chassis = self.v_max_wheel()/rC

        return

    def omega_max_chassis( self):
        """Maximale Winkelgeschwindigkeit, mit der sich das Chassis drehen kann.
        """
        return self.__omega_max_chassis

    def omega_max_wheel( self):
        """Maximale Winkelgeschwindigkeit der Räder.
        """
        return self.__omega_max_wheel

    def v_max_chassis( self):
        """Maximale geschwindigkeit, mit der das Chassis geradeaus fahren kann.
        """
        return self.v_max_wheel()

    def v_max_wheel( self):
        """Maximale v, die mit diesen Rädern möglich ist.
        """
        return self.__v_max_wheel

    def wheeldistance( self):
        """Abstand der beiden Räder.
        """
        return self.__wheeldistance


class UCKBodyDatasheet4Tests(ChassisDatasheet):

    def __init__( self):
        super().__init__( wheeldistance=42, wheeldiameter=42, wheelspeed_rpm=42)
        return


class DifferentialWheels:

    """Chassis, das es einem Roboter ermöglicht, auf der Stelle zu drehen (im Unterschied zu Ackermann-Steering).
    """

    def __init__( self, datasheet: ChassisDatasheet):
        self.__datasheet = datasheet

        self.__v_100 = 0
        self.__omega_100 = 0

        self.__vL = 0
        self.__vR = 0
        return

    def datasheet( self) -> ChassisDatasheet:
        return self.__datasheet

    def ddk_100( self, v_100: float, omega_100: float) -> (float, float):
        """Differential Drive Kinematics: Liefert vL, vR in %.
        """
        vL_100 = v_100 - omega_100
        vR_100 = v_100 + omega_100
        return vL_100, vR_100

    def execute( self):
        """Werte auf den MD25 schreiben (über I2C!).

        .. note::
            Schreibt auf die Hardware.
        """
        ### vC und omega in speedLHS und speedRHS umrechnen
        #
        speedL_100 = self.speedL_100()
        speedR_100 = self.speedR_100()

        ### Werte aufs Fahrwerk schreiben
        #
        ios2.MDBoards().board( "md").speed_100( speedL_100, speedR_100)

        return

    def omega_max( self):
        return self.datasheet().omega_max_chassis()

    def uck_100( self, *, v_100=None, omega_100=None):
        """Uni Cycle Kinematics: Lesen/schreiben von v_100 und omega_100.

        Wir berechnen zuerst v_100, dann omega_100. Grund für diese Reihenfolge: omega_100 reduziert unter Umständen v_100.
        """
        if (v_100, omega_100) == (None, None):
            return self.__v_100, self.__omega_100

        vL_100 = v_100 - omega_100
        vR_100 = v_100 + omega_100
        if max( vL_100, vR_100) > 100:
            v_100 -= max( vL_100, vR_100) - 100

        self.__v_100 = v_100
        self.__omega_100 = omega_100
        return self

    def v_max( self):
        return self.datasheet().v_max_wheel()

    def vL( self):
        return self.vL_100()/100*self.v_max()

    def vL_100( self):
        """Liefert den Speed in % für das linke Rad: Berechnet den Speed in % aus v_100 und omega_100.
        """
        vL_100, vR_100 = self.ddk_100( *self.uck_100())
        return vL_100
    speedL_100 = vL_100

    def vR( self):
        return self.vR_100()/100*self.v_max()

    def vR_100( self):
        """Liefert den Speed in % für das rechte Rad: Berechnet den Speed in % aus v_100 und omega_100.
        """
        vL_100, vR_100 = self.ddk_100( *self.uck_100())
        return vR_100
    speedR_100 = vR_100

    def width( self):
        return self.datasheet().wheeldistance()


class RoverKinematix(Object):

    """

    \_2DO
        Brauchen wir diese Klasse wirklich?
    """

    def __init__( self):
        self.__bTr = T3D.FromEuler()
        return

    def bTr( self, bTr=None):
        """Frame {ROBOT} in {BASE}.
        """
        if bTr is None:
            return self.__bTr

        self.__bTr << bTr
        return self


