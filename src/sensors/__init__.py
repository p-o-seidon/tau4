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

import gpsd
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
### MBUS-Messages
#
class _MBusMessageSensorData(mbus.Message):

    def __init__( self, sensordata):
        super().__init__()
        
        self.__sensordata = sensordata
        return
    
    def sensordata( self):
        return self.__sensordata
    
    
class _MBusMessageSensorError(mbus.Message):

    def __init__( self, error):
        super().__init__()
        
        self.__error = error
        return
    
    def sensorerror( self):
        return self.__error
    
    

################################################################################
### Sensor Data
#
#class SensorData(metaclass=abc.ABCMeta):
    
    #def __init__( self, id_sensor):
        #self.__id_sensor = id_sensor
        #return

    #@abc.abstractclassmethod    
    #def clone( self):
        #"""Clonen der Senordaten; sollte immer dann gemacht werden, wenn Sensordaten per mbus verschickt werden.
        #"""
        #pass
    
    #def id_sensor( self):
        #return self.__id_sensor
    
    

#class CompassSensorData(SensorData):
    
    #def __init__( self, *, id_sensor, alpha):
        #super().__init__( id_sensor)
        
        #self.__alpha = alpha
        #return
    
    #def alpha( self):
        #return self.__alpha

    #@overrides( SensorData)
    #def clone( self):
        #return self.__class__( \
            #id_sensor=self.id_sensor(), 
            #alpha=self.__alpha
        #)
    

#class NaviSensorData(SensorData):
    
    #def __init__( self, *, id_sensor, count_sats, wX, wY, bX, bY, bA, hdist, hspeed, mapurl):
        #super().__init__( id_sensor)
        
        #self.__count_sats = count_sats
        #self.__wX = wX
        #self.__wY = wY
        #self.__bX = bX
        #self.__bY = bY
        #self.__bA = bA
        #self.__hdist = hdist
        #self.__hspeed = hspeed
        #self.__mapurl = mapurl
        
        #return
    
    #def __lshift__( self, other):
        #self.__count_sats = other.__count_sats
        #self.__wX = other.__wX
        #self.__wY = other.__wY
        #self.__bX = other.__bX
        #self.__bY = other.__bY
        #self.__bA = other.__bA
        #self.__hdist = other.__hdist
        #self.__hspeed = other.__hspeed
        #self.__mapurl = other.__mapurl
        #return self
    
    #@overrides( SensorData)
    #def clone( self):
        #return self.__class__( \
            #id_sensor=self.id_sensor(), 
            #count_sats=self.__count_sats, 
            #wX=self.__wX, 
            #wY=self.__wY, 
            #bX=self.__bX, 
            #bY=self.__bY, 
            #bA=self.__bA,
            #hdist=self.__hdist, 
            #hspeed=self.__hspeed, 
            #mapurl=self.__mapurl
        #)
    
    #def bA( self):
        #return self.__bA
    
    #def bPos( self):
        #return (self.__bX, self.__bY)
    
    
    #def bX( self):
        #return self.__bX
    
    #def bY( self):
        #return self.__bY
    
    #def count_sats( self):
        #return self.__count_sats
    
    #def hdist( self):
        #return self.__hdist
    
    #def hspeed( self):
        #return self.__hspeed
    
    #def mapurl( self):
        #return self.__mapurl
    
    #def wX( self, arg=None):
        #if arg is None:
            #return self.__wX
        
        #self.__wX = arg
        #return self
    
    #def wXY( self):
        #return self.__wX, self.__wY

    #def wY( self, arg=None):
        #if arg is None:
            #return self.__wY
        
        #self.__wY = arg
        #return self


