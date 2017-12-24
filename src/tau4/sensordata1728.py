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

import abc
import collections
import ipaddress
from math import *
import time

from tau4 import Id
from tau4 import ios2
from tau4.oop import overrides
from tau4.data import pandora
from tau4.mathe.linalg import T3D, V3D


class _PerformanceCounter:

    def __init__( self, p_readings_per_s):
        self.__p_readings_per_s = p_readings_per_s

        self.__p_readings_per_s.value( 0)

        self.__readingtimes = collections.deque( [], maxlen=3)
        return

    def execute( self):
        self.__readingtimes.append( time.time())

        num_readings = len( self.__readingtimes)
        if num_readings:
            self.__p_readings_per_s.value( num_readings/(time.time() - self.__readingtimes[ 0]))

        return

    def p_readings_per_s( self):
        return self.__p_readings_per_s


class Actuals(metaclass=abc.ABCMeta):

    """Istwerte eines Sensrs.
    """

    class Status:

        class Names:

            _NOT_WORKING = "not working"
            _WORKING = "working"


        class Values:

            _NOT_WORKING = -1
            _WORKING = 1


    _StatusDictValue2Name = { \
        Status.Values._NOT_WORKING: Status.Names._NOT_WORKING,
        Status.Values._WORKING: Status.Names._WORKING,
    }


    @staticmethod
    def StatusName( status_value):
        return Actuals._StatusDictValue2Name[ status_value]




    def __init__( self, id: Id):
        self.__id = id
        self.__status_value = self.Status.Values._NOT_WORKING
        return

    @abc.abstractmethod
    def boxes_to_display( self):
        """Liefert die Boxes jener Werte, die von einem GUI zur Anzeige gebracht werden sollen.
        """
        pass

    def id( self):
        """Eindeutige Id für die Istwerte zu deren Identifikation.
        """
        return self.__id

    @abc.abstractmethod
    def is_ready( self):
        """Ist der Sensor bereit, ist es also sinnvoll, seine Daten auszulesen?

        \_2DO:  Umbenennen in is_working()?
        """
        pass

    def status_value( self, arg=None):
        """Lesen / Schreiben des Status (ein Zahlenwert!)
        """
        if arg is None:
            return self.__status_value

        self.__status_value = arg
        return self

    @abc.abstractmethod
    def update( self):
        """Aktualisieren der Istwerte des Sensors; Ausführung in/durch _actuals_update_() eines Sensor.
        """
        pass


class ActualsDistancesensor(Actuals):

    def __init__( self, id: Id):
        super().__init__( id=id)

        self.__sTm = T3D.FromEuler()

        self.__p_is_ready = pandora.BoxMonitored( value=True, label="%s: Ready?" % self.id())
        self.__p_distance = pandora.BoxMonitored( value=0.0, label="%s: Distance" % self.id(), dim="m")
        self.__performancecounter = _PerformanceCounter( pandora.BoxMonitored( value=0.0, label="%s: Readings/s" % self.id(), dim="1/s"))

        self.__boxes_to_display = (self.__p_is_ready, self.__p_distance, self.__performancecounter.p_readings_per_s())
        return

    @overrides( Actuals)
    def boxes_to_display( self):
        return self.__boxes_to_display

    def distance( self):
        return self.__p_distance.value()

    @overrides( Actuals)
    def is_ready( self):
        return self.__p_is_ready.value()

    def sTm( self):
        """Frame of the measurement relative {SENSOR}, where obstacles are detected in the sensor's Y-direction.
        """
        return self.__sTm

    def rTm( self, rTs: T3D):
        """Frame of the measurement relative {RACK}, where obstacles are detected in the sensor's Y-direction.
        """
        return rTs * self.__sTm

    def update( self, *, is_ready: bool, sTm: T3D):
        self.__p_is_ready.value( is_ready)
        self.__sTm << sTm
        self.__p_distance.value( sTm.y())

        self.__performancecounter.execute()
        return


class ActualsDistancesensorAnalog(ActualsDistancesensor):

    def __init__( self):
        super().__init__()
        return


