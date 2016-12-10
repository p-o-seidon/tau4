#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2016
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

import logging

import abc
import collections
import datetime
import time
from math import *
import socket

#import gpsd
from tau4 import ThisName
from tau4.com import mbus
from tau4.data import flex
from tau4.datalogging import UsrEventLog
from tau4.mathe.linalg import R3D, T3D, Vector3
from tau4.sweng import overrides
from tau4.sweng import PublisherChannel
from tau4.sweng import Singleton


class BaseFrame_DEBRECATED__USE_BaseFrameTeachable:
    
    """Base Frame.
    
    Base Frame z.B. eines GPS-Sensors. Der GPS-Sensor muss eine Instanz dieser 
    Klasse enthalten und sie mit P0, PX und PXY beschreiben, sobald diese auf 
    WORLD bezogenen Ortsvektoren feststehenn oder sich geändert haben.
    
    P0, PX und PXY werden über flex.VariableDeMoPe persistiert. Das bedeutet, 
    dass der Ctor diese liest und dann ein .execute() ausführt. Diese Parameter 
    zu speichern, hat den Vorteil, dass sie in Teaching Wizards als Default-Werte 
    verwendet werden können (s. Projekt CRUISER).
    """
    
    def __init__( self):
        self.__wT = T3D.FromEuler( *( 0,)*6)
        self.__wT_last = T3D.FromEuler( *( 0,)*6)

        fv = self._fv_wX_org_teached = flex.VariableDeMoPe( id="baseframe.wX_org_teached", value=0.0, value_min=None, value_max=None, label="Xorg teached", dim="m", dirname="./")
        fv.restore()        
        fv = self._fv_wY_org_teached = flex.VariableDeMoPe( id="baseframe.wY_org_teached", value=0.0, value_min=None, value_max=None, label="Yorg teached", dim="m", dirname="./")
        fv.restore()

        fv = self._fv_wX_x_teached = flex.VariableDeMoPe( id="baseframe.fv_wX_x_teached", value=0.0, value_min=None, value_max=None, label="Xx teached", dim="m", dirname="./")
        fv.restore()
        fv = self._fv_wY_x_teached = flex.VariableDeMoPe( id="baseframe.fv_wY_x_teached", value=0.0, value_min=None, value_max=None, label="Yx teached", dim="m", dirname="./")
        fv.restore()

        fv = self._fv_wX_xy_teached = flex.VariableDeMoPe( id="baseframe.fv_wX_xy_teached", value=0.0, value_min=None, value_max=None, label="Xxy teached", dim="m", dirname="./")
        fv.restore()
        fv = self._fv_wY_xy_teached = flex.VariableDeMoPe( id="baseframe.fv_wY_xy_teached", value=0.0, value_min=None, value_max=None, label="Yxy teached", dim="m", dirname="./")        
        fv.restore()
        
        try:
            self.execute()
        
        except ZeroDivisionError:
            pass

        return
    
    def execute( self):
        """Berechnungen durchführen.
        
        Erst wenn diese Methode ausgeführt worden ist, ist die neue Base berechnet 
        und übernommen! Ein anschließendes .restore_last_known_good() macht's 
        wieder rückgängig.
        """
        self.__wT_last << self.__wT
                                        # Aktuellen Frame als zuletzt gültigen sichern.
        P0 = Vector3( self._fv_wX_org_teached.value(), self._fv_wY_org_teached.value())
                                        # Ursprung
        PX = Vector3( self._fv_wX_x_teached.value(), self._fv_wY_x_teached.value())
                                        # Punkt auf der X-Achse
        PXY = Vector3( self._fv_wX_xy_teached.value(), self._fv_wY_xy_teached.value())
                                        # Punkt in pos. XY-Ebene
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
                                        # Frame
        self.__wT << T
                                        # Frame übernehmen
        return
    
    def fv_wX_org_teached( self):
        """X-Koordinate von P0.
        """
        return self._fv_wX_org_teached
    
    def fv_wY_org_teached( self):
        """Y-Koordinate von P0.
        """
        return self._fv_wY_org_teached

    def fv_wX_x_teached( self):
        """X-Koordinate von PX.
        """
        return self._fv_wX_x_teached
    
    def fv_wY_x_teached( self):
        """Y-Koordinate von PX.
        """
        return self._fv_wY_x_teached
    
    def fv_wX_xy_teached( self):
        """X-Koordinate von PXY.
        """
        return self._fv_wX_xy_teached
    
    def fv_wY_xy_teached( self):
        """Y-Koordinate von PXY.
        """
        return self._fv_wY_xy_teached

    def restore_last_known_good( self):
        self.__wT << self.__wT_last
        return
    
    def wT( self):
        """Base Frame.
        """
        return self.__wT