#class RangerSensorData(SensorData):
    
    def __init__( self, *, id_sensor, voltage, distance):
        super().__init__( id_sensor)
        
        self.__voltage = voltage
        self.__distance = distance

        self.__fv_default = flex.VariableDeMo( id=id_sensor, value=float( distance), value_min=0.0, value_max=None, label="???", dim="m")
        return
    
    def clone( self):
        return self.__class__( id_sensor=self.id_sensor(), voltage=self.__voltage, distance=self.__distance)
    
    def distance( self, arg=None):
        """Gemessener Abstand.
        """
        if arg is None:
            return self.__distance
        
        self.__distance = arg
        self.__fv_default.value( arg)
                                        # Abstand ist als Default Value.
        return self

    def voltage( self, arg=None):
        """Gemessene Spannung.
        
        Sie muss vom Sensor aus der Spannung und dem Maßstab aus dem Datasheet
        berechnet werden.
        """
        if arg is None:
            return self.__voltage
        
        self.__voltage = arg
        return self
        


################################################################################
### Sensors
#
#class Sensor(metaclass=abc.ABCMeta):

    #"""Sensor.
    
    #:param  id:     ID des Sensors
    #:param  ifel:   ElectricalInterface4Ranger-Instanz
    #:param  dash:   Datasheet4Ranger-Instanz
    #:param  rTs:    Lage des Sensors auf dem Roboter.
    
    #**Konzept**:
        #Jeder Sensor liest sein/e Messwerte und speichert sie. Das Auslesen der
        #Messwerte über entsprechende Methoden verändert die Messwerte nicht, d.h.
        #dabei wird niemals eine Messung veranlasst.
        
        #Komplexe Sensoren wie ein GPS-Sensor (Navi) verwalten mehr als einen 
        #Messwert. Ale Sensoren müssen daher einen Defaut-Messwert per 
        #fv_default() z.V. stellen.
    #"""

    #def __init__( self, *, id, ifel, dash, rTs):
        #self.__id = id
        #self.__ifel = ifel
        #self.__dash = dash
        #self.__rTs = rTs
        #return
    
    #@abc.abstractmethod
    #def rPo( self):
        #"""Richtungsvektor: Ein Abstandssensor (Ranger) kann einen Richtungsvektor erzeugen, dessen Länge dem gemessenen Wert entspricht, dessen Orientierung jener bezüglich des {ROBOTER} rT.
        
        #Ein Navi retourniert einen Richtungsvektor relativ {BASE}, alles Andere 
        #wäre sinnlos.
        
        #Ein Kompass retourniert einen Richtungsvektor relativ {WORLD} nach dem 
        #Einrichten relativ {BASE}.
        
        #.. note::
            #Ein Auslesen des Richtungsvektors hat keine Messung zur Folge!
        #"""
        #return Vector3( 0, 0)
    
    #def dash( self):
        #"""Datenblatt des Sensors.
        #"""
        #return self.__dash
    
    #@abc.abstractmethod
    #def execute( self):
        #"""Messung ausführen.
        
        #Danach stehen die Messwerte, der Richtungsvektor (dessen Bezugs-Frame 
        #bei jedem Sensor unterschiedlich sein kann!) und der Default-Wert (= der 
        #naheliegendste oder Hauptmesswert bei mehreren Messwerten) zur Verfügung.
        #"""
        #pass
      
    #@abc.abstractclassmethod
    #def fv_default( self):
        #"""Der naheliegendste Wert eines Sensors, wenn er mehr als einen Messwert liefern kann (wie bspw ein Navi).
        
        #Bei einem Ranger wird das der gemessene Abstand sein, bei einem Navi 
        #das Tuple (x, y) (ja, eine FV kann auch Tuples!) usw.
        #"""
        #pass
        
    #def id( self):
        #return self.__id
    
    #def ifel( self):
        #"""Elektrisches Interface.
        #"""
        #return self.__ifel
        
    #def is_available( self):
        #return True
    
    #def rTs( self):
        #"""Lage relativ {ROBOTER}.
        
        #Ist nicht bei allen Sensoren relevant (z.B. beim Compass), bei den 
        #Rangers aber wichtig zur Berechnung der Ausweichrichtung durch den 
        #ObstacleAvoider.
        #"""
        #return self.__rTs

    #@abc.abstractmethod
    #def sensordata( self):
        #"""Datenpaket der Messwerte.
        
        #.. todo::
            #2DO: In die Sensordaten gehört eigentlich auch der Richtungsvektor!
        #"""
        #pass
    

