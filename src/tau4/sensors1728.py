#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by F. Geiger, 1998 - 2017
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

"""\package sensors1728

Synopsis:
    Unterstützung fürs Handling der unterschiedlichsten Sensoren.

History:
    2017-08-14:
        \li Dokumentation.
        \li Änderung von Relevanz in Sensor.execute().
"""


import abc
import collections
import logging; _Logger = logging.getLogger()
from math import *
import pynmea2
import random
import serial
import socket
import sys
import threading
import time

from tau4 import DictWithUniqueKeys
from tau4 import Id
from tau4 import ios2
from tau4 import Object
from tau4 import ThisName
from tau4.automation.statemachines import StatemachineStandard
from tau4.data import pandora
from tau4.datalogging import SysEventLog, UsrEventLog
from tau4.dsp.filters import MovingAverageFilter
from tau4.mathe.linalg import R3D, T3D, V3D
from tau4.multitasking import threads as mtt
from tau4.oop import execute_cyclically, overrides, PublisherChannel
from tau4.oop import Singleton
from tau4 import sensordata1728 as sensordata

try:
    import loggers; _Logger = loggers.LoggerPool().logger( "plc") # 2DO: 2delete!

except (ImportError, KeyError) as e:
    class _Logger:

        def debug( self, *args, **kwargs):
            pass

        critical = debug
        error = debug
        info = debug
        warning = debug


    _Logger = _Logger()


################################################################################
### Sensoren
#
class Sensor(Object, abc.ABC):

    """Base Class für alle Sensoren.

    Konzept:
        Sensoren müssen durch den User per execute() ausgeführt werden. Erst dann
        können die Istwerte abgefragt werden.

        Jede Sub Class muss _actuals_update_() und _execute_() implementieren

    Publishers:
        Keine.

    """

    def __init__( self, id: Id, actuals: sensordata.Actuals, setup: sensordata.Setup):
        assert isinstance( id, Id)
        assert isinstance( actuals, sensordata.Actuals)
        assert isinstance( setup, sensordata.Setup)

        super().__init__( id=id)
        self.__setup = setup
        self.__actuals = actuals

        self.__readingtimes = collections.deque( [], maxlen=15)
        self.__p_readings_per_s = pandora.BoxMonitored( value=0.0, label="Readings/s")
        return

    def actuals( self) -> sensordata.Actuals:
        """Liefert die Istwerte.
        """
        return self.__actuals

    @abc.abstractmethod
    def _actuals_update_( self):
        """Übertragung der in execute() eingelesenen oder berechneten Istwerte in die Actuals, sodass sie per my_sensor.actuals() abgefragt werden können.

        \note   Muss von Sub Classes implementiert werden.

        Usage:
            \code{.py}
                def _actuals_update_( self):
                    '''Übertrag der vom Infrarotsensor gemessenen Hindernisdistanz in die Istwerte.
                    '''
                    distance = min( self.setup().distance_max(), self.__distance)
                    self.actuals().update( is_ready=True, distance=distance)
                    return
            \endcode
        """
        pass

    @abc.abstractmethod
    def conversiondelay( self):
        pass

    @abc.abstractmethod
    def _execute_( self) -> bool:
        """Einlesen und oder Berechnung der Istwerte.

        Die Istwerte sind lokal zu speichern, um sie dann per _actuals_update_()
        in die Actuals zu überführen.

        \note   Muss von Sub Classes implementiert werden.
        """
        pass

    def execute( self):
        """Ausführen des Senors: _execute_() ausführen, bei Erfolg _actuals_update_() ausführen, Readings per Second berechnen.

        \returns    True bei Erfolg, False sonst.

        \b 2017-08-14:
            Istwerte werden neu nicht nur bei Erfolg aktualisiert sondern auch bei
            Misserfolg. Anders wäre es nicht möglich, den Status des Geräts auf NOT WORKING zu setzen!

        """
        ### Sensor ausführen
        #
        success = self._execute_()
        assert isinstance( success, bool)

        ### Istwerte aktualisieren
        #
        self._actuals_update_()

        if success:
            ### Istwerte aktualisieren
            #
            self.__readingtimes.append( time.time())

            num_readings = len( self.__readingtimes)
            if num_readings:
                self.__p_readings_per_s.value( num_readings/(time.time() - self.__readingtimes[ 0]))

        return success

    def p_readings_per_s( self):
        """Anzahl erfolgreiche Sensorlesungen pro Sekunde (liefert die Box).
        """
        return self.__p_readings_per_s

    def readings_per_s( self):
        """Anzahl erfolgreiche Sensorlesungen pro Sekunde (liefert den Wert).
        """
        return self.__p_readings_per_s.value()

    def setup( self):
        """Liefert die Setup-Daten.
        """
        return self.__setup


class SensorCollection(Object):

    def __init__( self):
        self.__sensors = DictWithUniqueKeys()
        return

    def sensor_add( self, sensor: Sensor):
        self.__sensors[ str( sensor.id())] = sensor
        return self

    def sensors( self, id=None):
        if id is None:
            return self.__sensors.values()

        return self.__sensors[ str( id)]


class SensorOwner(metaclass=abc.ABCMeta):

    """\_2DO: Braucht's diese Klasse wirklich?
    """

    @abc.abstractmethod
    def bT( self):
        """The actual pose relative a {BASE} coordiate system.
        """
        pass



class Distancesensor(Sensor):

    """Basisklasse für Distanzmesser wie Infrarot- oder Unltraschallsensoren.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensor):
        super().__init__( id, actuals, setup)
        return


class DistancesensorIrs(Distancesensor):

    """Basisklasse für Infrarotsensoren.
    """

    pass


class DistancesensorIrs_Sharp_GP2D12(DistancesensorIrs):

    """Konkreter Infrarotsensor.
    """

    def __init__( self, *, id: Id, actuals: sensordata.ActualsDistancesensorAnalog, setup: sensordata.SetupDistancesensorAnalog):
        super().__init__( id, actuals, setup)

        self.__distance = 0
        return

    def _actuals_update_( self):
        """Übertrag der vom Infrarotsensor gemessenen Hindernisdistanz in die Istwerte.
        """
        distance = min( self.setup().distance_max(), self.__distance)
        self.actuals().update( is_ready=True, distance=distance)
        return

    def _execute_( self):
        distance_V = self.setup().ainp_distance_V().value()
        distance_mm = 10.0*((4187.8 / distance_V)**1.106)
        self.__distance = distance_mm/1000
        return


class DistancesensorUss(Distancesensor):

    """Ultraschallsensor.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id, actuals, setup)

        self._p_distance = pandora.BoxClipping( value=0.0, bounds=(0, self.setup().distance_max()))
                        # Geclippter Wert, wir wollen kein zu
                        #   scheues Reh.
                        #
                        #   Diese Box dient lediglich dem Clipping.
                        #   Effektiv verwendet wird self._sTm (v.a.
                        #   fürs Update der Actuals).
        self.__filter = MovingAverageFilter( None, "", "", 2)
        self.__is_filter_activated = False

        return

    def filter( self):
        return self.__filter

    def filter_activate( self):
        self.__is_filter_activated = True

    def filter_deactivate( self):
        self.__is_filter_activated = False

    def filter_is_activated( self):
        return self.__is_filter_activated


