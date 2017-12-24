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


"""\package rovers  Realisierung eines mobilen Roboters.

\par    Diary
-   2017-11-03: Erstellt. Noch nicht einsatzbereit!
"""

import abc
from math import atan2, degrees, pi, radians

from tau4 import Object
from tau4.robotix.mathe import T3D


class _Utils:

    @staticmethod
    def omega2n( omega): return omega/2/pi

    @staticmethod
    def n2omega( n): return 2*pi*n


class HWData(Object, metaclass=abc.ABCMeta):

    """Daten einer HW-Komponente.

    Ist immer mit einem INI-File verbunden, das - wenn nicht vorhanden - aus
    den Default-Werten erzeugt wird.
    """

    def __init__( self, id):
        super().__init__( id=id)
        return

    def pathname( self):
        return "./%s.dat" % self.classname()

    def dict2file( self, *, d, f):
        f.rewind()
        f.write( d)
        return self

    def file2dict( self, *, f, d):
        f.rewind()
        d.update( eval( f.read()))
        return self


class HWReader(Object, metaclass=abc.ABCMeta):

    """Liest Daten von der Hardware.

    Das kann über die PLC erfogen oder TAUs IO-System.
    """

    def __init__( self, id):
        super().__init__( id=id)
        return


class HWWriter(Object, metaclass=abc.ABCMeta):

    """Schreibt Daten auf die Hardware.

    Das kann über die PLC erfolgen oder TAUs IO-System.
    """

    def __init__( self, id):
        super().__init__( id=id)
        return


class DriveHWData(HWData):

    """Motordaten (eines GSM).

    Liest Daten-File ein, das aus den Default-Daten erzeugt wird, wenn es nicht
    existiert.
    """

    def __init__( self, *, id, nN, uAN, kM, J, TM):
        super().__init__( id=id)

        ### Daten-File einlesen. Wenn kein Daten-File vorhanden ist, wird es aus den Default-Daten erzeugt.
        #
        self.__values = { "nN": nN, "uAN": uAN, "kM": kM, "J": J, "TM": TM}
        try:
            with open( self.pathname(), "r") as f:
                self.file2dict( f=f, d=self.__values)

        except FileNotFoundError:
            with open( self.pathname(), "w") as f:
                self.dict2file( f=f, d=self.__values)

        return

    def J( self):
        """Trägheitsmoment von Motor, Getriebe und Rad.
        """
        pass

    def kM( self):
        """Drehmomentkonstante.
        """
        pass

    def nN( self):
        """Nenndrehzahl, gemessen am GetriebeAUSGANG.
        """
        pass

    def TM( self):
        """Mechanische Zeitkonstante, bezogen auf den GetriebeAUSGANG.
        """
        pass

    def uAN( self):
        """Nennspannung.
        """
        pass


class DriveHWReader(HWReader):

    """Liest Daten von der Drive-Sensorik wie Drehzahl usw.
    """

    def __init__( self, id):
        super().__init__( id=id)
        return

    def n_100( self):
        """Drehzahl des Rades lesen in 1/s, normiert auf [0, 100].
        """
        pass

    def v_100( self, v_100):
        """Tangentialgeschwindigkeit des Rades lesen in m/s, normiert auf [0, 100].
        """
        pass


class DriveHWWriter(HWWriter):

    """Schreibt Daten auf den Motor wie die Ankerspanung usw.
    """

    def n_100( self, n_100):
        """Drehzahl des Rades schreiben in 1/s, normiert auf [0, 100].
        """
        pass

    def v_100( self, v_100):
        """Tangentialgeschwindigkeit des Rades schreiben in m/s, normiert auf [0, 100].
        """
        pass


class DriveChassis(Object, metaclass=abc.ABCMeta):

    """Antriebseinheit: Unterer Teil des Chassis, Gesamtheit aller Antriebe.

    \_2DO
        Überlegen: Auch in Inspectors und Mutators einteilen?
    """

    def __init__( self, id):
        super().__init__( id=id)
        return

    def omega_100( self, omega_100):
        """Schreiben omega des Chassis in 1/s, normiert auf [0, 100]; Lesen ist nur über das SensorChassis möglich!

        Verwendet DriveHWWriter, um auf den Motor zu schreiben.
        """

    def v_100( self, omega_100):
        """Schreiben v des Chassis in m/s, normiert auf [0, 100]; Lesen ist nur über das SensorChassis möglich!

        Verwendet DriveHWWriter, um auf den Motor zu schreiben.
        """