#class TimeRestrictedSensor(Sensor):

    #"""Sensor, der innerhalb einer bestimmten Periode ausgeführt werden muss oder darf.
    #"""
    
    #def __init__( self, *, id, ifel, dash, rTs, cycletime_min, cycletime_max):
        #super().__init__( id=id, ifel=ifel, dash=dash, rTs=rTs)
        
        #self.__cycletime_min = cycletime_min
        #self.__cycletime_max = cycletime_max
        #self.__time = time.time()
        
        #self._tau4p_on_cycletime_exceeded = PublisherChannel.Synch( self)
        #return

    #@overrides( Sensor)    
    #def execute( self):
        #if self._is_time_to_execute_():
            #self._execute_()
                                            ## Downcall            
        #return self

    #@abc.abstractmethod
    #def _execute_( self):
        #pass
    
    #def _is_time_to_execute_( self):
        #if self.__cycletime_min <= time.time() - self.__time:
            #if time.time() - self.__time > self.__cycletime_max:
                #self._tau4p_on_cycletime_exceeded()
                
            #self._execute_()
            #self.__time = time.time()
            
        #return
                
    
#class Compass(Sensor):
    
    #"""Kompass (für mobile Roboter).
    
    #**Usage**::
    
        #from tau4.mathe.linalg import T3D
        #from tau4.robotix.sensors import compasses
        #from tau4.io import i2c
        
        #compass = compasses.HMC5883L( i2c.I2CBus( channelnbr=0))
        #try:
            #alpha = BEIM EINRICHTEN GEMESSENER WINKEL DER SÜD-NORD-RICHTUNG RELATIV ZUR BASIS IN RAD.
            #bTh = T3D.FromEuler( 0, 0, 0, alpha, 0, 0)
            #compass.bTh() << bTh
            #compass.execute()
                                            ## Liest den Compass ein.
            #bTc = compass.bTc()
            #bAlpha = compass.bTc().a()
            
        #except compasses.eCompassNotAvailableError as e:
            #print( str( e))
    #"""
    #def __init__( self, id):
        #super().__init__( id=id, ifel=None, dash=None, rTs=T3D.FromEuler( *(0,)*6))
        
        #self.__bTh = T3D.FromEuler( *(0,)*6)
        #self.__sensordata = CompassSensorData( id_sensor=id, alpha=0)
        #return
    
    #def alpha_deg( self):
        #return degrees ( self.alpha())
    
    #@abc.abstractmethod
    #def alpha( self):
        #"""Reading des Sensors relativ zur Base in RAD.
        #"""
        #pass
    
    #def bAlpha( self):
        #"""Reading des Sensors relativ zur {BASE} in RAD.: (self.bTh() * kTh.inverted()).a() mit kTh = T3D.FromEuler( 0, 0, 0, self.alpha(), 0, 0).
        
        #kTh:
            #Süd-Nord-Richtung im {COMPASS}-Frame. Dessen Alpha ist direkt der vom 
            #Kompass gelieferte Winkel.
            
        #bTh:
            #Süd-Nord-Richtung im {BASE}-Frame. Dessen Winkel muss beim Einrichten 
            #gemessen werden. Dazu richtet man den omass am {BASE}-Frame aus und 
            #liest den vom Kompass angezeigten Winkel ab:
            #mit bTh = T3D.FromEuler( 0, 0, 0, self.alpha(), 0, 0), wenn der Roboter 
            #normal zur X-Achse steht.
        #"""
        #kTh = T3D.FromEuler( 0, 0, 0, self.alpha(), 0, 0)
                                        ## Das hat der Kompass gerade gemessen
        #bTc = self.bTh() * kTh.inverted()
        #bAlpha = bTc.a()
        #return bAlpha
    
    #def bAlpha_deg( self):
        #"""Reading des Sensors relativ zur {BASE} in DEG.
        #"""
        #return degrees( self.bAlpha())
    
    #def bTh( self):
        #"""Frame, der dadurch entsteht, dass er im Ursprung der Base liegt und dort den Winkel alpha mit der Base einschließt.
        #"""
        #return self.__bTh
    
    #@overrides( Sensor)
    #def rPo( self):
        #"""Richtungsvektor relativ {BASE}.
        
        #.. note::
            #Die Ausführung dieser Methode hat keine Messung zur Folge!
            
        #.. todo::
            #2DO:    
                #Der Name dieser Methode ist beim Kompass falsch, müsste 
                #headingvector() heißen!
        #"""
        #a = self.bAlpha()
        #v = Vector3( cos( a), sin( a))
        #return v
    
    #@abc.abstractmethod
    #def execute( self):
        #"""Messung ausführen: Einlesen von self.alpha().
        #"""
        #pass

    #@overrides( Sensor)
    #def fv_default( self):
        #"""Winel relativ {WORLD}.
        #"""
        #return self.__sensordata.alpha()

    #def reset( self):
        #return    

    #@overrides( Sensor)
    #def sensordata( self):
        #return self.__sensordata
    
    
