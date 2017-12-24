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

"""\package rovercontrollers    Rover Controller, "bewegt" den Rover (führt ihn
aus), der selber "dumm" ist. Der RoverController führt auch die Regler aus,
die er hierzu entsprechend konfiguriert.

\par    Diary
-   2017-11-05: Erstellt. Noch nicht einsatzbereit!

\_2DO   rovercontrollers umbenennen in roverdrivers?
"""

import abc

from tau4 import Object, _ObjectSetup
from tau4.multitasking import threads as mtt
from tau4.robotix.mobile.rovers import Rover


class RoverController(mtt.CyclingThread):

    """Brain einer mobilen Roboteranwendung, der Rover selber hat keine Intelligenz.

    Der RoverController

    -   liest alle IOs, die dem Rover zur weiteren Verarbeitung z.V. stehen,
        die er aber nicht selber liest oder schreibt;

    -   bringt den Rover dazu, die Sensoren von den gerade gelesenen IOs zu lesen;

    -   führt die State Machine aus;

    -   führt in der State Machine die Regler aus, die er hierzu entsprechend konfiguriert hat;

    -   bringt den Rover dazu, die Aktuatoren auf die IOs schreiben zu lassen;

    -   schreibt alle IOs, die dem Rover zur weiteren Verarbeitung z.V. stehen,
        die er aber nicht selber liest oder schreibt.
    """

    def __init__( self, rover: Rover, cycletime: float=0.100):
        super().__init__( id=self.classname(), cycletime=cycletime, udata=None)

        self.__rover = rover
        return

    def rover( self) -> Rover:
        return self.__rover

    def _run_( self, udata):

        ### Lesen aller Eingänge
        #
        IOSystem().execute_inps()

        ### Ausführen aller Sensoren
        #
        self.rover().execute_sensors()

        ### Statemachine ausführen, die angibt, was mit dem Rover zu tun ist (Escape,
        #   Avoid, Goal).
        #
        #   Hier werden auch die Aktuatoren ausgeführt, nämlich drch die Regler.
        #
        self.statemachine().execute()

        ### Schreiben aller Ausgänge
        #
        IOSystem().execute_outs()

        return