class ActualsPositionsensor(Actuals):

    """Istwerte von Positionssensoren.
    """

    def __init__( self, id: Id):
        super().__init__( id=id)
        self.__p_is_ready = pandora.BoxMonitored( value=False, label="Is ready")
        self.__p_num_sats = pandora.BoxMonitored( value=0,label="# sats")
        self.__p_wX = pandora.BoxMonitored( value=0.0, label="wX", dim="m")
        self.__p_wY = pandora.BoxMonitored( value=0.0, label="wY", dim="m")
        self.__p_wZ = pandora.BoxMonitored( value=0.0, label="wZ", dim="m")
        self.__p_bA = pandora.BoxMonitored( value=0.0, label="bA", dim="rad")
        self.__p_bX = pandora.BoxMonitored( value=0.0, label="bX", dim="m")
        self.__p_bY = pandora.BoxMonitored( value=0.0, label="bY", dim="m")
        self.__p_bZ = pandora.BoxMonitored( value=0.0, label="bZ", dim="m")

        self.__p_prec_xy = pandora.BoxMonitored( value=0.0, label="prec_xy", dim="m")
        self.__p_prec_z = pandora.BoxMonitored( value=0.0, label="prec_z", dim="m")

        self.__boxes_to_display = (\
            self.__p_is_ready,
            self.__p_wX,
            self.__p_wY,
            self.__p_bX,
            self.__p_bY,
            self.__p_bA,
            self.__p_num_sats
        )
        return

    @overrides(Actuals)
    def boxes_to_display( self):
        """Liefert die Boxes jener Werte, die von einem GUI zur Anzeige gebracht werden sollen.
        """
        return self.__boxes_to_display

    def _bA_( self, arg):
        """Orientierung um Z-Achse relativ {BASE} (Schreiben).

        Ausführung durch _actuals_update_() des Sensor.
        """
        self.__p_bA.value( arg)
        return self

    def bA( self):
        """Orientierung um Z-Achse relativ {BASE} (Lesen).
        """
        return self.__p_bA.value()

    def bX( self):
        """Position relativ {BASE}: X-Koordinate.
        """
        return self.__p_bX.value()

    def bXY( self):
        """Position relativ {BASE}: Tuple aus X- und Y-Koordinate.
        """
        return self.__p_bX.value(), self.__p_bY.value()

    def bY( self):
        """Position relativ {BASE}: Y-Koordinate.
        """
        return self.__p_bY.value()

    def bZ( self):
        """Position relativ {BASE}: Z-Koordinate.
        """
        return self.__p_bZ.value()

    def _bXYZ_( self, x, y, z):
        """Position relativ {BASE}: Triple aus X-, Y- und Z-Koordinate (Schreiben).

        Ausführung durch _actuals_update_() des Sensor.
        """
        self.__p_bX.value( x)
        self.__p_bY.value( y)
        self.__p_bZ.value( z)
        return self

    def _is_ready_( self, b: bool):
        """Arbeitet das Gerät (Schreiben)?

        Ausführung durch _actuals_update_() des Sensor.
        """
        self.__p_is_ready.value( b)
        return self

    @overrides( Actuals)
    def is_ready( self):
        """Arbeitet das Gerät (Lesen)?

        \_2DO: Wie merke ich, dass das Navilock nicht/ready ist?
        """
        return self.__p_is_ready.value()

    def _num_sats_( self, arg: float):
        self.__p_num_sats.value( arg)
        return self

    def num_sats( self):
        return self.__p_num_sats.value()

    def _prec_xy_( self, prec: float):
        """Error margin in meters.

        Ausführung durch _actuals_update_() des Sensor's.
        """
        self.__p_prec_xy.value( prec)
        return self

    def positionprecision_xy( self):
        return self.__p_prec_xy.value()

    def positionprecision_z( self):
        return self.__p_prec_z.value()

    def _prec_z_( self, prec: float):
        """Error margin in meters.

        Ausführung durch _actuals_update_() des Sensor's.
        """
        self.__p_prec_z.value( prec)
        return self

    @overrides( Actuals)
    def update( self, is_ready: bool, wX: float, wY: float, wZ: float, prec_xy: float, prec_z: float, bX: float, bY: float, bZ: float, bA: float, num_sats: int):
        """Aktualisieren der Istwerte des Sensors; Ausführung in/durch _actuals_update_() eines Sensor.
        """
        self._is_ready_( is_ready)
        self._wXYZ_( wX, wY, wZ)
        self._prec_xy_( prec_xy)
        self._prec_z_( prec_z)
        self._bXYZ_( bX, bY, bZ)
        self._bA_( bA)
        self._num_sats_( num_sats)
        return

    def wP( self) -> V3D:
        return V3D( self.__p_wX.value(), self.__p_wY.value(), self.__p_wZ.value())

    def wT( self) -> T3D:
        """Lage relativ {WORLD}.

        \_2DO
            Das sollte die einzige Methode sein, die Auskunft gibt über die Lage.
        """
        return T3D.FromEuler( self.__p_wX.value(), self.__p_wY.value(), self.__p_wZ.value(), self.__p_bA.value())

    def _wXYZ_( self, x, y, z):
        """Position relativ {WORLD}: Triple aus X-, Y- und Z-Koordinate (Schreiben).

        Ausführung durch _actuals_update_() des Sensor.
        """
        self.__p_wX.value( x)
        self.__p_wY.value( y)
        self.__p_wZ.value( z)
        return self

    def wXY( self):
        """Position relativ {WORLD}: Triple aus X-, Y- und Z-Koordinate (Lesen).
        """
        return self.__p_wX.value(), self.__p_wY.value()