#class CompassI2C(Compass):
    
    #def __init__( self, id, i2c):
        #super().__init__( id)

        #self.__i2c = i2c
        #return
    
    #@overrides( Compass)
    #def alpha( self):
        #return self.__i2c.value()
    
    #def _close_( self):
        #self.__i2c.close()
        #return self
    
    #def execute( self):
        #self._open_()
        
        #### 2DO: Wie liest man einen I2C-Kompass?
        
        #self._close_()
        #return self
    
    #@overrides( Compass)
    #def is_available( self):
        #return False
    
    #def _open_( self):
        #self.__i2c.open()
        #return self
    
    
#class Navi(TimeRestrictedSensor):

    #class MBusMessageNaviData(_MBusMessageSensorData):
        
        #pass

        
    #class MBusMessageNaviError(_MBusMessageSensorError):
        
        #pass
        
    #def __init__( self, *, id, ifel, dash, rTs):
        #super().__init__( id=id, ifel=ifel, dash=dash, rTs=rTs, cycletime_min=5, cycletime_max=7.5)
        
        #self.__base = self.BaseFrame()
        #return

    #def base( self):
        #return self.__base


    #def ll2xy( self, lat, lon):
        #"""(LAT, LON -> (wX, wY).
        #"""
        #y = lat * 111.111 * 1000
        #x = 111.111 * cos( radians( lat)) * lon * 1000
        #return (x, y)
    