class DistancesensorUss_Devantech_SRF04(DistancesensorUss):

    """USS von Devantech; arbeitet mit Trigger und Echo; Zeitmessung erforderlich.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id, actuals, setup)

        self._dout_trigger = setup.dout_trigger()
        self._dinp_echo = setup.dinp_echo()

        self._rTs = setup.rTs()

        self._sTm = T3D.FromEuler()

        return

    @overrides(Sensor)
    def _actuals_update_( self):
        """Übertrag der vom Ultraschallsensor gemessenen Hindernisdistanz in die Istwerte.

        Ausführung durch Base Class (Downcall), nachdem _execute_() ausgeführt
        worden ist (also ebenfalls ein Downcall). Geschrieben werden is_ready
        (immer = True) und self._sTm.
        """
        _Logger.debug( "DistancesensorUss_Devantech_SRF04::_actuals_update_(): self._sTm = '%s'. ", self._sTm)
        actuals = self.actuals()
        actuals.update( is_ready=True, sTm=self._sTm)
        return

    @overrides(Sensor)
    def _execute_( self):
        """Ausführung des Sensors, also Messung der Hindernisdistanz durch Ausführen von _measure_().
        """
        this_name = "DistancesensorUss_Devantech_SRF04::_execute_"
        _Logger.debug( "%s(): E n t e r e d. This sensor's id = '%s'. ", this_name, self.id())

        self._measure_()

        _Logger.debug( "%s(): self._sTm = '%s'. ", this_name, self._sTm)
        _Logger.debug( "%s(): Exit now.\n", this_name)
        return True

    def _measure_( self):
        """Ausführung des Sensors, also Messung der Hindernisdistanz.

        Die Messung erfolgt "direkt". Diese Methode blockiert also solange, bis
        das Echo empfangen worden ist.
        """
        this_name = "DistancesensorUss_Devantech_SRF04::_measure_"
        _Logger.debug( "%s(): E n t e r e d. This sensor's id = '%s'. ", this_name, self.id())
        distance = self.setup().distance_max()

        self._dout_trigger.value( 0).execute()
        time.sleep( 0.010)

        self._dout_trigger.value( 1).execute()
        time.sleep( 0.00001)
#        time.sleep( 0.010)
        self._dout_trigger.value( 0).execute()

#        if GPIO.wait_for_edge( self.__gpionmbr_echo, GPIO.RISING, timeout=500):
#            t0 = time.time()
#
#            if GPIO.wait_for_edge( self.__gpionmbr_echo, GPIO.FALLING, timeout=500):
#                t1 = time.time()
#
#                tof = t1 - t0
#                distance = tof * 343 / 2

        t0 = time.time()

# #####
#
        _Logger.debug( "%s(): Wait for echo. ", this_name)
        r = self._dinp_echo.wait_for_falling_edge( timeout_ms=100)
        if r:
            _Logger.debug( "%s(): Echo detected. ", this_name)
            t1 = time.time()

            tof = t1 - t0
            distance = tof * 343.0/2.0
            _Logger.debug( "%s(): distance = %.3f m. ", this_name, distance)

            self._dinp_echo.execute()
                            # Damit auch der Wert für die Anzeige
                            #   z.V. steht, denn oben mussten wir
                            #   die Impl direkt verwenden -> 2DO
        else:
            _Logger.debug( "%s(): Timeout. ", this_name)

        if self.filter_is_activated():
            distance = self.filter().value( distance).execute().value()

        self._p_distance.value( distance)
                        # Geclippter Wert. Grund: USS gehen sehr
                        #   weit und sind daher sozusagen zu
                        #   empfindlich für unsere Zwecke.
#        self.__callback.time_trigger( t0)
#        self.__dinp_echo.execute()
#
# #####

        self._sTm = T3D.FromEuler( 0, self._p_distance.value(), 0)
        _Logger.debug( "%s(): self._sTm = '%s'. ", this_name, self._sTm)
        _Logger.debug( "%s(): Exit now.\n", this_name)
        return True


class DistancesensorUss_Devantech_SRF04_Threaded(DistancesensorUss_Devantech_SRF04):

    class _Cycler(mtt.CyclingThread):

        __lock_for_measure = threading.Lock()
                                        # Das ist nötig wegen GPIO.wait_for_edge().
                                        #   Umsteigen auf wiringPi!!!

        def __init__( self, sensor: DistancesensorUss_Devantech_SRF04, cycletime):
            super().__init__( id="_Cycler", cycletime=cycletime, udata=None)

            self.__sensor = sensor
            return

        def _run_( self, udata):
            with self.__lock_for_measure:
                self.__sensor._measure_()

            return


    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id, actuals, setup)

        self.__cycler = self._Cycler( self, cycletime=0.100)
                                        # Bei 5 km/h entspricht das etwa 140 mm
        self.__cycler.start( syncly=True)
        return

    @overrides( DistancesensorUss_Devantech_SRF04)
    def _execute_( self) -> bool:
        return True


class DistancesensorUss_Devantech_SRF04_Using_Callbacks(DistancesensorUss_Devantech_SRF04):

    """Arbeitet nicht mit Polling sondern mit Callbacks.

    \note   Hat mit dem IO-System <i>Explorer HAT Pro</i> besser funktioniert
    als DistancesensorUss_Devantech_SRF04.
    """

    class Callback4Echo:

        def __init__( self, uss):
            self.__uss = uss

            self.__time_triggered = 0
            self.__time_echo = 0
            self.__is_preecho_detected = False
            self.__is_echo_detected = False
            return

        def callback_on_echo_high( self, *arg):
            """ECHO = hi bedeutet Start der Messung.

            Das Ganze funktioniert so: Nach dem TRIGGER werden die Bursts gesendet.
            Dann geht ECHO auf hi - die Messung ist gestartet. Wenn ECHO auf lo geht,
            kann der Messwert "Zeit" abgelesen werden.
            """
            _Logger.debug( "Callback4Echo::callback_on_echo_high(): Reset the callback instance.")
            self.reset()
            self.__is_preecho_detected = True
                                            # Braucht's das wirklich?
            return

        def callback_on_echo_low( self, *arg):
            """ECHO = lo bedeutet   E n d e   d e r   M e s s u n g.

            Das Ganze funktioniert so: Nach dem TRIGGER werden die Bursts gesendet.
            Dann geht ECHO auf hi - die Messung ist gestartet. Wenn ECHO auf lo geht,
            kann der Messwert "Zeit" abgelesen werden.
            """
            self.__time_echo = time.time()

            d = self.distance()
            self.__uss._p_distance.value( d)
            _Logger.debug( "Callback4Echo::callback_on_echo_low(): d = %.3f m.", d)

            self.__is_echo_detected = True
            return

        def distance( self):
            this_name = "Callback4Echo::distance"

            dt = self.__time_echo - self.__time_triggered
            _Logger.debug( "%s(): dt = %.3f s", this_name, dt)
            ds = dt * 343 / 2
            _Logger.debug( "%s(): ds = %.3f m", this_name, ds)
            return ds

        def is_echo_detected( self):
            return self.__is_echo_detected

        def is_preecho_detected( self):
            return self.__is_preecho_detected

        def reset( self):
            self.__is_echo_detected = False
            self.__is_preecho_detected = False
            self.__time_triggered = time.time()
            _Logger.debug( "Callback4Echo::reset(): Instance reset.")
            return self


    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id, actuals, setup)

        self.__callback = self.Callback4Echo( self)
        self._dinp_echo.add_event_detect_rising( self.__callback.callback_on_echo_high)
        self._dinp_echo.add_event_detect_falling( self.__callback.callback_on_echo_low)

        return

    @overrides( DistancesensorUss_Devantech_SRF04)
    def _execute_( self):
        """Sensor ausführen.

        Wir gehen hier anders vor:

        \li Wir arbeiten mit Callbacks.
        \li Da der Echo-Pin bei Trigger von 0 auf 1 und bei Empfang des Echos
            von 1 auf 0 geht, registrieren wir je einen Callback für die beiden
            unterschiedlichen Ereginisse.
        \li Wir messen wir die Zeit zwischen der steigenden und fallenden Flanke.
            So können wir uns auch den Reset der Zeitmessung in der Callback-Instanz.
            sparen.

        \note   Ein Triggerpuls von 10 us Dauer funktionert hier nicht. Der
                Triggerpuls ist daher hier nicht 10 us sondern 1 ms.
        """
        ### Vorbereitungen
        #
        this_name = "DistancesensorUss_Devantech_SRF04::_execute_"
        _Logger.debug( "%s(): E n t e r e d. ", this_name)
        distance = self.setup().distance_max()

        ### TRIGGER
        #
        self._dout_trigger.value( 0).execute()
        time.sleep( 0.010)

        self._dout_trigger.value( 1).execute()
        time.sleep( 0.001)
        self._dout_trigger.value( 0).execute()

        _Logger.debug( "%s(): Triggered. ", this_name)

        ### Warten auf ECHO
        #
        self.__callback.reset()
        t0 = time.time()
        while time.time() - t0 <= 0.100:
            if self.__callback.is_echo_detected():
                break

            time.sleep( 0.001)

        if not self.__callback.is_echo_detected():
            _Logger.error( "%s(): No Echo detected, set measured distance to %.3f m.", this_name, distance)
            self._p_distance.value( distance)
                                            # Geclippter Wert. Grund: USS gehen sehr
                                            #   weit und sind daher sozusagen zu
                                            #   empfindlich für unsere Zwecke.
        else:
            _Logger.debug( "%s(): Echo (falling edge) detected. d = %.3f m.", this_name, self._p_distance.value())
            pass
                                            # Callback hat den Distanzwert schon in die Box self._p_distance geschrieben
        self._sTm = T3D.FromEuler( 0, self._p_distance.value(), 0)

        self._dinp_echo.clear_events()

        _Logger.debug( "%s(): Exit now.\n", this_name)
        return True


class DistancesensorUss_Devantech_SRF04_Using_CallbackChainer(DistancesensorUss_Devantech_SRF04):

    """Arbeitet nicht mit Polling sondern mit ECHO-Callbacks, die ihrerseite wieder den Sensor TRIGGERn - deswegen der Namens-Suffix CallbackChainer.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id, actuals, setup)

        self.__time_ECHO = 0
        self.__time_TRIG = 0

        self._dinp_echo.add_event_detect_rising( self._on_echo_high_)
        self._dinp_echo.add_event_detect_falling( self._on_echo_low_)

        self._trigger_()

        return

    def _on_echo_high_( self, *args):
        """ECHO = hi bedeutet Start der Messung.

        Das Ganze funktioniert so: Nach dem TRIGGER werden die Bursts gesendet.
        Dann geht ECHO auf hi - die Messung ist gestartet. Wenn ECHO auf lo geht,
        kann der Messwert "Zeit" abgelesen werden.
        """
        if self._dinp_echo.libname() == "pigpio":
            id_sys, level, time_us = args
            self.__time_TRIG = time_us/1000000

        else:
            self.__time_TRIG = time.time()

        return

    def _on_echo_low_( self, *args):
        """ECHO = lo bedeutet   E n d e   d e r   M e s s u n g.

        Das Ganze funktioniert so: Nach dem TRIGGER werden die Bursts gesendet.
        Dann geht ECHO auf hi - die Messung ist gestartet. Wenn ECHO auf lo geht,
        kann der Messwert "Zeit" abgelesen werden.
        """
        if self._dinp_echo.libname() == "pigpio":
            id_sys, level, time_us = args
            self.__time_ECHO = time_us/1000000

        else:
            self.__time_ECHO = time.time()

        dt = self.__time_ECHO - self.__time_TRIG
        ds = dt * 343 / 2
        self._p_distance.value( ds)

        self._trigger_( 0.100)
        return

    @overrides( DistancesensorUss_Devantech_SRF04)
    def _execute_( self) -> bool:
        """Sensor ausführen.

        Wir müssen hier nur die Daten, die die Callbacks berechnet haben, weiterverarbeiten.

        Man könnte hier auch die TRIGGERung machen, denn die Callbacks müssen ja
        nur auf die Edges "schauen". Zur zeit erfolgt die TRIGGERung in den Callbacks.
        """
        self._sTm = T3D.FromEuler( 0, self._p_distance.value(), 0)
        return True

    def _trigger_( self, coolingtime=0.100):
        time.sleep( max( 0, coolingtime))

        self._dout_trigger.value( 0).execute()
        time.sleep( 0.010)

        self._dout_trigger.value( 1).execute()
        time.sleep( 0.001)
        self._dout_trigger.value( 0).execute()

        return