################################################################################
### Datasheets
#
class _Datasheet:
    
    def __init__( self):
        return
    
    
class Datasheet4SharpGP2D12(_Datasheet):

    def alert_distance_mm( self):
        pass



    def distance_max( self):
        return 0.8
    
    def info_distance_mm( self):
        pass

    def m_per_volt( self):
        return 0.400

    def warnig_distance_mm( self):
        pass


################################################################################
### Electrical Interfaces
#
class _ElectricalInterfaceAnalog:
    
    def __init__( self, dout_enable, dout_trigger, ainp_volts):
        self.__dout_enable = dout_enable
        self.__dout_trigger = dout_trigger
        self.__ainp_volts = ainp_volts
        return
    
    def dout_enable( self):
        return self.__dout_enable
    
    def dout_trigger( self):
        return self.__dout_trigger
    
    def ainp_volts( self):
        return self.__ainp_volts
    
    
class ELIF4SharpInfraredSensor(_ElectricalInterfaceAnalog):

    """Elektrisches Interface.
    
    .. note::
        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
    """

    def __init__( self, ainp_volts):
        super().__init__( None, None, ainp_volts)
        return
    
    def enable( self):
        pass

    def execute( self):
        """Elektrisches Interface ausführen.

        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
        """
        pass

    def mvolts( self):
        return self.volts() * 1000

    def reg_tau4s_on_ready( self, tau4s):
        pass

    def volts( self):
        """Spannung am Analogausgang.

        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
        """
        volts = self.ainp_volts().fv_raw().value()
        return volts
    


################################################################################
### Sensors
#
class Sensor3(abc.ABC):

    """ABC für alle Sensoren.
    
    :param  id:
        Eindeutige Id.
        
    Ersetzt Sensor2.
    """
    def __init__( self, id, specs_io, specs_data, rT):
        self.__tau4p_on_modified = PublisherChannel.Synch( self)
        
        self.__id = id if id not in ("", None, -1) else "%s, created on %s" % (self.__class__.__name__, datetime.datetime.now())
        self.__specs_io = specs_io
        self.__spec_data = specs_data
        self.__rT = rT
        return

    @abc.abstractmethod
    def execute( self):
        """Trigger an Sensor, Sensor lesen, Wert speichern, Filter ausführen, Wert speichern.
        """
        pass

    @abc.abstractmethod
    def fv_default( self):
        """Varbl für Anzeigezwecke und dgl.
        """
        pass
    
    def id( self):
        return self.__id
    
    @abc.abstractmethod
    def read( self):
        """Lesen, was auch immer.
        """
        pass
    
    def reg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified += tau4s
        return self

    @abc.abstractmethod
    def reset( self):
        pass
    
    def rPm( self):
        """Position der Messung relativ zum Rack, auf dem der Sensor montiert ist.
        """
        return self.rTm()._P_()
    
    def rT( self):
        """Lage relativ {R} (Rack).
        """
        return self.__rT
    
    @abc.abstractmethod
    def rTm( self):
        """Frame of the measurement relative to the rack, the sensor is mounted on.
        """
        pass
    
    def specs_data( self):
        """Datenblatt für Umrechnungen wie Spannung nach Abstand usw.
        """
        return self.__spec_data
    
    @abc.abstractmethod
    def sPm( self):
        """Position der Messung relativ zum Sensor.
        """
        pass
    
    def _tau4p_on_modified_( self):
        return self.__tau4p_on_modified()
    
    def ureg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified -= tau4s
        return self


class Ranger2(Sensor3):
    
    def __init__( self, id, specs_io, specs_data, rT):
        super().__init__( id=id, specs_io=specs_io, specs_data=specs_data, rT=rT)
        
        self.__fv_default = flex.VariableDeClMo( value=0.0, label="Distance", dim="m")
        return
    
    def fv_default( self):
        return self.__fv_default
    
    def rPm( self) : return self.rPo()
    
    def rPo( self):
        """Position des Obstacles relativ Rack.
        """
        return self.rTo()._P_()
    
    def rTm( self) : return self.rTo()

    def rTo( self):
        """The obstacle's frame relative to the rack.
        """
        rTs = self.rT()
                                        # Sensor frame rel. to rack.
        sPo = self.sPo()
                                        # Obstacle position rel. to sensor
        sTo = T3D.FromEuler( 0, sPo.y(), 0)
                                        # Obstacle frame rel. to sensor
        rTo = rTs * sTo
        return rTo
    
    def sPm( self) : return self.sPo()
    
    @abc.abstractmethod
    def sPo( self):
        """Position des Obstacles relativ Sensor.
        """
        pass