#class NavilockNL602U(Navi):
    
    #"""Konkretes Navi.
    
    #Hält eine Instanz der Klasse NaviSensorData, die über enstprechende Mehoden
    #abgefragt werden können. Diese Sensordaten werden aber auch per MBUS versendet. 
    #Clients können sich für den Empfang anmelden per
    #Navi.MBusMessageNaviData.RegisterSubscriber() und 
    #Navi.MBusMessageNaviError.RegisterSubscriber()
    #"""
        
    #def __init__( self, *, id, rTs):
        #super().__init__( id=id, ifel=None, dash=None, rTs=rTs)
        #self.__is_connected = False
        
        #self.__response = None
        
        #self.__sensordata = NaviSensorData( id_sensor=id, count_sats=0, wX=0, wY=0, bX=0, bY=0, bA=0, hdist=0, hspeed=0, mapurl="http://")
        
        #self.__fv_default = flex.VariableDeMo( id="%s.wXY" % id, value=(0.0, 0.0), value_min=None, value_max=None, label="GPS wXY", dim="(m, m)")

        #self.__wA = 0
        #self.__wXY = [ [0, 0], [ 0, 0]]        
        #return

    #def bT( self, *, wTb, wT):
        #"""Navi im Garten.
        #"""
        #return wTb.inverted() * wT
    
    #def connect( self):
        #try:
            #gpsd.connect()
            #self.__is_connected = True
            
        #except ConnectionRefusedError:
            #UsrEventLog().log_error( ThisName( self) + "(): Cannot connect to GPS sensor. ")
        
        #return
    
    #def rPo( self):
        #"""
        
        #.. todo::
            #2DO: 
                #Falscher Name für Navi und Kompass. Sollen wir die Notwendigkeit 
                #dieser Methode wie def't in der Base Class fallen lassen?
        #"""
        #x2, y2 = self.__wXY[ 0]
        #x1, y1 = self.__wXY[ -1]
        #dvec = Vector3( x2 - x1, y2 - y1)
        #return dvec
    
    #def error( self):
        #return self.__error

    #@overrides( TimeRestrictedSensor)
    #def _execute_( self):
        #if not self.__is_connected:
            #self.connect()
            
        #if not self.__is_connected:
            #return
        
        #hdist = self.__sensordata.hdist()
        #try:
                
            #self.__response = gpsd.get_current()
                                            ## Gesamter Response
            #self.__wXY[ 0] = self.wXY()
            #if self.__wXY[ -1] == [0, 0]:
                #self.__wXY[ -1][ :] = self.__wXY[ 0]
                                            ## Jetzige Pos. des Navi rel. WORLD
            ##if self._distance_( *self.__wXY[ 0], *self.__wXY[ -1]) > 5:
            ## ##### Kann erst Python 3.5
            #(x1, y1), (x2, y2) = self.__wXY[ 0], self.__wXY[ -1]
            #if self._distance_( x2, y2, x1, y1) > 5:
                                            ## Wir können einen Vektor zur 
                                            ##   Richtungsbestimmung berechnen.
                                            ##
                                            ## 2DO: Der Wert 5 muss aus dem Datenblatt
                                            ##   des Navis kommen!
                #x2, y2 = self.__wXY[ 0]
                #hdist = sqrt( x2*x2 + y2*y2)
                #x1, y1 = self.__wXY[ -1]
                #dvec = Vector3( x2 - x1, y2 - y1)
                #self.__wA = dvec.a()
                                                ## Winkel alpha rel. WORLD.
            #else:
                                            ## Wir arbeiten mit der zuletzt gültigen Orientierung
                #pass
            
            #wT = T3D.FromEuler( self.__wXY[ 0][ 0], self.__wXY[ 0][ 1], 0, self.__wA, 0, 0)
                                            ## Lage des Navis rel. WORLD.
            #wTb = self.base().wT()
                                            ## Lage der Base (Garten) rel. WORLD
            #bX, bY, bA = self.bT( wTb=wTb, wT=wT).xya()
                                            ## Lage des Navis rel. BASE (Garten)

            #sensordata = NaviSensorData(\
                #id_sensor=self.id(),
                #count_sats=self.count_sats(),
                #wX=self.wXY()[ 0],
                #wY=self.wXY()[ 1],
                #bX=bX,
                #bY=bY,
                #bA=bA,
                #hdist=hdist,
                #hspeed=self.hspeed(),
                #mapurl=self.map_url()
                                            ## URL in OpenStreetMap
                #)

            #self.__sensordata << sensordata
            
            #self.__fv_default.value( self.wXY())

            #message = self.MBusMessageNaviData( sensordata)
            #message.publish()
            
        #except (KeyError, gpsd.NoFixError) as e:
            #self.__error = e
            
        #except IndexError as e:
                                        ## GPS ausgesteckt.
            #self.__error = e

        #return
    
    #def _distance_( self, x2, y2, x1, y1):
        #return sqrt( (x2 - x1)**2 + (y2 - y1)**2)
    
    #def fv_default( self):
        #return self.__fv_default
    
    #def count_sats( self):
        #return self.__response.sats
    
    #def error_margin( self):
        #return self.__response.error
    
    #def hspeed( self):
        #return self.__response.speed()
    
    #def wLL( self):
        #"""(LAT, LON).
        
        #.. note::
            #wLL() ist zwar nicht sinnvoll, weil es ein bLL() oder was auch 
            #immer gar nicht gibt. Aber ll() kann man schlecht lesen. 
        #"""
        #return self.__response.position()

    #def map_url( self):
        #return self.__response.map_url()
    
    #def pos_precision( self):
        #return self.__response.position_precision()
    
    #def posLL( self):
        #"""Deprecated, use wLL()!
        #"""
        #return self.__response.position()
    
    #def wXY( self):
        #return self.ll2xy( *self.posLL())

    ##def wTa( self):
        ##"""Garten in Welt - geteacht.
        ##"""
        ##return self.__wTa
    
    ##def wTn( self):
        ##"""Roboter in Welt - geliefert vom GPS.
        ##"""
        ##return self.__wTn
    
    #@overrides( Sensor)
    #def sensordata( self):
        #return self.__sensordata
    

    