class DistancesensorUss_Devantech_SRF04_Using_PyMata(DistancesensorUss):

    """Zugriff auf SRF04 über PyMata.

    Im Unterschied zu direkten Lösungen werden die IOs von PyMata bedient und nicht
    vom IO-System von TAU4. Den Distanzwert erhalten wir über den Callback _on_ussdata_().

    \param  id      Eindeutige Identifikation des Sensors.
    \param  actuals Istwerte des Sesors.
    \param  setup   Konfigurationsdaten des Sensors.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id=id, actuals=actuals, setup=setup)

        self.__dout_trigger = setup.dout_trigger()
        self.__dinp_echo = setup.dinp_echo()

        self.__distance_cm = -1

        board = self.__dout_trigger.board()
        board.uss_config( self.__dout_trigger.sysid(), self.__dinp_echo.sysid(), self._on_ussdata_)

        return

    @overrides(Sensor)
    def _actuals_update_( self):
        """Übertrag der vom Ultraschallsensor gemessenen Hindernisdistanz in die Istwerte.

        Geschrieben werden is_ready (immer = True) und self._sTm.
        """
        _Logger.debug( "DistancesensorUss_Devantech_SRF04::_actuals_update_(): self._sTm = '%s'. ", self._sTm)
        actuals = self.actuals()
        actuals.update( is_ready=True, sTm=self._sTm)
        return

    @overrides(Sensor)
    def conversiondelay( self):
        """So lange braucht der Sensor, bis er wieder getriggert werden kann.

        \_2DO
            Muss aus dem(?) Datenblatt kommen.
        """
        return 0.050

    def _on_ussdata_( self, datadict):
        self.__distance_cm = datadict[ 1]
        return

    def _execute_( self):
        """Abstandswert verarbeiten, den der Callback _on_ussdata_() "geschickt" hat.
        """
        distance = self.__distance_cm/100.0
        if self.filter_is_activated():
            distance = self.filter().value( distance).execute().value()

        self._p_distance.value( distance)
        self._sTm = T3D.FromEuler( 0, self._p_distance.value(), 0)
        return True


class DistancesensorUss_Devantech_SRF04__Mock(DistancesensorUss):

    """Zugriff auf Software-SRF04, dient somit dem Dev'ment und Debugging anderer Software-Teile.

    \param  id      Eindeutige identifikation des Sensors.
    \param  actuals Istwerte des Sesors.
    \param  setup   Konfigurationsdaten des Sensors.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsDistancesensor, setup: sensordata.SetupDistancesensorUSS):
        super().__init__( id=id, actuals=actuals, setup=setup)

        self.__distance_cm = -1

        return

    @overrides(Sensor)
    def _actuals_update_( self):
        """Übertrag der vom Ultraschallsensor gemessenen Hindernisdistanz in die Istwerte.

        Geschrieben werden is_ready (immer = True) und self._sTm.
        """
        _Logger.debug( "DistancesensorUss_Devantech_SRF04::_actuals_update_(): self._sTm = '%s'. ", self._sTm)
        actuals = self.actuals()
        actuals.update( is_ready=True, sTm=self._sTm)
        return

    def _execute_( self) -> bool:
        """Sensorwerte erzeugen, wirlichen Sensorwerten "ähnlich sehen".
        """
        self.__distance_cm = random.randint( 42, 420)

        distance = self.__distance_cm/100.0
        if self.filter_is_activated():
            distance = self.filter().value( distance).execute().value()

        self._p_distance.value( distance)
        self._sTm = T3D.FromEuler( 0, self._p_distance.value(), 0)
        return True



class Distancesensors(SensorCollection):

    """Collection gleichartiger Sensoren.
    """

    def __init__( self):
        super().__init__()
        return

    ############################################################################
    ### Overrides
    #
    pass

    ############################################################################
    ### Spezialisierung
    #
    def headingvector( self, rTs: T3D) -> V3D:
        """Liefert die Resultierende aller Distanzsensorlesungen.

        \param  rTs
            Lage des Sensors im Rack. Dabei ist angenommen, dass der "Sensorstrahl"
            in x-Richtung verläuft.
        """
        P = V3D()
        for sensor in self.sensors():
            assert isinstance( sensor, Distancesensor)
            actuals = sensor.actuals()
            assert isinstance( actuals, sensordata.ActualsDistancesensor)
            P += actuals.rTm( rTs).P()

        return P