class IRS(Ranger2):
    
    def __init__( self, id, specs_io, specs_data, rT):
        super().__init__( id=id, specs_io=specs_io, specs_data=specs_data, rT=rT)
        return
    
    def execute( self):
        """Read the voltage by using the specs_io.
        """
        return
    
    def read( self):
        return
    
    def reset( self):
        return
    
    def sPo( self):
        """Position des Obstacles relativ Sensor.
        
        Die Position wird rel. rT angenommen!
        """
        ### Sensorspannung lesen
        #
        voltage = 42
        
        ### Sensorspannung umrechnen in Obstacle Distance
        #
        distance = self.specs_data().distance( voltage)
        
        ### Obstacle Distance speichern für Anzeige
        #
        self.fv_default().value( distance)        
        
        ### Obstacle Distance umrechnen in Vector3
        #
        sPo = Vector3( 0, distance, 0)
        
        return sPo
    
        
class IRSDummy(IRS):
    
    """IRS to be tested w/o a real sensor.
    """
    
    def __init__( self, id, specs_io, specs_data, rT):
        super().__init__( id=id, specs_io=specs_io, specs_data=specs_data, rT=rT)
        
        self.__distance = 0
        return
    
    def execute( self):
        ### Read the sensor's voltage
        #
        voltage = 42
    
        ### Transform the voltage into an obstacle distance
        #
        self.__distance = self.specs_data().distance( voltage)
    
        ### Store the obstacle distance (for display purposes)
        #
        self.fv_default().value( self.__distance)        

        return
    
    def sPo( self):
        """Position des Obstacles relativ Sensor.
        
        Die Position wird rel. rT angenommen!
        """
        ### Obstacle Distance umrechnen in Vector3
        #
        sPo = Vector3( 0, self.__distance, 0)
        
        return sPo
    
    def _distance_( self, arg):
        """Overwrite the measured distance for testing purposes.
        """
        self.__distance = arg
        return self
    

class SensorSpec:

    pass


class SensorSpecData(SensorSpec):

    pass


class SensorSpecDataIRS(SensorSpecData):

    def __init__( self, meters_per_volts):
        self.__meters_per_volts = meters_per_volts
        return
    
    def distance( self, volts):
        return volts * self.__meters_per_volts

    
class SensorSpecDataUSS(SensorSpecData):

    pass


class SensorSpecIO(SensorSpec):
    
    """Elektrisches Interface.
    
    .. note::
        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
    """

    def __init__( self, ainp_volts):
        self.__ainp_volts = ainp_volts
        return
    
    def ainp_volts( self):
        return self.__ainp_volts
    
    def enable( self):
        pass

    def execute( self):
        """Elektrisches Interface ausführen.

        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
        """
        pass

    def mvolts( self):
        return self.volts() * 1000

    def reg_tau4s_on_ready( self, tau4s):
        pass

    def volts( self):
        """Spannung am Analogausgang.

        Das ELIF arbeitet auf die I/Os. D.h. dass nur Variable gelesen und 
        geschrieben werden, das execute() übernimmt HAL4IOs()!
        """
        volts = self.ainp_volts().fv_raw().value()
        return volts
    
    
class Sensors2(metaclass=Singleton):

    @staticmethod
    def rAlpha( sensors):
        """Calculate the angle of the resultant rPo.
        
        This simple algo allows us to check for obstacles. The size of the angle 
        in absence of an obstacle depends on the transforms you defined in your 
        app. If you defined the transforms so that the y-axis points ito the 
        sensing direction, the angle must equal t0 90° in absensce of any obstacle. 
        In that case the angle is less than 90° if an obstacle approaches from the 
        left hand side and it is greater than 90° if it approaches from the right 
        hand side.
        """
        P = Vector3()
        for sensor in sensors:
            rPo = sensor.rTo().P()
            P += rPo
            
        alpha = atan2( P.y(), P.x())            
        return alpha
    
    
    def __init__( self):
        self.__sensors = []
        self.__sensors_by_sensorid = {}
        self.__sensors_by_groupid = {}
        return
    
    def __call__( self, *, id_group=None, id_sensor=None):
        if id_group:
            return self.__sensors_by_groupid[ id_group]
        
        if id_sensor:
            return self.__sensors_by_sensorid[ id_sensor]
        
        return self.__sensors
    
    def __iter__( self):
        return iter( self.__sensors)
    
    def __len__( self):
        return len( self.__sensors)
    
    def add_group( self, id_group):
        if id_group in self.__sensors_by_groupid:
            raise ValueError( "Group '%s' exists already!" % id_group)
        
        self.__sensors_by_groupid[ id_group] = []
        return self
    
    def add_sensor( self, id_group, sensor):
        if not id_group in self.__sensors_by_groupid:
            raise ValueError( "Unknown group id '%s'!" % id_group)
        
        if sensor.id() in self.__sensors_by_sensorid:
            raise ValueError( "Id '%s' not unique among all sensors!" % sensor.id())

        self.__sensors.append( sensor)
        self.__sensors_by_groupid[ id_group].append( sensor)
        self.__sensors_by_sensorid[ sensor.id()] = sensor
        return self
    
    def count( self):
        return len( self.__sensors)
    
    def execute( self):
        for sensor in self.__sensors:
            sensor.execute()
            
        return self

    def sensor( self, id_sensor):
        return self.__sensors_by_sensorid[ id_sensor]
    
    