#class GPSStatus(flex.VariableDeClMo):

    #"""Folgende Status sind möglich: NOK (= 0), O (= 1).    
    #"""
    
    #def __init__( self, value=0):
        #super().__init__( value=int( value), label="GPS Status", dim="", value_min=0, value_max=1)

        #return
    
    #def __int__( self):
        #return self.value()
    
    #def __str__( self):
        #return ("NOK", "OK")[ int( self.value())]
    
    #def is_nok( self):
        #return int( self) == 0

    #def is_ok( self):
        #return int( self) == 1

    #def to_nok( self):
        #self.value( 0)
        #return self

    #def to_ok( self):
        #self.value( 1)
        #return self


#class Ranger(Sensor):

    #"""Abstandsmesser.
    
    #:param  id:     ID des Sensors
    #:param  ifel:   ElectricalInterface4Ranger-Instanz
    #:param  dash:   Datasheet4Ranger-Instanz
    #:param  rTs:    Lage des Sensors auf dem Roboter.
    
    #Das Publizieren der Sensordaten kann nicht per MBUS erfolgen, weil es mehr 
    #als einen Ranger gibt. Es erfolgt also über den Publikationsmechanismus der 
    #FV, die den Default-Messwert hält.
    #"""
    
    #def __init__( self, *, id, ifel, dash, rTs):
        #super().__init__( id=id, ifel=ifel, dash=dash, rTs=rTs)
        
        #self.__sensordata = RangerSensorData( id_sensor=id, voltage=0, distance=0)
        #self.__fv_default = flex.VariableDeMo( id="varbls.sensors.%s" % id, value=0.0, label="%s" % id, dim="m")
        #return
        
    #def rPo( self):
        #"""Richtungsvektor des Obstacles relativ {ROBOT}.
        
        #Die Länge gibt die Entfernung zum Hinderis an. In Rangers werden alle 
        #Richtungsvektor zu einer Resultierenden addiert. Ist die Richtung mit 
        #der y-Achse von {ROBOT} identisch, ist ein Hindernis erkannt worden. Weicht 
        #sie ab, dann in die Richtung, in die ausgwichen werden muss.
        #"""
        #d = self.distance()
        #sTo = T3D.FromEuler( d, 0, 0, 0, 0, 0)
                                        ## Der Sensorstrahl läuft entlang der X-Achse.
        #rTo = self.rTs() * sTo
        #rPo = rTo._P_()
        #return rPo
    
    #def rPo_max( self):
        #"""Richtungsvektor des Obstacles an der Detektionsgrenze relativ {ROBOT} = maximale Sichtweite.
        
        #Die Länge gibt die Sichtweite an. In Rangers werden alle 
        #Richtungsvektor zu einer Resultierenden addiert. Ist die Richtung mit 
        #der y-Achse von {ROBOT} identisch, ist ein Hindernis erkannt worden. Weicht 
        #sie ab, dann in die Richtung, in die ausgwichen werden muss.
        #"""
        #d = self.dash().distance_max()
        #sTo = T3D.FromEuler( d, 0, 0, 0, 0, 0)
                                        ## Der Sensorstrahl läuft entlang der X-Achse.
        #rTo = self.rTs() * sTo
        #rPo = rTo._P_()
        #return rPo

    #def distance( self):
        #"""Liefert den Abstand zum Hindernis in m.
        
        #Es wird keine Messung ausgeführt!
        #"""
        #return self.fv_default().value()

    #def distance_max( self):
        #"""Liefert den Abstand zum Hindernis in m, der noch "gesehen" wird vom Sensor.
        
        #Es wird keine Messung ausgeführt!
        #"""
        #return self.dash().distance_max()

    #@overrides( Sensor)
    #def execute( self):
        #"""Ausführen der Messung.
        
        #-   Sensordaten aktualisieren.
        #-   Sensordaten per MBUS publishen.
        
        #Die Messung wird nicht wirklich ausgeführt, weil der Messwert aus dem 
        #I/O-System ausgelesen wird, das seinerseits schon ausgeführt worden ist.
        
        #.. todo::
            #2DO:    Brauchen wir wirklich SensorData?
        #"""
        #self.__sensordata.voltage( self.ifel().volts())
                                        ## 2DO: Braucht's das wirklich?
        #self.__sensordata.distance( self.__sensordata.voltage() * self.dash().m_per_volt())
                                        ## 2DO: Könnten wir hier nicht einfach eine 
                                        ##   Variabble fv_figure einführen?
        #self.fv_default().value( self.__sensordata.distance())
                                        ## 2DO: Umbenennen in fv_figure_default.
        #return
    
    #@overrides( Sensor)
    #def fv_default( self):
        #return self.__fv_default

    #@overrides( Sensor)
    #def sensordata( self):
        #return self.__sensordata
    
    
