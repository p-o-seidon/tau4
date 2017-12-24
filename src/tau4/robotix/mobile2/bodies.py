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

"""\package mobile2 Alles für die Realisierung mobiler Roboter: Rover Bodies.

\par    Diary
-   2017-11-28: Erstellt. Noch nicht einsatzbereit!

"""

import abc
from math import atan2, degrees, pi, radians

from tau4 import Object
from tau4.ios2 import IOSystem, MotorDriver
from tau4.robotix.mathe import T3D
from tau4.sensors1728 import Distancesensor, Distancesensors, Positionsensor, Positionsensors

import data


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


class RoverBody(Object, abc.ABC):

    """Body eines mobilen Roboters.
    """

    def __init__( self, motordrver: MotorDriver):
        self.__distancesensors = Distancesensors()
        self.__positionsensors = Positionsensors()

        self.__motordriver = motordrver
        return

    def buttons( self, usrid):
        """Liefert den dem Button zugeordneten DInp.
        """
        return IOSystem().dinps( usrid)

    def distancesensors( self):
        return self.__distancesensors

    def distancesensor_add( self, sensor):
        self.__distancesensors.sensor_add( sensor)
        return self

    def execute_sensors( self):
        """Ausführen aller Sensoren.
        """
        if self.__distancesensors:
            self.__distancesensors.execute()

        self.__positionsensor.execute()
        return self

    def execute_actuators( self):
        """Ausführen aller MotorDriver.
        """
        self.__motordriver.execute()
        return self

    def kinematix( self):
        return self.__kinematix

    def positionsensor( self):
        return self.__positionsensor

    def positionsensor_add( self, sensor):
        assert len( self.__positionsensors.sensors()) == 0
        self.__positionsensors.sensor_add( sensor)
        return self

    def switches( self, usrid):
        """Liefert den dem Switch zugeordneten DInp.
        """
        return IOSystem().dinps( usrid)

    def wT( self):
        """Lage relativ {WORLD}.
        """
        return self.__positionsensor.actuals().wT()


class UCKBody(RoverBody):

    def __init__( self, motordrver: MotorDriver):
        super().__init__( self, motordriver=motordrver)

        self.__v_100 = 0
        self.__omega_100 = 0

        self.__vL = 0
        self.__vR = 0
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


