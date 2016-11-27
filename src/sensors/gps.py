#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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

### Std-Lub
#
from math import *
import socket

### TAU4
#
from tau4 import ThisName
from tau4.data import flex
from tau4.datalogging import SysEventLog, UsrEventLog
from tau4.mathe.linalg import T3D, Vector3
from tau4.sensors import Locator, NaviStatus, Sensor3


################################################################################
class EmlidReachGPS(Sensor3):
    
    """DGPS Reach von EMLID.
    
    :param  id:
        Eindeutige Id.
        
    :param  ip_addr:
        IP-Adresse wie z.B. 10.0.0.239.
        
    :param  ip_portnbr:
        Port Number wie z.B. 1962.
        
    :param  rT:
        Lage des Sensors relativ z.B. zu einem Rack oder Roboter.
        
    Dieser Sensor ist ein TCP-Client, der sich an eine IP-Address:Port-Kombi hängt, die 
    im mitgeteilt werden muss. In Arbeit ist gerade ein EmidReachFinder, der genau 
    diese Daten liefern kann.
    
    
    """
    
    ############################################################################    
    #   P U B L I C   I N T E R F A C E
    class Receiver:
        
        def __init__( self):
            self.__datastr = b""
            self.__buffersize = 64
            return
        
        def data( self, socket):
            data = socket.recv( self.__buffersize*3)
                                            # Wir holen mehr Daten, als die Mesage 
                                            #   lang ist, um kein altes Zeug 
                                            #   weiterzuverarbeiten
            self.__datastr += data
            while not b"\n" in self.__datastr:
                data = socket.recv( self.__buffersize*3)
                if not data:
                    break
                
                self.__datastr += data
    
            try:
                items = self.__datastr.split( b"\n")
                data = items[ -2]
                                                # Letzter vollständiger Datensatz
                self.__datastr = items[ -1]
                                                # Unvollständiger "Schwanz" des Datensatzes
                buffersize = max( 64, len( data) + 1)
                                                # +1 wegen des '\n'.
                if buffersize != self.__buffersize:
                    UsrEventLog().log_info( "Change buffersize from '%d' to '%d'. " % (self.__buffersize, buffersize), ThisName( self))
                    self.__buffersize = buffersize
                    
                return data
            
            except (IndexError, ValueError) as e:
                UsrEventLog().log_error( "Received data seem to be corrupted or Rover has closed down the socket: '%s'!" % e, ThisName( self))
                                            # Caller muss Socket schließen, sonst 
                                            #   laufen wir hier immer in den Timeout!
                return None        
        
        
    def __init__( self, *, id, ip_addr: str, ip_portnbr: int, rT):
        super().__init__( id=id, specs_io=None, specs_data=None, rT=rT)
        
        self.__ip_addr = ip_addr
        self.__ip_portnbr = ip_portnbr
        
        self.__socket = None
        self.__is_open = False
        
        self.__wP = Vector3()
                                        # (Eigene) Position relativ {W}.
#        self.__fv_default = flex.VariableDeMo( value=self.bP(), label="bP")
# ##### 2016-11-17
        self.__satellite_count = 0
        
        self.__receiver = self.Receiver()
        
        self.__fv_status = NaviStatus()
        
        self.__fv_default = flex.VariableDeClMo( value=0.0, label="Distance from wPorg", dim="m")
        return

# ##### 2016-11-20
#    def base( self):
#        """Der geteachte BaseFrame, weil wir mit dem {W} nichts anfangen können.
#        
#        Unser Navi liefert also nicht nur Koordinaten relativ {W} sondern auch 
#        relativ {B}! Letzteres muss natürlich geteacht worden sein!
#        """
#        return Locator().bases().wB()
# ##### 2016-11-20
    