#class RangerSensorsHeadingVectorBuilder:
    
    #"""Baut den Heading Vector, der die Resultierende ist aus den Vektoren vom Sensor zum Obstacle.
    
    #Die Resultierende ist relativ {ROBOT}.
    
    #Wenn der Winkel ungleich 0 ist, heißt das, dass einer der Seitensenoren 
    #angesprochen hat.
    
    #Wenn die Länge nicht mehr Solllänge hat, heißt das, dass (einer) der Front-Sensor(en) 
    #angesprochen hat.
    
    #Nützen ann die beiden Werte bspw. in Behaviours wie AVOID und ESCAPE.
    #"""
    
    #def __init__( self, sensors):
        #self.__rangers = [ sensor for sensor in sensors if isinstance( sensor, Ranger)]
        #return
    
    #def headingvector( self):
        #rPo = Vector3( 0, 0, 0)
        #for ranger in self.__rangers:
            #rPo += ranger.rPo()
            
        #return rPo
    
    #def headingvector_deviationangle( self, rPm, is_format_deg=False):
        #"""
        
        #:param  rPm:
            #Richtung, in der sich der Roboter relativ {ROBOT} bewegt ('m' steht 
            #für 'movement').
        #"""
        #rPo = self.headingvector()
                                        ## Resultierende aller Obstacles relativ 
                                        ##   {ROBOT}.
        #rAo = atan2( rPo.y(), rPo.x())
        #rAm = atan2( rPm.y(), rPm.x())
        #alpha = rAo - rAm
        #return alpha if not is_format_deg else degrees( alpha)
    
    #def headingvector_deviationmagnitude( self):
        #rPo_max = Vector3( 0, 0, 0)
        #for ranger in self.__rangers:
            #rPo_max += ranger.rPo_max()
            
        #rPo = self.headingvector()
        #deviationmagnitude = rPo_max.mag() - rPo.mag()
        #return deviationmagnitude
    
    
#class RangerSharpGP2D12(Ranger):
    
    #"""Konkreter Sensor: IR-Sensor von Sharp.
    #"""

    #def __init__( self, *, id, ifel, rTs):
        #super().__init__( id=id, ifel=ifel, dash=Datasheet4SharpGP2D12(), rTs=rTs)
        #return
    


#class Weather(Sensor):
    
    #pass


#class Sensors(dict):
    
    #def __init__( self, *args, **kwargs):
        #super().__init__( *args, **kwargs)
    
        #self.__fv_sensorcount = flex.VariableDeMo( id="tau4.sensors.count", value=0, value_min=None, value_max=None, label="# tau4sensors.Sensors", dim=None)
        
        #self.__tau4p_on_directionvector_changed = PublisherChannel.Synch( self)
        
        #self.__compasses = Compasses()
        #self.__navis = Navis()
        #self.__rangers = Rangers()
        #return
    
    #def __call__( self, key):
        #return self[ key]
    
    #def add( self, sensor):
        #if sensor.id() in self:
            #raise KeyError( "Sensor '%s' already added!")
        
        #self[ sensor.id()] = sensor
        #if isinstance( sensor, Ranger):
            #self.__rangers.append( sensor)
            
        #elif isinstance( sensor, (Navi, Navi2)):
            #self.__navis.append( sensor)
        
        #elif isinstance( sensor, Compass):
            #self.__compasses.append( sensor)
        
        #self.__fv_sensorcount.value( len( self)) # 2DO: Und die Rangers?!
        #return self
    