class USS(Ranger2):
    
    """Ultraschallsensor.
    
    ACHTUNG:
        Das Ausführen von USSen kann einige 10 ms dauern!
    """
    
    def __init__( self, id, specs_io, specs_data, rT):
        super().__init__( id=id, specs_io=specs_io, specs_data=specs_data, rT=rT)
        return
    
    def execute( self):
        """
        
        ACHTUNG:
            Das Ausführen von USSen kann einige 10 ms dauern!
        """
        return
    
    def read( self):
        return
    
    def reset( self):
        return
    
    def sPo( self):
        """Position des Obstacles relativ Sensor.
        
        Die Position wird rel. rT angenommen!
        """
        ### Sensorspannung lesen
        #
        
        ### Sensorspannung umrechnen in Obstacle Distance
        #
        distance = 42
                                        # 2DO: wie geht man mit enem SRF04 um?
        
        ### Obstacle Distance umrechnen in Vector3
        #
        sPo = Vector3( 0, distance, 0)
        
        return sPo
    
        
################################################################################
### Lokalisierung
#
class BaseTeachable:
    
    """Eine Base relativ irgendeiner anderen Base, wbei die Base geteacht werden kann.
    
    2DO:
        Refactoring: Base Class erzeugen.
    """
    
    def __init__( self):
        ### Das CS
        #
        self.__xTb = T3D.FromEuler()
                                        # Transformation der Base relativ 
                                        #   igendwas (deswegen das 'x').
        self.__xTb_inverted = self.__xTb.inverted()
                                        # Die Inversion davon.
        self.__xTb_last = T3D.FromEuler()
                                        # Last known good
        ### Die Vektoren der Positionen, die geteacht werden. Sie müssen dann in 
        #   die Varbls umgerechnet werden (s. close()).
        #
        self.__p_org = Vector3()
        self.__p_x = Vector3()
        self.__p_xy = Vector3()

        ### Flex.Varbls, die die geteachten Werte persistent speichern können und 
        #   auch der Anzeige der Base dienen. Sie werden aus den 3 geteachten 
        #   Vektoren berechnet.
        #
        fv = self._fv_wX_org_teached = flex.VariableDeMoPe( id="baseframe.fv_wX_org_teached", value=0.0, value_min=None, value_max=None, label="Xorg teached", dim="m", dirname="./")
        fv.restore()        
        fv = self._fv_wY_org_teached = flex.VariableDeMoPe( id="baseframe.fv_wY_org_teached", value=0.0, value_min=None, value_max=None, label="Yorg teached", dim="m", dirname="./")
        fv.restore()

        fv = self._fv_wX_x_teached = flex.VariableDeMoPe( id="baseframe.fv_wX_x_teached", value=0.0, value_min=None, value_max=None, label="Xx teached", dim="m", dirname="./")
        fv.restore()
        fv = self._fv_wY_x_teached = flex.VariableDeMoPe( id="baseframe.fv_wY_x_teached", value=0.0, value_min=None, value_max=None, label="Yx teached", dim="m", dirname="./")
        fv.restore()

        fv = self._fv_wX_xy_teached = flex.VariableDeMoPe( id="baseframe.fv_wX_xy_teached", value=0.0, value_min=None, value_max=None, label="Xxy teached", dim="m", dirname="./")
        fv.restore()
        fv = self._fv_wY_xy_teached = flex.VariableDeMoPe( id="baseframe.fv_wY_xy_teached", value=0.0, value_min=None, value_max=None, label="Yxy teached", dim="m", dirname="./")        
        fv.restore()
        
        ### Gemüse
        #
        self.__is_open_for_teaching = False

        ### Nun laden wir die Flex.Varbls in die Vektoren und berechnen den 
        #   Frame xTb durch Ausführen von close().
        #
        self.__p_org << Vector3( self._fv_wX_org_teached.value(), self._fv_wY_org_teached.value(), 0)
        self.__p_x << Vector3( self._fv_wX_x_teached.value(), self._fv_wY_x_teached.value(), 0)
        self.__p_xy << Vector3( self._fv_wX_xy_teached.value(), self._fv_wY_xy_teached.value(), 0)

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
    
    def bP( self, xP: Vector3) -> Vector3:
        """Transformiert eine Position in die Base.
        
        Die Originalposition muss natürlich aus dem gleichen CS X kommen, in dem 
        sich diese Base befindet.
        """
        assert not self.__is_open_for_teaching

        xT = T3D( R3D.FromEuler(), xP)
        bT = self.__xTb_inverted * xT
        return bT._P_()
    
    def close( self, cancel=False): # Raises ZeroDivisionError
        """Effektive Berechnung der Transformation und Speicherung aller Werte, die fürs Restore und die Anzeige gebraucht werden.
        """
        assert self.__is_open_for_teaching
        
        if cancel == False:
            self.__xTb_last << self.__xTb
                                           # Aktuellen Frame als zuletzt gültigen sichern.
            
            ### Vektoren in die Flex.Varbls schreiben für ANzeige und Speicherung
            #
            x, y, z = self.__p_org.xyz()
                                            # Position der {B} in {W}
            self._fv_wX_org_teached.value( x).store()
            self._fv_wY_org_teached.value( y).store()
            
            x, y, z = self.__p_x.xyz()
            self._fv_wX_x_teached.value( x).store()
            self._fv_wY_x_teached.value( y).store()
    
            x, y, z = self.__p_xy.xyz()
            self._fv_wX_xy_teached.value( x).store()
            self._fv_wY_xy_teached.value( y).store()
    
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
                
                self.__xTb << T
                self.__xTb_inverted = self.__xTb.inverted()
                
                self.__is_open_for_teaching = False
                
            except ZeroDivisionError as e:
                UsrEventLog().log_error( "'%s'. " % e, ThisName( self))
                raise e
            
        else:
            self.__is_open_for_teaching = False
        
        return self

    def fv_wX_org_teached( self):
        """X-Koordinate von P0.
        """
        return self._fv_wX_org_teached
    
    def fv_wY_org_teached( self):
        """Y-Koordinate von P0.
        """
        return self._fv_wY_org_teached

    def fv_wX_x_teached( self):
        """X-Koordinate von PX.
        """
        return self._fv_wX_x_teached
    
    def fv_wY_x_teached( self):
        """Y-Koordinate von PX.
        """
        return self._fv_wY_x_teached
    
    def fv_wX_xy_teached( self):
        """X-Koordinate von PXY.
        """
        return self._fv_wX_xy_teached
    
    def fv_wY_xy_teached( self):
        """Y-Koordinate von PXY.
        """
        return self._fv_wY_xy_teached

    def is_open( self):
        return self.__is_open_for_teaching
    
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

        self.__p_org << Vector3( x, y, z)
        return self
    
    def p_org( self):
        """Porg relativ {X}.
        
        Könnte man auch als xPorg() bezeichnen.
        """
        return self.__p_org
    
    def restore_last_known_good( self):
        self.__xTb << self.__xTb_last
        return
        
    def x( self, x, y, z):
        """Teach Point: Position auf der x-Achse relativ X.
        """
        assert self.__is_open_for_teaching

        self.__p_x << Vector3( x, y, z)
        return self

    def xT( self) -> T3D:
        return self.__xTb
        
    def xy( self, x, y, z):
        """Teach Point: Position in der positiven xy-Ebene relativ X.
        """
        assert self.__is_open_for_teaching

        self.__p_xy << Vector3( x, y, z)
        return self

    
class _Bases:
    
    """Alle Bases, die der Locator kennt.
    """
    
    def __init__( self):
        self.__wB = BaseTeachable()
        return
    
    def wB( self):
        """DIE Base relativ World.
        """
        return self.__wB
    

class Locator(metaclass=Singleton):
    
    """Container für alle Bases.
    """
    
    def __init__( self):
        self.__bases = _Bases()
        return
    
    def bases( self):
        return self.__bases
    

    