class Positionsensor(Sensor):

    """Base Class für Sensoren, die die Position messen wie zB GPS.

    \param  actuals Istwerte.

    \param  setup   Einstellungen, die nicht mehr geändert werden müssen währen des Laufs.

    Publishers:
        Folgende Publishers sind implementiert, wobei gleich die Registrierungsmethoden
        angegeben sind:

        -   reg_tau4s_on_new_reading():
            Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
            Publisher Channel), wenn eine Lesung erfolgt ist. Die Frequenz, mit
            der diese Methode ausgeführt wird, hängt von der Frequenz ab, mit der
            execute() des Sensors ausgeführt wird und hänggt damit allein von der
            App ab.

        -   reg_tau4s_on_new_position():
            Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
            Publisher Channel), wenn sich die neu gelesene Position von der vorgängig
            gelesenen unterscheidet.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsPositionsensor_Navilock, setup: sensordata.SetupPositionsensor):
        super().__init__( id, actuals, setup)

        self._tau4p_on_new_reading = PublisherChannel.Synch( self)
        self._tau4p_on_new_position = PublisherChannel.Synch( self)

        self._altitude = 0
        self._lat = 0
        self._lon = 0
        self._num_sats = 0
        self._positionprecision_xy, self._positionprecision_z = (-1, -1)

        self._wT = T3D.FromEuler()
                                        # Pose rel. {WORLD}
        self._bP = V3D()
        self._bP_last = V3D()
        self._bA = 0.0
        return

    @overrides( Sensor)
    def _actuals_update_( self):
        """Berechnet (xX, wY, wZ), (bX, bY, bZ) und (bA, 0, 0) und schreibt sie in die Actuals.
        """
        _names = (self.__class__.__name__, "_actuals_update_")
        _Logger.debug( "%s.%s(): E n t e r e d. ", *_names)

        is_new_position = False

        ### Pose und Position in {WORLD}
        #
        wX, wY = sensordata.Utils.LL2XY( self._lat, self._lon)
        wZ = self._altitude
        self._wT << T3D.FromEuler( wX, wY, wZ)
                                        # Pose rel. {WORLD}
        wP = self._wT.P()
                                        # Pos. rel. {WORLD}
        ### Position in {BASE}
        #
        #   Die Berechnung kann so erfolgen:
        #   wP = self._gps_().data().wT().P()
        #                   # Aktuelle Position relativ
        #                   #   {WORLD} - gemessener Wert.
        #   self.__bP << Locator().bases().wB().bP( wP)
        #                                  ^        ^
        #                                  |        |
        #                                  |        w
        #                                  |         P...Aktuelle Position relativ
        #                                  |             {WORLD} - gemessener Wert
        #                                  Base relativ {WORLD} (hat auch ein wTb()).
        #
        _Logger.debug( "%s.%s(): self.setup().wTb() = %s. ", *_names, self.setup().wTb())
        _Logger.debug( "%s.%s(): self.setup().wTb_inverted() = %s. ", *_names, self.setup().wTb_inverted())
        _Logger.debug( "%s.%s(): wP = %s. ", *_names, wP)
        self._bP << self.setup().wTb_inverted() * wP
                                        # Pos. rel. {BASE}
        _Logger.debug( "%s.%s(): self._bP = %s. ", *_names, self._bP)
        bX, bY, bZ = self._bP.xyz()

        ### alpha der Orientierung in {BASE}
        #
        P1 = V3D( *self._bP_last.xy())
        _Logger.debug( "%s.%s(): P1 = %s. ", *_names, P1)
        P2 = V3D( *self._bP.xy())
        _Logger.debug( "%s.%s(): P2 = %s. ", *_names, P2)
        dx = P2.x() - P1.x()
        dy = P2.y() - P1.y()
        if dx or dy:
            self._bA = atan2( dy, dx)
                                            # Das ist die Richtung der Roboter-
                                            #   bewegung. Das muss nicht auch die
                                            #   Richtung  des CS sein! Hier
                                            #   kommt es auf die App an!
            _Logger.debug( "%s.%s(): New self._bA = %.3f°. ", *_names, degrees( self._bA))

            is_new_position = True

        else:
            _Logger.debug( "%s.%s(): No new self._bA. Old self.__bA = %.3f°. ", *_names, degrees( self._bA))

        ### Alle Daten in die Actuals schreiben
        #
        self.actuals().update( \
            is_ready=self.is_connected() and self.is_data_valid(),
            wX=wX, wY=wY, wZ=wZ,
            prec_xy=self._positionprecision_xy, prec_z=self._positionprecision_z,
            bX=bX, bY=bY, bZ=bZ, bA=self._bA,
            num_sats=self._num_sats
        )

        ### Daten für nächsten Aufruf
        #
        self._bP_last << self._bP

        ### Subscribers
        #
        self._tau4p_on_new_reading()

        if is_new_position:
            self._tau4p_on_new_position()

        _Logger.debug( "%s.%s(): Exit now.\n ", *_names)
        return

    @abc.abstractmethod
    def is_connected( self):
        pass

    @abc.abstractmethod
    def is_data_valid( self):
        pass

    def reg_tau4s_on_new_reading( self, tau4s):
        """tau4s registrieren für Ausführung, wenn eine neue Lesung vorliegt.

        Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
        Publisher Channel), wenn eine Lesung erfolgt ist. Die Frequenz, mit
        der diese Methode ausgeführt wird, hängt von der Frequenz ab, mit der
        execute() des Sensors ausgeführt wird und hänggt damit allein von der
        App ab.

        An die gelesene Position kommt der Subsriber per tau4pc.client().actuals().
        """
        self._tau4p_on_new_reading += tau4s
        return self

    def reg_tau4s_on_new_position( self, tau4s):
        """tau4s registrieren für Ausführung, wenn eine neue Position vorliegt, die sich von der letzten unterscheidet.

        Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
        Publisher Channel), wenn sich die neu gelesene Position von der vorgängig
        gelesenen unterscheidet.

        An die gelesene Position kommt der Subsriber per tau4pc.client().actuals().
        """
        self._tau4p_on_new_position += tau4s
        return self


class Positionsensor2(Sensor):

    """Base Class für Sensoren, die die Position messen wie zB GPS.

    \param  actuals Istwerte.

    \param  setup   Einstellungen, die nicht mehr geändert werden müssen währen des Laufs.

    Publishers:
        Folgende Publishers sind implementiert, wobei gleich die Registrierungsmethoden
        angegeben sind:

        -   reg_tau4s_on_new_reading():
            Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
            Publisher Channel), wenn eine Lesung erfolgt ist. Die Frequenz, mit
            der diese Methode ausgeführt wird, hängt von der Frequenz ab, mit der
            execute() des Sensors ausgeführt wird und hänggt damit allein von der
            App ab.

        -   reg_tau4s_on_new_position():
            Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
            Publisher Channel), wenn sich die neu gelesene Position von der vorgängig
            gelesenen unterscheidet.

    \note
        Unterschied zu Positionssensor: Arbeitet in WORLD. Die Umrechung nach BASE muss durch die App erfolgen.
    """

    def __init__( self, id: Id, actuals: sensordata.ActualsPositionsensor2, setup: sensordata.SetupPositionsensor):
        super().__init__( id, actuals, setup)

        self._tau4p_on_new_reading = PublisherChannel.Synch( self)
        self._tau4p_on_new_position = PublisherChannel.Synch( self)

        self._altitude = 0
        self._lat = 0
        self._lon = 0
        self._num_sats = 0
        self._positionprecision_xy, self._positionprecision_z = (-1, -1)

        self._wT = T3D.FromEuler()
                                        # Pose rel. {WORLD}
        self._wP = V3D()
        self._wP_last = V3D()
        return

    @overrides( Sensor)
    def _actuals_update_( self):
        """Berechnet (xX, wY, wZ), (bX, bY, bZ) und (bA, 0, 0) und schreibt sie in die Actuals.
        """
        #_names = (self.__class__.__name__, "_actuals_update_")
        #_Logger.debug( "%s.%s(): E n t e r e d. ", *_names)

        is_new_position = False

        ### Pose und Position in {WORLD}
        #
        wX, wY = sensordata.Utils.LL2XY( self._lat, self._lon)
        wZ = self._altitude
        self._wT << T3D.FromEuler( wX, wY, wZ)
                                        # Pose rel. {WORLD}
        self._wP << self._wT.P()
                                        # Pos. rel. {WORLD}
        ### Position in {BASE}
        #
        #   Die Berechnung kann so erfolgen:
        #   wP = self._gps_().data().wT().P()
        #                   # Aktuelle Position relativ
        #                   #   {WORLD} - gemessener Wert.
        #   self.__bP << Locator().bases().wB().bP( wP)
        #                                  ^        ^
        #                                  |        |
        #                                  |        w
        #                                  |         P...Aktuelle Position relativ
        #                                  |             {WORLD} - gemessener Wert
        #                                  Base relativ {WORLD} (hat auch ein wTb()).
        #
        #_Logger.debug( "%s.%s(): self.setup().wTb() = %s. ", *_names, self.setup().wTb())
        #_Logger.debug( "%s.%s(): self.setup().wTb_inverted() = %s. ", *_names, self.setup().wTb_inverted())
        #_Logger.debug( "%s.%s(): wP = %s. ", *_names, wP)

        ### alpha der Orientierung in {WORLD}
        #
        P1 = V3D( *self._wP_last.xy())
        #_Logger.debug( "%s.%s(): P1 = %s. ", *_names, P1)
        P2 = V3D( *self._wP.xy())
        #_Logger.debug( "%s.%s(): P2 = %s. ", *_names, P2)
        dx = P2.x() - P1.x()
        dy = P2.y() - P1.y()
        if dx or dy:
            wX, wY, wZ, wA, wB, wC = self._wT.euler()
            wA = atan2( dy, dx)
            self._wT << T3D.FromEuler( wX, wY, wZ, wA, wB, wC)
                                            # Das ist die Richtung der Roboter-
                                            #   bewegung in WORLD. Das stimmt
                                            #   natürlich nicht sofort nach
                                            #   Richtungswechseln!
                                            #
                                            # 2DO: Die 3. der obigen 3 Zeilen ist
                                            #   sehr teuer! Geht das auch anders?
            #_Logger.debug( "%s.%s(): New self._bA = %.3f°. ", *_names, degrees( self._bA))

            is_new_position = True

        else:
            _Logger.debug( "%s.%s(): No new self._bA. Old self.__bA = %.3f°. ", *_names, degrees( self._bA))

        ### Alle Daten in die Actuals schreiben
        #
        self.actuals().update( \
            is_ready=self.is_connected() and self.is_data_valid(),
            wT=wX, wY=wY, wZ=wZ,
            prec_xy=self._positionprecision_xy,
            prec_z=self._positionprecision_z,
            num_sats=self._num_sats
        )

        ### Daten für nächsten Aufruf
        #
        self._wP_last << self._wP

        ### Subscribers
        #
        self._tau4p_on_new_reading()

        if is_new_position:
            self._tau4p_on_new_position()

        #_Logger.debug( "%s.%s(): Exit now.\n ", *_names)
        return

    @abc.abstractmethod
    def is_connected( self):
        pass

    @abc.abstractmethod
    def is_data_valid( self):
        pass

    def reg_tau4s_on_new_reading( self, tau4s):
        """tau4s registrieren für Ausführung, wenn eine neue Lesung vorliegt.

        Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
        Publisher Channel), wenn eine Lesung erfolgt ist. Die Frequenz, mit
        der diese Methode ausgeführt wird, hängt von der Frequenz ab, mit der
        execute() des Sensors ausgeführt wird und hänggt damit allein von der
        App ab.

        An die gelesene Position kommt der Subsriber per tau4pc.client().actuals().
        """
        self._tau4p_on_new_reading += tau4s
        return self

    def reg_tau4s_on_new_position( self, tau4s):
        """tau4s registrieren für Ausführung, wenn eine neue Position vorliegt, die sich von der letzten unterscheidet.

        Ausführung des Subscribers mit dem üblichen Argument tau4pc ('pc' für
        Publisher Channel), wenn sich die neu gelesene Position von der vorgängig
        gelesenen unterscheidet.

        An die gelesene Position kommt der Subsriber per tau4pc.client().actuals().
        """
        self._tau4p_on_new_position += tau4s
        return self


class Positionsensor_EMLID_Reach(Positionsensor):

    _CONVERSIONDELAY = 2.0


    ############################################################################
    ### State Machine States
    #
    class State_NOT_READY(StatemachineStandard.State):

        def __init__( self):
            super().__init__(\
                [\
                    StatemachineStandard.State.ExitPoint( self.exitcondition_IS_TRUE, Positionsensor_EMLID_Reach.State_CONNECTING),
                ]
            )
            self.__receiver = Positionsensor_EMLID_Reach._Receiver
            return

        def close( self):
            return

        def execute( self):
            return

        def exitcondition_IS_TRUE( self):
            return True

        def number( self):
            return -1

        def open( self):
            return


    class State_CONNECTING(StatemachineStandard.State):

        def __init__( self):
            super().__init__(\
                [\
                    StatemachineStandard.State.ExitPoint( self.exitcondition_IS_CONNECTED, Positionsensor_EMLID_Reach.State_RECEIVING),
                ]
            )
            self.__receiver = Positionsensor_EMLID_Reach._Receiver
            return

        def close( self):
            return

        def execute( self):
            self.__receiver.connect()
            return

        def exitcondition_IS_CONNECTED( self):
            return self.__receiver.is_connected()

        def number( self):
            return 1

        def open( self):
            return


    class State_RECEIVING(StatemachineStandard.State):

        def __init__( self):
            super().__init__(\
                [\
                    StatemachineStandard.State.ExitPoint( self.exitcondition_ERRORS_OCCURRED, Positionsensor_EMLID_Reach.State_NOT_READY),
                ]
            )
            return

        def close( self):
            self.statemachine().receiver().disconnect()
            return

        def execute( self):
            self.statemachine().receiver().execute()
                                            # Die Daten können jetzt mit
                                            #   self.statemachine().receiver().data() abgeholt
                                            #   werden.
            return

        def exitcondition_ERRORS_OCCURRED( self):
            return self.statemachine().receiver().data() is None

        def number( self):
            return 2

        def open( self):
            return


    ############################################################################
    ### State Machine
    #
    class Statemachine(StatemachineStandard):

        def __init__( self, receiver):
            super().__init__( Positionsensor_EMLID_Reach.State_NOT_READY)

            self.__receiver = receiver

            return

        def is_sensor_connected( self):
            return self.__receiver.is_connected()

        def receiver( self):
            return self.__receiver


    ############################################################################
    ### Receiver
    #
    class ReceiverBT:

        """Empfänger für Daten vom EMLID Reach, wobei der Empfänger ein Bluetooth ist.

        <b>ACHTUNG: In Arbeit!</b>

        EMLID REach muss entspreched konfiguriert werden. Da EMLID Reach als
        Server eine immer wechselnde IP-Adresse hat und ich das nicht über den
        Router regeln will, scheint die bessere Verbindungsmöglicheit zu sein,
        EMLID Reach als Client zu konfigurieren. Dort muss dann eine Server-Adresse
        angebeben werden und die fest 10.0.0.101 - die IP-Adresse des RasPi-Rovers.

        Siehe https://pymotw.com/3/socket/tcp.html#echo-server für einen TCP-Echo-Server.
        """

        def __init__( self, ipaddr, portnbr):
            self.__ipaddr = ipaddr
            self.__portnbr = portnbr

            self.__datastr = b""
            self.__buffersize = 4096
            self.__data = None
            self.__socket = None

            self.__connection = None
            self.__ipaddr_client = None

            self.__is_connected = False
            return

        def connect( self):
            self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout( 1)
            self.__socket.bind( ( str( self.__ipaddr), self.__portnbr))
            try:
                self.__socket.listen( 1)
                self.__connection, self.__ipaddr_client = self.__socket.accept()
                UsrEventLog().log_error( "Client '%s' has connected! " % str( self.__ipaddr_client), ThisName( self))
                self.__is_connected = True

            except (OSError, socket.timeout) as e:
                self.__is_connected = False
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))

            return

        def data( self):
            return self.__data

        def disconnect( self):
            self.__connection.close()

            self.__is_connected = False
            return

        def execute( self):
            while not b"\n" in self.__datastr:
                data = ""
                try:
                    data = self.__connection.recv( self.__buffersize)

                except socket.timeout:
                    pass

                if not len( data):
                    break

                self.__datastr += data

            try:
                items = self.__datastr.split( b"\n")
                self.__data = items[ -2]
                                                # Letzter sicher vollständiger Datensatz
                self.__datastr = items[ -1]
                                                # Unvollständiger "Schwanz" des Datensatzes
                return

            except (IndexError, ValueError) as e:
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))
                                            # Caller muss Socket schließen, sonst
                                            #   laufen wir hier immer in den Timeout!
                self.__data = None

            return None

        def is_connected( self):
            return self.__is_connected


    class ReceiverTcpClient:

        """Empfänger für Daten vom EMLID Reach, wobei der Empfänger ein TCPClient ist.
        """

        def __init__( self, ipaddr, portnbr):
            self.__ipaddr = ipaddr
            self.__portnbr = portnbr

            self.__datastr = b""
            self.__buffersize = 4096
            self.__data = None
            self.__socket = None

            self.__is_connected = False
            return

        def connect( self):
            self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout( 1)
            try:
                self.__socket.connect( (str( self.__ipaddr), self.__portnbr))
                self.__is_connected = True

            except (OSError, socket.timeout) as e:
                self.__is_connected = False
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))

            return

        def data( self):
            return self.__data

        def disconnect( self):
            self.__socket.close()

            self.__is_connected = False
            return

        def execute( self):
            while not b"\n" in self.__datastr:
                data = ""
                try:
                    data = self.__socket.recv( self.__buffersize)

                except socket.timeout:
                    pass

                if not len( data):
                    break

                self.__datastr += data

            try:
                items = self.__datastr.split( b"\n")
                self.__data = items[ -2]
                                                # Letzter sicher vollständiger Datensatz
                self.__datastr = items[ -1]
                                                # Unvollständiger "Schwanz" des Datensatzes
                return

            except (IndexError, ValueError) as e:
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))
                                            # Caller muss Socket schließen, sonst
                                            #   laufen wir hier immer in den Timeout!
                self.__data = None

            return None

        def is_connected( self):
            return self.__is_connected


    class ReceiverTcpServer:

        """Empfänger für Daten vom EMLID Reach, wobei der Empfänger ein TCPClient ist.

        EMLID REach muss entspreched konfiguriert werden. Da EMLID Reach als
        Server eine immer wechselnde IP-Adresse hat und ich das nicht über den
        Router regeln will, scheint die bessere Verbindungsmöglicheit zu sein,
        EMLID Reach als Client zu konfigurieren. Dort muss dann eine Server-Adresse
        angebeben werden und die fest 10.0.0.101 - die IP-Adresse des RasPi-Rovers.

        Siehe https://pymotw.com/3/socket/tcp.html#echo-server für einen TCP-Echo-Server.
        """

        def __init__( self, ipaddr, portnbr):
            self.__ipaddr = ipaddr
            self.__portnbr = portnbr

            self.__datastr = b""
            self.__buffersize = 4096
            self.__data = None
            self.__socket = None

            self.__connection = None
            self.__ipaddr_client = None

            self.__is_connected = False
            self.__is_data_valid = False
            return

        def connect( self):
            self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout( 1)
            try:
                self.__socket.bind( ( str( self.__ipaddr), self.__portnbr))
                self.__socket.listen( 1)
                self.__connection, self.__ipaddr_client = self.__socket.accept()
                UsrEventLog().log_error( "Client '%s' has connected! " % str( self.__ipaddr_client), ThisName( self))
                self.__is_connected = True

            except (OSError, socket.timeout) as e:
                self.__is_connected = False
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))

            return

        def data( self):
            return self.__data

        def disconnect( self):
            self.__connection.close()

            self.__is_connected = False
            return

        def execute( self):
            while not b"\n" in self.__datastr:
                data = ""
                try:
                    data = self.__connection.recv( self.__buffersize)
                    self.__is_data_valid = True

                except socket.timeout:
                    pass

                if not len( data):
                    break

                self.__datastr += data

            try:
                items = self.__datastr.split( b"\n")
                print( ThisName( self) + "(): %s. " % items)
                self.__data = items[ -2]
                                                # Letzter sicher vollständiger Datensatz
                self.__datastr = items[ -1]
                                                # Unvollständiger "Schwanz" des Datensatzes
                return

            except (IndexError, ValueError) as e:
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))
                                            # Caller muss Socket schließen, sonst
                                            #   laufen wir hier immer in den Timeout!
                self.__data = None
                self.__is_data_valid = False

            return None

        def is_connected( self):
            return self.__is_connected

        def is_data_valid( self):
            return self.__is_data_valid


    class ReceiverSerial:

        def __init__( self, portname="/dev/ttyACM0", baudrate=115200):
            self.__portname = portname
            self.__baudrate = baudrate

            self.__datastr = b""
            self.__buffersize = 4096
            self.__data = None
            self.__serial = None
            return

        def connect( self):
            self.__serial = serial.Serial( port="/dev/ttyACM0", baudrate=115200)
            self.__serial.timeout = 0.5
            return

        def data( self):
            return self.__data

        def disconnect( self):
            self.__serial.close()
            return

        def execute( self):
            while not b"\n" in self.__datastr:
                #data = self.__serial.read( self.__buffersize)
                data = self.__serial.read( self.__serial.inWaiting() or 1)
                if not len( data):
                    break

                self.__datastr += data

            try:
                items = self.__datastr.split( b"\n")
                self.__data = items[ -2]
                                                # Letzter sicher vollständiger Datensatz
                self.__datastr = items[ -1]
                                                # Unvollständiger "Schwanz" des Datensatzes
                return

            except (IndexError, ValueError) as e:
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))
                                            # Caller muss Socket schließen, sonst
                                            #   laufen wir hier immer in den Timeout!
                self.__data = None

            return None

        def is_connected( self):
            return self.__serial.isOpen()


    ############################################################################
    ### Position Sensor
    #
    def __init__( self, id: Id, actuals: sensordata.ActualsPositionsensor_EMLIDReach, setup: sensordata.SetupPositionsensor_EMLID_Reach):
        assert isinstance( actuals, sensordata.ActualsPositionsensor_EMLIDReach)
        assert isinstance( setup, sensordata.SetupPositionsensor_EMLID_Reach)
        super().__init__( id, actuals, setup)

        #receiver = Positionsensor_EMLID_Reach._Receiver = Positionsensor_EMLID_Reach.ReceiverTcpClient( setup.ipaddr(), setup.portnbr())
        receiver = Positionsensor_EMLID_Reach._Receiver = Positionsensor_EMLID_Reach.ReceiverTcpServer( setup.ipaddr(), setup.portnbr())
        self.__statemachine = self.Statemachine( receiver)
        return

    @overrides( Positionsensor)
    def _actuals_update_( self):
        data = self.__statemachine.receiver().data()
        if data:
            try:
                #self._nmea2actuals_( data)
                self._llh2actuals_( data)
                super()._actuals_update_()

            except AttributeError as e:
                self.actuals()._is_ready_( False)

        else:
            self.actuals()._is_ready_( False)

        return

    @overrides( Positionsensor)
    def conversiondelay( self):
        return self._CONVERSIONDELAY

    @execute_cyclically( _CONVERSIONDELAY)
    @overrides( Positionsensor)
    def _execute_( self):
        if self.setup().is_setup():
            self.__statemachine.execute()

        return True

    @overrides( Positionsensor)
    def is_connected( self):
        return self.__statemachine.is_sensor_connected()

    @overrides( Positionsensor)
    def is_data_valid( self):
        return self.__statemachine.receiver().is_data_valid()

    def _llh2actuals_( self, data):
        try:
            items = str( data, "utf-8").split( " ")
            self._lat = float( items[ 4])
            self._lon = float( items[ 8])
            self._altitude = float( items[ 11])
            self._num_sats = int( items[ 17])

        except ValueError as e:
            UsrEventLog().log_error( "An error occurred upon value conversions: '%s'!" % e, ThisName( self))

        return

    def _nmea2actuals_( self, data):
        nmea_object = pynmea2.parse( str( data, "utf-8"))
        self._lat = float( nmea_object.lat)
        self._lon = float( nmea_object.lon)
        self._altitude = float( nmea_object.altitude)
        self._num_sats = int( nmea_object.num_sats)
        return


class Positionsensor_Navilock(Positionsensor):

    """Navilock an USB, zB NL-602U oder NL-8002U.
    """

    _CONVERSIONDELAY = 1.0


    def __init__( self, id: Id, actuals: sensordata.ActualsPositionsensor_Navilock, setup: sensordata.SetupPositionsensor):
        super().__init__( id, actuals, setup)
        self.__is_connected = False
        self.__is_data_valid = False
        return

    @overrides( Positionsensor)
    def conversiondelay( self):
        return self._CONVERSIONDELAY

    @execute_cyclically( _CONVERSIONDELAY)
    @overrides( Positionsensor)
    def _execute_( self) -> bool:
        """Liest den GPS Receiver: Mode 2D: LAT, LON, #SATS; Mode 3D: ALT.

        Was in welchem Mode möglich ist, findet man unter
        https://github.com/MartijnBraam/gpsd-py3/blob/master/DOCS.md. SO ist
        z.B. die Höhe (altitude()) nur bei Mode >= 3 (= 3D) möglich.

        Daten, die nicht verfügbar sind, werden typgerecht mit -1 belegt.
        """
        success = False

        if self.setup().is_sensor_available():

            import gpsd
            if not self.__is_connected:
                try:
                    gpsd.connect()

                    self.__is_connected = True

                except Exception as e:
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

            if self.__is_connected:
                try:
                    gpsd_response = gpsd.get_current()
                                                    # May raise KeyError -> ?!
                    self._lat, self._lon = gpsd_response.position()
                    self._num_sats = gpsd_response.sats
                    self._altitude = gpsd_response.altitude() if gpsd_response.mode >=3 else -1

                    self._positionprecision_xy, self._positionprecision_z = gpsd_response.position_precision()

                    self.__is_data_valid = True
                    success = True

                except gpsd.NoFixError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

                except IndexError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

                except KeyError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

        return success

    @overrides( Positionsensor)
    def is_connected( self):
        return self.__is_connected

    @overrides( Positionsensor)
    def is_data_valid( self):
        return self.__is_data_valid


class Positionsensor2_Navilock(Positionsensor2):

    """Navilock an USB, zB NL-602U oder NL-8002U.
    """

    _CONVERSIONDELAY = 1.0


    def __init__( self, id: Id, actuals: sensordata.ActualsPositionsensor_Navilock, setup: sensordata.SetupPositionsensor):
        super().__init__( id, actuals, setup)
        self.__is_connected = False
        self.__is_data_valid = False
        return

    @overrides( Positionsensor)
    def conversiondelay( self):
        return self._CONVERSIONDELAY

    @execute_cyclically( _CONVERSIONDELAY)
    @overrides( Positionsensor)
    def _execute_( self) -> bool:
        """Liest den GPS Receiver: Mode 2D: LAT, LON, #SATS; Mode 3D: ALT.

        Was in welchem Mode möglich ist, findet man unter
        https://github.com/MartijnBraam/gpsd-py3/blob/master/DOCS.md. SO ist
        z.B. die Höhe (altitude()) nur bei Mode >= 3 (= 3D) möglich.

        Daten, die nicht verfügbar sind, werden typgerecht mit -1 belegt.
        """
        success = False

        if self.setup().is_sensor_available():

            import gpsd
            if not self.__is_connected:
                try:
                    gpsd.connect()

                    self.__is_connected = True

                except Exception as e:
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

            if self.__is_connected:
                try:
                    gpsd_response = gpsd.get_current()
                                                    # May raise KeyError -> ?!
                    self._lat, self._lon = gpsd_response.position()
                    self._num_sats = gpsd_response.sats
                    self._altitude = gpsd_response.altitude() if gpsd_response.mode >=3 else -1

                    self._positionprecision_xy, self._positionprecision_z = gpsd_response.position_precision()

                    self.__is_data_valid = True
                    success = True

                except gpsd.NoFixError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

                except IndexError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

                except KeyError as e:
                    self.__is_data_valid = False
                    SysEventLog().log_error( "GPSD error: '%s'. " % e, ThisName( self))

        return success

    @overrides( Positionsensor)
    def is_connected( self):
        return self.__is_connected

    @overrides( Positionsensor)
    def is_data_valid( self):
        return self.__is_data_valid


class Positionsensors(SensorCollection):

    pass


class Sensors(metaclass=Singleton):

    @staticmethod
    def rAlpha( sensors):
        """Calculate the angle of the resultant rPo.

        This simple algo allows us to check for obstacles. The size of the angle
        in absence of an obstacle depends on the transforms you defined in your
        app. If you defined the transforms so that the y-axis points into the
        sensing direction, the angle must equal to 90° in absensce of any obstacle.
        In that case the angle is
        --  less than 90° if an obstacle approaches from the
            left hand side and it is

        --  greater than 90° if it approaches from the right
            hand side.
        """
        cname, fname = "Sensors", "rApha"

        _Logger.debug( "%s::%s(): E n t e r e d. ", cname, fname)

        P = V3D()
        for sensor in sensors:
            rTm = sensor.actuals().rTm( rTs=sensor.setup().rTs())
            rPm = rTm.P()
            P += rPm

            _Logger.debug( "%s::%s(): Sensor id = '%s'. ", cname, fname, sensor.id())
            _Logger.debug( "%s::%s(): sTm = '%s'. ", cname, fname, sensor.actuals().sTm())
            _Logger.debug( "%s::%s(): rTs = '%s'. ", cname, fname, sensor.setup().rTs())
            _Logger.debug( "%s::%s(): rTm = '%s'. ", cname, fname, rTm)
            _Logger.debug( "%s::%s(): rPm = '%s'. ", cname, fname, rPm)
            _Logger.debug( "%s::%s(): P = '%s'. ", cname, fname, P)

        alpha = atan2( P.y(), P.x())
        _Logger.debug( "%s::%s(): alpha = '%3f°. ", cname, fname, degrees( alpha))

        _Logger.debug( "%s::%s(): Exit now.\n", cname, fname)
        return alpha


    @staticmethod
    def rDistance( sensors):
        """Calculate the length of the resultant rPo.

        General explanation see above.

        The resaon for this method is: If the obstacle approaches straight in
        front of the robot, alpha will be zero and the obstacle will not be
        avoided. But a collision would be unevitable. So, additionally we have
        to consider the length of the resultant.

        """
        P = V3D()
        for sensor in sensors:
            rPm = sensor.actuals().rTm( sensor.setup().rTs()).P()
            P += rPm

        distance = P.mag()
        return distance


    def __init__( self):
        self.__navdevs = {}
        self.__rangers_dict = collections.OrderedDict()
        self.__rangers_available = []
        return

    def execute( self):
        raise NotImplementedError( "Not implemented, today and in future. Call execute_rangers(), execute_navdevs() etc. instead!")
        self.execute_navdevs()
        self.execute_rangers()
        return

    def execute_navdevs( self):
        for sensor in self.navdevs_available():
            sensor.execute()

        return

    def execute_rangers( self):
        for sensor in self.rangers_available():
            sensor.execute()

        return

    def navdev_add( self, sensor: Positionsensor):
        if sensor.id() in self.__navdevs:
            raise KeyError( "Ranger '%s' already added!" % sensor.id())

        self.__navdevs[ sensor.id()] = sensor
        return

    def navdevs( self, id: Id=None):
        if id is None:
            return self.__navdevs.values()

        return self.__navdevs[ id]

    def navdevs_available( self):
        return [sensor for sensor in self.navdevs() if sensor.setup().is_setup()]

    def navdevs_execute( self):
        for sensor in self.navdevs():
            sensor.execute()

        return self

    def ranger_add( self, ranger: Distancesensor):
        if str( ranger.id()) in self.__rangers_dict:
            raise KeyError( "Ranger '%s' already added!" % ranger.id())

        self.__rangers_dict[ str( ranger.id())] = ranger
        self.__rangers_dict = collections.OrderedDict( sorted( self.__rangers_dict.items()))
        self.__rangers_available = [sensor for sensor in self.rangers() if sensor.setup().is_setup()]

        return

    def rangers( self, id: Id=None):
        if id is None:
            return self.__rangers_dict.values()

        return self.__rangers_dict[ str( id)]

    def rangers_available( self):
        return self.__rangers_available

    def rangers_smallest_distance( self):
        rangers = self.rangers_available()
        if rangers:
            return min( [ranger.actuals().distance() for ranger in rangers])

        return sys.float_info.max



################################################################################
### Lokalisierung
#
class BaseTeachable:

    """Eine Base relativ irgendeiner anderen Base, wobei die Base geteacht werden kann.

    2DO:
        Refactoring: Base Class erzeugen.
    """

    def __init__( self):
        ### Das CS
        #
        self.__xTb = T3D.FromEuler()
                                        # Transformation der Base relativ
                                        #   igendwas (deswegen das 'x'). Meist
                                        #   wird das Irgendwas allerdings {WORLD}
                                        #   sein.
        self.__xTb_inverted = self.__xTb.inverted()
                                        # Die Inversion davon.
        self.__xTb_last_known_good = T3D.FromEuler()
                                        # Last known good
        ### Die Vektoren der Positionen, die geteacht werden. Sie werden aus den
        #   Variablen berechnet (s. close()).
        #
        self.__p_org = V3D()
        self.__p_x = V3D()
        self.__p_xy = V3D()

        ### Variable, die die geteachten Werte persistent speichern können und
        #   auch der Anzeige der Base dienen. Aus ihnen werden die 3 geteachten
        #   Vektoren (s. oben) berechnet.
        #
        p = self._p_wX_org_teached = pandora.BoxMonitored( id="baseframe.p_wX_org_teached", value=0.0, label="Xorg teached", dim="m")
        pandora.Shelf().box_restore( p)
        p = self._p_wY_org_teached = pandora.BoxMonitored( id="baseframe.p_wY_org_teached", value=0.0, label="Yorg teached", dim="m")
        pandora.Shelf().box_restore( p)

        p = self._p_wX_x_teached = pandora.BoxMonitored( id="baseframe.p_wX_x_teached", value=0.0, label="Xx teached", dim="m")
        pandora.Shelf().box_restore( p)
        p = self._p_wY_x_teached = pandora.BoxMonitored( id="baseframe.p_wY_x_teached", value=0.0, label="Yx teached", dim="m")
        pandora.Shelf().box_restore( p)

        p = self._p_wX_xy_teached = pandora.BoxMonitored( id="baseframe.p_wX_xy_teached", value=0.0, label="Xxy teached", dim="m")
        pandora.Shelf().box_restore( p)
        p = self._p_wY_xy_teached = pandora.BoxMonitored( id="baseframe.p_wY_xy_teached", value=0.0, label="Yxy teached", dim="m")
        pandora.Shelf().box_restore( p)

        ### Gemüse
        #
        self.__is_open_for_teaching = False

        ### Nun laden wir die Variablen in die Vektoren und berechnen den
        #   Frame xTb durch Ausführen von close().
        #
        self.__p_org << V3D( self._p_wX_org_teached.value(), self._p_wY_org_teached.value(), 0)
        self.__p_x << V3D( self._p_wX_x_teached.value(), self._p_wY_x_teached.value(), 0)
        self.__p_xy << V3D( self._p_wX_xy_teached.value(), self._p_wY_xy_teached.value(), 0)

        ### Nutzdaten aus Teaching-Daten berechnen
        #
        try:
            self.open()
            self.close()
                                            # Die Berechnung erfolgt effektiv in
                                            #   close().
        except ZeroDivisionError as e:
            UsrEventLog().log_error( "Cannot calculate frame xTb: '%s'" % e, ThisName( self))
            raise e

        return

    def __repr__( self):
        return "Porg=" + repr( self.__p_org)

    def bP( self, xP: V3D) -> V3D:
        """Transformiert eine Position in die Base.

        Die Originalposition muss natürlich aus dem gleichen CS X kommen, in dem
        sich diese Base befindet.
        """
        #assert not self.__is_open_for_teaching
        # ##### Unnötige Einschränkung?

        xT = T3D( R3D.FromEuler(), xP)
        bT = self.__xTb_inverted * xT
        return bT.P()

    def close( self, cancel=False): # Raises ZeroDivisionError
        """Effektive Berechnung der Transformation und Speicherung aller Werte, die fürs Restore und die Anzeige gebraucht werden.
        """
        _Logger.info( "E n t e r e d.")
        assert self.__is_open_for_teaching

        if cancel == False:
                                        # Real close, not a cancel.
            ### Die 3 Vektoren berechnen
            #
            self.__p_org << V3D( self._p_wX_org_teached.value(), self._p_wY_org_teached.value(), 0)
            _Logger.info( "p_wOrg = '%s'. ", self.__p_org)
            self.__p_x << V3D( self._p_wX_x_teached.value(), self._p_wY_x_teached.value(), 0)
            _Logger.info( "p_wX = '%s'. ", self.__p_x)
            self.__p_xy << V3D( self._p_wX_xy_teached.value(), self._p_wY_xy_teached.value(), 0)
            _Logger.info( "p_wXY = '%s'. ", self.__p_xy)

            ### Frame berechnen
            #
            try:
                P0 = self.__p_org
                PX = self.__p_x
                PXY = self.__p_xy

                P0X = PX - P0
                            # X-Achse, nicht normalisiert
                P0XY = PXY - P0
                            # Vektor zum Punkt in pos. XY-Ebene
                ex = P0X.normalized()
                            # X-Achse
                ez = P0X.ex( P0XY).normalized()
                            # Z-Achse
                ey = ez.ex( ex)
                            # Y-Achse
                R = R3D.FromVectors( ex, ey, ez)
                T = T3D( R, P0)

                self.__xTb_last_known_good << self.__xTb
                            # Aktuellen Frame als zuletzt gültigen sichern.
                _Logger.info( "Saved last known good frame: xTb = '%s'.", self.__xTb_last_known_good)
                self.__xTb << T
                _Logger.info( "xTb = '%s'. ", self.__xTb)
                self.__xTb_inverted = self.__xTb.inverted()

            except ZeroDivisionError as e:
                                            # Die geteachten Positionen sind zu
                                            #   nah beieinander.
                UsrEventLog().log_error( "'%s'. " % e, ThisName( self))
#                raise e
# ##### We run in a thread very likely. So, the calling program parts don't know how
    #   to handle this exception

            finally:
                self.__is_open_for_teaching = False


        else:
            self.__is_open_for_teaching = False

        _Logger.info( "Exit now.\n")
        return self

    def open( self):
        """Base zum Ändern öffnen.
        """
        assert not self.__is_open_for_teaching
        self.__is_open_for_teaching = True
        return self

    def org( self, x, y, z):
        """Teach Point: Ursprung der Base relativ X.
        """
        assert self.__is_open_for_teaching

        self.__p_org << V3D( x, y, z)
        return self

    def p_wX_org_teached( self):
        """X-Koordinate von P0.
        """
        return self._p_wX_org_teached

    def p_wY_org_teached( self):
        """Y-Koordinate von P0.
        """
        return self._p_wY_org_teached

    def p_wX_x_teached( self):
        """X-Koordinate von PX.
        """
        return self._p_wX_x_teached

    def p_wY_x_teached( self):
        """Y-Koordinate von PX.
        """
        return self._p_wY_x_teached

    def p_wX_xy_teached( self):
        """X-Koordinate von PXY.
        """
        return self._p_wX_xy_teached

    def p_wY_xy_teached( self):
        """Y-Koordinate von PXY.
        """
        return self._p_wY_xy_teached

    def is_open( self):
        return self.__is_open_for_teaching

    def xPorg( self):
        """Porg relativ {X}.

        Könnte man auch als xPorg() bezeichnen.
        """
        return self.__p_org

    def restore_last_known_good( self):
        self.__xTb << self.__xTb_last_known_good
        return

    def x( self, x, y, z):
        """Teach Point: Position auf der x-Achse relativ X.
        """
        assert self.__is_open_for_teaching

        self.__p_x << V3D( x, y, z)
        return self

    def xT( self) -> T3D:
        return self.__xTb

    def xy( self, x, y, z):
        """Teach Point: Position in der positiven xy-Ebene relativ X.
        """
        assert self.__is_open_for_teaching

        self.__p_xy << V3D( x, y, z)
        return self


class _Bases:

    """The :py:class:`Locator` 's bases.

    At this time the following bases are available:
    --  wB
            THE base relative {WORLD}.


    """

    def __init__( self):
        self.__wB = BaseTeachable()
        return

    def wB( self):
        """THE base relative {WORLD}.
        """
        return self.__wB


class Locator(metaclass=Singleton):

    """Container for all bases.

    See :py:class:`_Bases`.
    """

    def __init__( self):
        self.__bases = _Bases()
        return

    def bases( self):
        """Bases held by the Locator.
        """
        return self.__bases


class DistanceSensor_ContourDetector(Distancesensor):

    """Dokumentation siehe file:///home/fgeiger/D.X/Projects/DDG/cruiser/dox/cruiser.main.odt!
    """

    @classmethod
    def SymPyVersion( cls, owner : SensorOwner, id, bContourpoints : tuple, rTs : T3D):
        return cls( owner, id, bContourpoints, rTs)

    def __init__( self, owner : SensorOwner, id, contourpoints : tuple, rTs : T3D):
        super().__init__( id, rTs)
        self.__owner = owner
        self.__contourpolygon = sympy.Polygon( *contourpoints)
        self.__rTs = rTs

        self.__data = SensorData_DistanceSensor( SensorStatus())
        self.__reach = 3
        self.__p_distance = pandora.Box( value=0.0)
        return

    def data( self):
        return self.__data

    def _execute_( self):
        bTr = self.owner().bT()
                                        # {RACK} we are mounted on, relative {BASE}
        rTs = self.__rTs
                                        # {SENSOR} relative {RACK}, we are mounted on.
        sTm = T3D.FromEuler( 0, self.reach(), 0)
                                        # This far the sensor beam reaches w/o
                                        #   detecting the contour.
        bTm = bTr * rTs * sTm
                                        # Pose of the beam's end relative {BASE}
        bPm = bTm.P()
                                        # Position of the beam's end relative {BASE}
        bTs = bTr * rTs
        pt1 = sympy.Point( *bTs.P().xy())
        pt2 = sympy.Point( *bPm.xy())
        if not self.__contourpolygon.encloses_point( pt2):
            if self.__contourpolygon.encloses_point( pt1):
                segment = sympy.Segment( pt1, pt2)
                pt = list( self.__contourpolygon.intersect( segment))[ 0]
                distance = pt1.distance( pt)

            else:
                distance = 0

        else:
            distance = self.reach()

        self.__p_distance.value( distance)
        return True

    def owner( self):
        """2DO: Move this into a base class.
        """
        return self.__owner

    def p_distance( self):
        return self.__p_distance

    def p_value_default( self):
        return self.__p_distance

    def rTm( self):
        """Measurement relative {RACK}, which the sensor is mounted on.
        """
        return

    def rTs( self):
        """Pose of the sensor relative {RACK}, which the sensor is mounted on.
        """
        return self.__rTs

    def reset( self):
        return

    def sTm( self):
        """Measurement relative {SENSOR}.
        """
        return

#    def __init__( self, rT: T3D):
#        self.__reach = 0.8
#
#        self.__rT = rT
#                                        # Lage des Sensors {S} in {R}.
#        self.__Th = T3D.FromEuler( 0, self.reach(), 0, 0, 0, 0)
#                                        # Lage der Strahlspitze in {S}.
#        self.__bTr = T3D.FromEuler()
#                                        # Lage von {R} in {B}. Wird bei jeder
#                                        #   Ausführung von execute() neu gesetzt.
#        return

    def execute_SAVE_FOR_LATER( self):
        """Sensor ausführen: Schnittpunkt mit Contour berechnen und hieraus den Heading Vector.

        contour:
            Contour, mit der der Strahl evtl. einen Schnittpunkt hat.

        bTr:
            Lage von {R} in {B}.
        """
        self.__bTr = bTr
                                        # {R} in {B}
        bT = self.bT( bTr)
                                        # {S} in {B}
        bTh = self.bTh( bTr)
                                        # Strahlende in {B}
        beam = Segment.FromT3D( bT, bTh)
        points = contour.intersection( beam)
                                        # Schnittpunkt (oder Strahlende) in {B}.
        if points:
            bPi = Point( points[ 0])
                                            # 2DO: Ist der erste Punkt immer der
                                            #   am nächsten liegende?
            bTi = T3D.FromEuler( *bPi.comps())
                                            # Schnittpunkt gefunden.
        else:
            bTi = self.bTh( bTr)
                                            # Keinen Schnittpunkt gefunden, nehmen
                                            #   das Strahlende
        rTi = bTr.inverted() * bTi
                                        # Schnittpunkt in {R}. Dieser Wert
                                        #   wird für die Berechnung des
                                        #   Heading Vector verwendet!
        self.__rTi = rTi
        return

    def bT( self, bTr: T3D):
        """Lage des Sensors in {B}.

        Punkt 1 des Segments, das durch den Strahl definiert wird.
        """
        rT = self.__rT
                                        # {S} in {R}
        bT = bTr * rT
                                        # {S} in {B}
        return bT

    def bTh( self, bTr: T3D):
        """Lage der Sensorstrahlspitze in {B}.

        Punkt 2 des Segments, das durch den Strahl definiert wird.
        """
        rT = self.__rT
                                        # {S} in {R}
        Th = self.__Th
                                        # Lage der Strahlspitze in {S}.
        bTh = bTr * rT * Th
                                        # Lage der Strahlspitze in {B}.
        return bTh

    def bTi( self):
        """Lage des Schnittpunktes {I} in {B}.

        Anm.:
            Die Berechnung des Schnittpunktes erfolgt in {B}.
        """
        return bTi

    def headingvectorR( self):
        rTi = self.__rTi
                                        # Schnittpunkt in {R}
        hv = rTi.P()
        return hv

    def _is_point_in_contour_( self, p : V3D):
        """Returns True, if p lies w/i the contour.

        Th point we check is the end of the sensors virtual beam. If the vector
        to the end of the beam lies w/i the contour, then the sensor is considered
        being sufficiently far away from the contour and no intersection point has
        to be computed. Precond.: The sample time is 'small enough'.
        """
        return

    def reach( self, arg=None):
        """Reichweite des Strahls.

        Anm.:
            Sollte reach() einmal änderbar sein, dann muss immer auch self.__Th
            neu berechnet werden, wenn reach geändert wird.
        """
        if arg is None:
            return self.__reach

        self.__reach = float( arg)
        self.__Th = T3D.FromEuler( 0, self.reach(), 0, 0, 0, 0)
        return self

    def rTi( self):
        """Lage des Schnittpunktes {I} in {R}.
        """
        bTi = self.bTi()
        bTr = self.__bTr

        rTi = bTr.inverted() * bTi
        return rTi

    def rT( self):
        """Lage des Sensors {S} in {R}.
        """
        return self.__rT