class ActualsPositionsensor2(Actuals):

    """Istwerte von Positionssensoren.

    Unterschied zu ActualsPositionsensor: Alles WORLD-basierend.
    """

    def __init__( self, id: Id):
        super().__init__( id=id)
        self.__p_is_ready = pandora.BoxMonitored( value=False, label="Is ready")
        self.__p_num_sats = pandora.BoxMonitored( value=0,label="# sats")

        self.__p_wT = pandora.BoxMonitored( value=T3D.FromEuler(), label="wT")

        self.__p_prec_xy = pandora.BoxMonitored( value=0.0, label="prec_xy", dim="m")
        self.__p_prec_z = pandora.BoxMonitored( value=0.0, label="prec_z", dim="m")

        self.__boxes_to_display = (\
            self.__p_is_ready,
            self.__p_wT,
            self.__p_num_sats
        )
        return

    @overrides(Actuals)
    def boxes_to_display( self):
        """Liefert die Boxes jener Werte, die von einem GUI zur Anzeige gebracht werden sollen.
        """
        return self.__boxes_to_display

    def _is_ready_( self, b: bool):
        """Arbeitet das Gerät (Schreiben)?

        Ausführung durch _actuals_update_() des Sensor.
        """
        self.__p_is_ready.value( b)
        return self

    @overrides( Actuals)
    def is_ready( self):
        """Arbeitet das Gerät (Lesen)?

        \_2DO: Wie merke ich, dass das Navilock nicht/ready ist?
        """
        return self.__p_is_ready.value()

    def _num_sats_( self, arg: float):
        self.__p_num_sats.value( arg)
        return self

    def num_sats( self):
        return self.__p_num_sats.value()

    def _prec_xy_( self, prec: float):
        """Error margin in meters.

        Ausführung durch _actuals_update_() des Sensor's.
        """
        self.__p_prec_xy.value( prec)
        return self

    def positionprecision_xy( self):
        return self.__p_prec_xy.value()

    def positionprecision_z( self):
        return self.__p_prec_z.value()

    def _prec_z_( self, prec: float):
        """Error margin in meters.

        Ausführung durch _actuals_update_() des Sensor's.
        """
        self.__p_prec_z.value( prec)
        return self

    @overrides( Actuals)
    def update( self, *, is_ready: bool, wT: T3D, prec_xy: float, prec_z: float, num_sats: int):
        """Aktualisieren der Istwerte des Sensors; Ausführung in/durch _actuals_update_() eines Sensor.

        \param  is_ready

        \param  wT
            Aktuelle Lage.
        """
        self._is_ready_( is_ready)
        self.__p_wT.value( wT)
        self._prec_xy_( prec_xy)
        self._prec_z_( prec_z)
        self._num_sats_( num_sats)
        return

    def wT( self) -> T3D:
        """Lage relativ {WORLD}.

        \_2DO
            Das sollte die einzige Methode sein, die Auskunft gibt über die Lage.
        """
        return self.__p_wT.value()


class ActualsPositionsensor_EMLIDReach(ActualsPositionsensor):

    pass


class ActualsPositionsensor_Navilock(ActualsPositionsensor):

    pass


class ActualsPositionsensor2_Navilock(ActualsPositionsensor2):

    pass


class Setup(metaclass=abc.ABCMeta):

    def __init__( self, *, id, is_setup, rTs: T3D):
        self.__id = id
        self.__is_setup = is_setup
        self.__rTs = rTs
        return

    def __repr__( self):
        return "<%s>%s</%s>" % (self.__class__.__name__, self.__dict__, self.__class__.__name__)

    def id( self):
        return self.__id

    def is_setup( self, arg=None):
        if arg is None:
            return self.__is_setup

        self.__is_setup = arg
        return self

    def is_sensor_available( self, arg=None):
        return self.is_setup( arg)

    def rTs( self):
        """The sensor's pose on the rack, which it is mounted on.
        """
        return self.__rTs