class SensorChassis(Object, metaclass=abc.ABCMeta):

    """Sensorplattform: 'Oberer Teil' des Chassis, Gesamtheit aller Sensoren.

    Zu den Sensoren gehören auch die Radsensoren, weshalb hier auch DriveHWReader
    zum EInsatz kommt.
    """

    def __init__( self, id):
        super().__init__( id=id)
        return

    def alpha_heading( self):
        """Richtung, in die der Rover fahren kann, ohne auf ein Hindernis zu treffen.

        \par    Berechnung
        \code
            P = V3()
            for ranger in Rover().rangersF():
                                            # Über alle Abstandssensoren an der Front.
                rTo = ranger.rTo()
                                                # Obstacle relativ ROBOT.
                P += rTo.P()

            alpha_heading = atan2( P.y(), P.x())
        \endcode

        \note   Es reicht nicht, nur den Winkel zu berücksichtigen, weil ein
        Geraudeaus-auf-eine-Wand-zufahren so nicht erkann werden kann - siehe distance_heading().
        """

    def alpha_compass( self):
        """Abweichung von Norden.
        """

    def distance_heading( self):
        """Länge des aus rTo().P() gebildeten Heading-Vektors.

        Siehe alpha_heading().
        """

    @abc.abstractmethod
    def wTr( self):
        """Liefert die aktuelle Position des Rovers in WORLD.

        Hierzu muss das SensorChassis über einen entsprecenden Sensor eine
        Positionbestimmung vornehmen und die Rechnung

        wTr = wTs rTs.inverted()

        vornehmen, wobei wTs die Pose ist, die vom Sensor erfasst wird.
        """
        pass


class SensorError(Object):

    def __init__( self, sensorid, errornumber, errortext):
        self.__sensorid = sensorid
        self.__errornumber = errornumber
        self.__errortext = errortext
        return

    def __iter__( self):
        """i, n, t = Sensorerror( ...)
        """
        for each in (self.__sensorid, self.__errornumber, self.__errortext):
            yield each


class Rover(Object):

    """Mobiler Roboter.

    \param  wTb

    \note   Rover hat selbst keine Intelligenz, die sitzt im RoverController.
    """

    class _RoverInspectors(Object):

        """Gesamtheit aller API-Methoden, die den Rover seiteneffektfrei lesen.
        """

        def __init__( self, mutators):
            self.__mutators = mutators
            return

        def errors_sensors( self) -> tuple:
            """Liefert eine Liste von SensorError's.
            """
            pass

        def wTb( self) -> T3D:
            """BASE relativ WORLD.
            """
            return self.__mutators._wTb_()


    class _RoverMutators(Object):

        """Gesamtheit aller API-Methoden, die den Rover beschreiben.
        """

        def __init__( self):
            self.__wTb = T3D.FromEuler()
            return

        def omage_100( self, omega_100):
            """Rover().chassis().omega_100( omega_100): Sollwert Winkelgeschwindigkeit des Rovers.
            """
            pass

        def v_100( self, v_100):
            """Rover().chassis().v_100( v_100): Sollwert Schwerpuntsgeschwindigkeit des Rovers.
            """
            pass

        def _wTb_( self) -> T3D:
            """Ausführung durch _RoverInspectors.wTb().
            """
            return self.__wTb

        def wTb( self, wTb: T3D):
            """BASE relativ WORLD.
            """
            self.__wTb << wTb
            return self

    ############################################################################
    def __init__( self, wTb: T3D):
        self.__mutators = self._RoverMutators()
        self.__inspectors = self._RoverInspectors( self.__mutators)

        self.__mutators.wTb( wTb)
        assert self.__inspectors.wTb() == wTb
        return

    def execute( self):
        self.execute_hwreaders()
        self.execute_hwwriters()
        return self

    def execute_hwreaders( self):
        for sensor in self.__sensors:
            sensor.execute( self.__mutators)

        return self

    def execute_hwwriters( self):
        self.__propulsion.execute()
        return self

    def inspectors( self):
        return self.__inspectors

    def mutators( self):
        return self.__mutators