# ##### 2016-11-17
#    def bP( self): # Eigene, aktuelle Position rel. Locator().bases().wB()
#        """Aktuelle Position relativ {B}.
#        
#        Nur Position, keine Orientierung.
#        """
#        bP = Locator().bases().wB().bPos( self.wP())
#        #                      ^               ^ 
#        #                      |               |
#        #                      |               w
#        #                      |                P...Aktuelle Position relativ 
#        #                      |                    {W} - gemessener Wert,
#        #                      w
#        #                       B...Org der Base relativ {W}
#        return bP
#
# ##### 2016-11-17

# ##### 2016-11-17
#    def bXY( self):
#        return self.bP().xy()
# ##### 2016-11-17
        
    def execute( self): # Daten einlesen und für Abruf bereithalten
        """Daten einlesen und für Abruf bereithalten.
        """
        if not self._is_open_():
            UsrEventLog().log_error( "Socket not open! ", ThisName( self))
            UsrEventLog().log_info( "Try to open socket. ", ThisName( self))
            self._open_()            
            UsrEventLog().log_info( "Socket should be open now. ", ThisName( self))

        if self._is_open_():
            try:
                ### Daten im Format LLA lesen (heißt LLH bei Emlid)
                #
                data = self.__receiver.data( self.__socket)
                
                if data:
                    gps_week, time_of_week, lat, lon, h, quality_flag, satellite_count, *dont_care = map( float, data.strip().split())
        
                    ### Daten in (X, Y) umrechnen
                    #
                    wX, wY = self._ll2xy_( lat, lon)

                    ### Daten nach {W} transformieren
                    #
                    self.__wP << Vector3( wX, wY, h)
                    
                    ### Weitere Daten speichern für Anzeige
                    #
                    self.__satellite_count = satellite_count
                    
                    self.status().to_ok()
                    
                else:
                    self.status().to_nok()
                    UsrEventLog().log_error( "Didn't receive data, close socket now!", ThisName( self))
                    self._close_()
                
            except ConnectionResetError as e:
                self.status().to_nok()
                UsrEventLog().log_error( "'%s'!" % e, ThisName( self))
        
            except socket.timeout as e:
                self.status().to_nok()
                UsrEventLog().log_error( "'%s'!" % e, ThisName( self))

        else:
            self.status().to_nok()
            UsrEventLog().log_error( "Socket is not open!", ThisName( self))
            
        return self

    def fv_default( self):
        """wPorg.
        """
        return self.__fv_default
    
    def read( self):
        return self.bP()
    
    def reset( self):
        pass
    
    def rPm( self):
        """Position einer Messung bezüglich eines Racks (oder Roboters).
        
        Diese Messung ann bedeuten:
        -   Die Entfernung eines Hinderisses bei einem Ranger.
        -   Die Position eines GPS-Devices.
        """
        return self.rT()._P_()
    
    def satellite_count( self):
        return self.__satellite_count
    
    def sensordata( self):
        return NaviSensorDataEmlidReach( sensor=self)

    def sPm( self):
        """Position einer Messung bezüglich des Sensors.
        
        Diese Messung kann bedeuten:
        -   Die Entfernung eines Hinderisses bei einem Ranger.
        -   Die Position eines GPS-Devices.
        """
        return self.wP()

    def status( self):
        return self.__fv_status
    
    def wP( self):
        """Aktuelle Position relativ {W}.
        """
        return self.__wP

    ############################################################################    
    #   P R O T E C T E D   I N T E R F A C E
    def _close_( self):
        self.__socket.close()
        self.__is_open = False
        return self
    
    def _is_open_( self):
        return self.__is_open
    
    def _ll2xy_( self, lat, lon):
        """(LAT, LON -> (wX, wY).
        """
        y = lat * 111.111 * 1000
        x = 111.111 * cos( radians( lat)) * lon * 1000
        return (x, y)

    def _open_( self):
        try:
            self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout( 10)
            self.__socket.connect( (self.__ip_addr, self.__ip_portnbr))
            self.__is_open = True
            
        except socket.timeout as e:
            UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
            
        except ConnectionRefusedError as e:
            UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
            
        return self
    
    