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

"""\package mobile2 Alles für die Realisierung mobiler Roboter: Robot Brains.

\par    Diary
-   2017-11-28: Erstellt. Noch nicht einsatzbereit!

"""

import abc
from math import cos, degrees, radians, sin

from tau4 import Object
from tau4.mathe.linalg import T3D, V3D
from tau4.robotix.mobile2 import bodies as tau4bodies


class RoverBrain(Object, abc.ABC):

    """Brain einer mobilen Roboteranwendung, der Rover selber hat keine Intelligenz.

    RoverBrain weiß alles, RoverBody hat alles.

    RoverBrain

    -   liest alle IOs, die dem Rover zur weiteren Verarbeitung z.V. stehen,
        die er aber nicht selber liest oder schreibt;

    -   bringt den Rover dazu, die Sensoren von den gerade gelesenen IOs zu lesen;

    -   führt die State Machine aus;

    -   führt in der State Machine die Regler aus, die er hierzu entsprechend konfiguriert hat;

    -   bringt den Rover dazu, die Aktuatoren auf die IOs schreiben zu lassen;

    -   schreibt alle IOs, die dem Rover zur weiteren Verarbeitung z.V. stehen,
        die er aber nicht selber liest oder schreibt.

    -   Weiß, wo der Rover gerade ist, kennt also seine Position und Orientierung.

    \note
        Basisklasse aller Rover.
        Eine App verwendet am besten den StandardRover als Basisklasse.
    """

    def __init__( self, roverbody: tau4bodies.RoverBody):
        self.__body = roverbody
        self.__directioncontroller = None
        self.__distancecontroller = None

        self.__wTb = T3D.FromEuler()
        self.__wTb_inverted = self.__wTb.inverted()

        return

    @abc.abstractmethod
    def goaldirectioncontroller_new( self):
        pass

    def goaldirectioncontroller( self):
        if self.__directioncontroller is None:
            self.__directioncontroller = self.goaldirectioncontroller_new()

        return self.__directioncontroller

    @abc.abstractmethod
    def goaldistancecontroller_new( self):
        pass

    def distancecontroller( self):
        if self.__distancecontroller is None:
            self.__distancecontroller = self.goaldistancecontroller_new()

        return self.__distancecontroller

    def bT( self):
        """Lage relativ {BASE}.

        Nur das Brain kann das wissen. Der Body kann's nicht wissen, weil der nur
        auf den Positionssensor zugreifen kann.
        """
        wTr = self.__body.positionsensor().wT()
        bTr = self.__wTb_inverted * wTr
        return bTr

    def wTb( self, wTb: T3D=None):
        """{BASE} relativ {WORLD} - muss vom Teacher kommen.

        Nur das Brain kann das wissen. Der Body kann's nicht wissen, weil der nur
        auf den Positionssensor zugreifen kann.

        \_2DO
            Definieren im RoverBrain oder im Cruiser?
        """
        if wTb is None:
            return self.__wTb

        self.__wTb << wTb
        self.__wTb_inverted << self.__wTb.inverted()
        return self

