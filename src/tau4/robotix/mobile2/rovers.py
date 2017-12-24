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

"""\package mobile2 Alles für die Realisierung mobiler Roboter: Rovers, bestehend aus Brains, Bodies, Controllers.

\par    Diary
-   2017-11-28: Erstellt. Noch nicht einsatzbereit!

"""

import abc

from tau4 import Object
from tau4 import ios2 as tau4ios
from tau4.robotix.mobile2 import bodies, brains


class Goal(abc.ABC):

    pass


class Rover(Object, abc.ABC):

    """Zusammenfassung von RoverBrain und RoverBody und IO-Handling.
    """

    def __init__( self, id):
        super().__init__( id=id)

        self.__body: bodies.RoverBody = None
        self.__brain: brains.RoverBrain = None
        self.__kinematic = None
        return

    @abc.abstractmethod
    def body_new( self) -> bodies.RoverBody:
        """RoverBody und RoverBrain können app-spezifisch sein, weshalb diese Methode abzuleiten ist.
        """
        pass

    def body( self) -> bodies.RoverBody:
        """Aktueller RoverBody.
        """
        if self.__body is None:
            self.__body = self.body_new()

        return self.__body

    @abc.abstractmethod
    def brain_new( self) -> brains.RoverBrain:
        """RoverBody und RoverBrain können app-spzifisch sein, weshalb diese Methode abzuleiten ist.
        """
        pass

    def brain( self) -> brains.RoverBrain:
        """Aktuelles RoverBrain.
        """
        if self.__brain is None:
            self.__brain = self.brain_new()

        return self.__brain

    def execute( self) -> bool:
        """Rover ausführen: IOSystem, RoverBrain, RoverBody, IOSystem.
        """

        ### IOSystem lesen
        #
        tau4ios.IOSystem().execute_inps()

        ### RoveerBody ausführen
        #
        self.body().execute_sensors()

        ### RoverBrain ausführen
        #
        self.brain().execute()

        ### RoveerBody ausführen
        #
        self.body().execute_actuators()

        ### IOSystem schreiben
        #
        tau4ios.IOSystem().execute_outs()

        return


class StandardGoal(Goal):

    pass


class StandardRover(Rover):

    def __init__( self, id):
        super().__init__( id)
        return