##    def directionvector( self):
##        return self.rangers().directionvector()
    
    #def compass( self):
        #"""Es gibt nur einen Compass.
        #"""
        #return self.compasses( 0)
    
    #def compasses( self, i=None):
        #"""
        
        #Was tun, wenn's mehr als einen Compass gibt?
        #"""
        #if i is None:
            #return self.__compasses
        
        #return self.__compasses[ i]

    #def execute( self):
        #"""
        
        #.. todo::   2DO:
            #Ganzes Sensorwert-Publishing überdenken!
        #"""
        #for sensor in self.values():
            #sensor.execute()
            
        #self.navis().tau4p_on_directionvector_modified()
        #self.rangers().tau4p_on_directionvector_modified()
        #return self
    
    #def fv_sensorcount( self):
        #return self.__fv_sensorcount

    #def gps( self):
        #return self( "GPS")
    
    #def navi( self):
        #"""Es gibt nur ein Navi.
        #"""
        #return self.navis( 0)
    
    #def navis( self, i=None):
        #"""
        
        #Was tun, wenn's mehr als ein Navi gibt?
        #"""
        #if i is None:
            #return self.__navis
        
        #return self.__navis[ 0]

    #def rangers( self):
        #return self.__rangers
    
    #def reg_tau4s_on_directionvector_changed( self, tau4s):
        #self.__tau4p_on_directionvector_changed += tau4s
        #return self


#class Navis(list):

    #def __init__( self):
        #super().__init__()
        
        #self.__tau4p_on_rAlpha_modified = PublisherChannel.Synch( self)

    #def directionvector( self):
        #vec = Vector3( 0, 0)
        #for sensor in self:
            #vec += sensor.directionvector()
            
        #return vec

    #def reg_tau4s_on_rAlpha_modified( self, tau4s):
        #self.__tau4p_on_rAlpha_modified += tau4s
        #return
    
    #def tau4p_on_directionvector_modified( self):
        #self.__tau4p_on_rAlpha_modified()


#class Rangers(list):
    
    #def __init__( self):
        #super().__init__()
        
        #self.__tau4p_on_rAlpha_modified = PublisherChannel.Synch( self)

    #def apend( self, ranger):
        #assert isinstance( ranger, Ranger)
        #return super().append( ranger)
        
    #def rPo( self):
        #"""Headingvektor relativ {ROBOT}: Summe aller Vektoren, die durch die Ranger definiert werden.
        
        #Spricht keiner der Ranger an, dann schließt der Vektor mit der X-Achse 0° ein.
        #"""
        #rPo = Vector3( 0, 0)
        #for sensor in self:
            #rPo += sensor.rPo()
            
        #return rPo
    
    #def execute( self):
        #for r in self:
            #r.execute()
            
        #return

    #def reg_tau4s_on_rAlpha_modified( self, tau4s):
        #self.__tau4p_on_rAlpha_modified += tau4s
        #return
    
    #def tau4p_on_directionvector_modified( self):
        #self.__tau4p_on_rAlpha_modified()


#class Compasses(list):
    
    #def __init__( self):
        #super().__init__()
        
        #self.__tau4p_on_rAlpha_modified = PublisherChannel.Synch( self)

    #def directionvector( self):
        #"""Summe aller Vektoren, die durch die Kompasse definiert werden.
        
        #.. todo::
            #2DO: Abklären, scheint mir wenig sinnvoll zu sein.
        #"""
        #vec = Vector3( 0, 0)
        #for sensor in self:
            #vec += sensor.directionvector()
            
        #return vec

    #def reg_tau4s_on_rAlpha_modified( self, tau4s):
        #self.__tau4p_on_rAlpha_modified += tau4s
        #return
    
    #def tau4p_on_directionvector_modified( self):
        #self.__tau4p_on_rAlpha_modified()

################################################################################
### Sensors2
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
    

    