class SetupDistancesensor(Setup):

    """Konfiguration für einen Distanzsensor.

    \param  is_setup
        Ist der Sensor verfügbar oder soll er ignoriert werden?

    \param  distance_max
        Wie wqeit "sieht" der Sensor maximal?

    \param  rTs
        Wo auf dem Rack (Roboter, Rover, was immer) ist der Sensor montiert?
    """

    def __init__( self, *, id, is_setup: bool, distance_max: float, rTs: T3D):
        super().__init__( id=id, is_setup=is_setup, rTs=rTs)

        self.__distance_max = distance_max
        return

    def distance_max( self):
        return self.__distance_max


class SetupDistancesensorUSS(SetupDistancesensor):

    """Konfiguration eines Ultraschallsensors.

    \param  is_setup
        Ist der Sensor verfügbar oder soll er ignoriert werden?

    \param  distance_max
        Wie weit "sieht" der Sensor maximal?

    \param  rTs
        Wo auf dem Rack (Roboter, Rover, was immer) ist der Sensor montiert?

    \param  dout_trigger
        Ausgang, um den Sensor zu triggern.

    \param  dinp_echo
        Eingang, der beobachtet werden muss. Ist er hi, muss die Zeit berechnet
        werden, die seit dem Triger vergangen ist.

    \par IO-Handling
        Vom IO-Handling her funktionieren die USS anders als alle anderen Sensoren.
        Bei allen Sensoren ist es ja so, dass sie die IOs nicht direkt lesen/schreiben,
        sondern dass eine PLC o.ä. das übernimmt und die Sensoren dann auf die
        bereits gelesenen IOs zugreifen. Beim Schreiben erfolgt der effektive
        Schreibvorgang auf die Hardarwe dann auch mit Verzögerung, weil der Sensor
        den OUT zwar beschreibt, er aber erst am Ende eines PLC-Zylklus effektiv
        auf die Hardware geschrieben wird.

        Bei USS geht das natürlich nicht. Zwar könnte der Schreibvorgang
        verzögert erfolgen, das Lesen muss aber in Echtzeit erfolgen. Wie das
        genau gehen kann, siehe z.B. DistancesensorUss_Devantech_SRF04.
    """

    def __init__( self, *, id, is_setup: bool, dout_trigger: ios2.DOut, dinp_echo: ios2.DInp, distance_max: float, rTs: T3D):
        super().__init__( id, is_setup=is_setup, distance_max=distance_max, rTs=rTs)

        self.__dout_trigger = dout_trigger
        self.__dinp__echo = dinp_echo
        return

    def dinp_echo( self):
        return self.__dinp__echo

    def dout_trigger( self):
        return self.__dout_trigger


class SetupDistancesensorAnalog(Setup):

    def __init__( self, *, ainp_distance_V: ios2.AInp, distance_max):
        self.__distance_max = distance_max

        self.__ainp_distance_V = ainp_distance_V
        return

    def ainp_distance_V( self):
        return self.__ainp_distance_V

    def distance_max( self):
        return self.__distance_max


class SetupPositionsensor(Setup):

    """
    """

    def __init__( self, *, is_setup: bool, rTs: T3D, wTb: T3D):
        super().__init__( is_setup=is_setup, rTs=rTs)
        self.__wTb = wTb
        self.__wTb_inverted = wTb.inverted()
        return

    def wTb( self, arg: T3D=None):
        """{BASE}
        """
        if arg is None:
            return self.__wTb

        self.__wTb << arg
        self.__wTb_inverted << arg.inverted()
        return self

    def wTb_inverted( self):
        """{BASE}
        """
        return self.__wTb_inverted


class SetupPositionsensor2(Setup):

    def __init__( self, *, is_setup: bool, rTs: T3D):
        super().__init__( is_setup=is_setup, rTs=rTs)
        return



class SetupPositionsensor_EMLID_Reach(SetupPositionsensor):

    def __init__( self, is_setup: bool, ipaddr: ipaddress.IPv4Address, portnbr: int, rTs: T3D, wTb: T3D):
        super().__init__( is_setup=is_setup, rTs=rTs, wTb=wTb)
        self.__ipaddr = ipaddr
        self.__portnbr = portnbr
        return

    def ipaddr( self):
        return self.__ipaddr

    def portnbr( self):
        return self.__portnbr


class Utils:

    @staticmethod
    def LL2XY( lat, lon):
        """(LAT, LON -> (wX, wY).
        """
        y = lat * 111.111 * 1000
        x = 111.111 * cos( radians( lat)) * lon * 1000
        return (x, y)
