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
import os
import socket

### TAU4
#
from tau4 import ThisName
from tau4.automation.sm import SM, SMState
from tau4.data import flex
from tau4.datalogging import SysEventLog, UsrEventLog
from tau4.mathe.linalg import T3D, Vector3
#from tau4.sensors import Locator, GPSStatus, Sensor3
from tau4.sensors import Locator, Sensor3
from tau4.sweng import PublisherChannel, Singleton


class EmlidReachSettings(metaclass=Singleton):
    
    def __init__( self):
        self.__fv_ip_addr = flex.VariableDeMoPe( id="emlid.reach.ip_addr", value="192.168.42.1", label="EMLID Reach IP Addr", dim="", dirname="./")
        flex.Variable.Store( self.__fv_ip_addr.id(), self.__fv_ip_addr)
                                        # Im Objektspeicher speichern
        self.restore()
        return
    
    def ip_addr( self, arg=None):
        if arg is None:
            return self.__fv_ip_addr.value()
        
        self.__fv_ip_addr.value( arg)
        return self
    
    def ip_portnbr( self):
        return 1962
    
    def restore( self):
        self.__fv_ip_addr.restore()
        return self
    
    def socket_timeout( self):
        return 5
   
    def store( self):
        self.__fv_ip_addr.store()
        return
    
    
class EmlidReachFinder:
    
    def __init__( self):
        return
    
    def socket( self, ip_addr, ip_portnbr):
        success = False
        handle = os.popen( "ping -c 1 -W 1 " + ip_addr)
        lines = handle.readlines()
        for j, line in enumerate( lines):
            if line.find( "1 packets transmitted, 1 received, 0% packet loss") >= 0:
                success = True

        handle.close()

        if success:
            sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout( EmlidReachSettings().socket_timeout())
            try:
                print( "Try to conect to '(%s, %d)'. " % (ip_addr, ip_portnbr))
                sock.connect( (ip_addr, ip_portnbr))
                print( "####### S u c c e s s ,   w e   a r e   c o n n e c t e d   to (%s, %s). socket.getpeername() == %s. ########" % (ip_addr, ip_portnbr, sock.getpeername()))
                return sock
                
            except (ConnectionRefusedError, OSError) as e:
                print( "ERROR: '%s' (ip_addr = '%s', ip_portnbr = '%d')!" % (e, ip_addr, ip_portnbr))
                return None
        
        return None

            
class EmlidReachGPS(Sensor3):
    
    """DGPS Reach by EMLID.
    
    :param  id:
        Unique Id.
        
    :param  ip_addr:
        IP-address as e.g. 10.0.0.239.
        
    :param  ip_portnbr:
        Port-number as e.g. 1962.
        
    :param  rT:
        Frame (transform or pose) of the sensor reletive to {R}, i.e. a rack or 
        robot.
        
    This sensor is a TCP client. IP address and port has to be supplied upon 
    instantiation.
    
    If the connection to the TCP server failes, the EmlidReachFider is used to 
    find the server.
    """
    
    ############################################################################    
    #   P U B L I C   I N T E R F A C E        
    ###
    def __init__( self, *, id, ip_addr: str, ip_portnbr: int, rT):
        super().__init__( id=id, specs_io=None, specs_data=None, rT=rT)
        
        self.__socket = None
        self.__is_open = False
        
        self.__fv_default = flex.VariableDeClMo( value=0.0, label="Distance from wPorg", dim="m")
        
#        _SMStates._Common()._fv_ip_addr.value( ip_addr).store()
#        _SMStates._Common()._fv_ip_portnbr.value( ip_portnbr).store()
        _SMStates.GPSConnectedAndReceiving()._tau4p_on_data += self._tau4s_on_data_
        self.__sm = SM(\
            {\
                _SMStates.GPSIdle(): \
                    { \
                        lambda: True: _SMStates.GPSConnecting(),
                    },
                    
                _SMStates.GPSConnecting(): \
                    { \
                        _SMStates.GPSConnecting().is_connected: _SMStates.GPSConnectedAndReceiving(),
                        _SMStates.GPSConnecting().is_error: _SMStates.GPSFinding(),
                    },
                
                _SMStates.GPSFinding(): \
                    { \
                        _SMStates.GPSFinding().is_found: _SMStates.GPSConnecting(),
                        _SMStates.GPSFinding().is_error: _SMStates.GPSError(),
                    },
                
                _SMStates.GPSConnectedAndReceiving(): \
                    { \
                        _SMStates.GPSConnectedAndReceiving().is_disconnected: _SMStates.GPSConnecting(),
                    },
                    
                _SMStates.GPSError(): \
                    { lambda: True: _SMStates.GPSIdle()},
            },
            _SMStates.GPSIdle(),
            _SMStates._Common()
        )
        return

    def execute( self): # Daten einlesen und für Abruf bereithalten
        """Daten einlesen und für Abruf bereithalten.
        """
        self.__sm.execute()
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
        
        Diese Messung kann bedeuten:
        -   Die Entfernung eines Hinderisses bei einem Ranger.
        -   Die Position eines GPS-Devices.
        """
        return self.rT()._P_()
    
    def rTm( self):
        """Frame of a measuremet relative to the rack or robot the sensor is mounted on.
        
        This measurement may mean:
        -   The distance of an obstacle if the sensor is a ranger.
        -   The pose of a GPS device.
        """
        return self.rT()
    
    def satellite_count( self):
        return _SMStates._Common()._satellite_count
    
    def _sm_( self):
        return self.__sm
    
    def sm( self):
        return self.__sm
    
    def sPm( self):
        """Position einer Messung bezüglich des Sensors.
        
        Diese Messung kann bedeuten:
        -   Die Entfernung eines Hinderisses bei einem Ranger.
        -   Die Position eines GPS-Devices.
        """
        return self.wP()

    def statename( self):
        return self.__sm.smstate_current().__class__.__name__
    
    def status( self):
        return _SMStates._Common()._fv_status
    
    def _tau4s_on_data_( self, tau4pc):
        self._tau4p_on_modified_()
        return
    
    def wP( self):
        """Aktuelle Position relativ {W}.
        """
        return _SMStates._Common()._wP

    pass
    ############################################################################    
    #   P R O T E C T E D   I N T E R F A C E
    ###
    

class GPSStatus(flex.VariableDeClMo):

    """Folgende Status sind möglich: NOK (= 0), O (= 1).    
    """
    
    def __init__( self, value=0):
        super().__init__( value=int( value), label="GPS Status", dim="", value_min=0, value_max=1)

        return
    
    def __int__( self):
        return self.value()
    
    def __str__( self):
        return ("NOK", "OK")[ int( self.value())]
    
    def is_nok( self):
        return int( self) == 0

    def is_ok( self):
        return int( self) == 1

    def to_nok( self):
        self.value( 0)
        return self

    def to_ok( self):
        self.value( 1)
        return self


class Receiver:
    
    """ Übernimmt das Empfangen und Verarbeiten der Daten.
    """
    
    def __init__( self):
        self.__datastr = b""
        self.__buffersize = 64
        return
    
    def data( self, socket):
        #buffersize_multiplier = 3
        buffersize_multiplier = 2
        data = socket.recv( self.__buffersize*buffersize_multiplier)
                                        # Wir holen mehr Daten, als die Message 
                                        #   lang ist, um kein altes Zeug 
                                        #   weiterzuverarbeiten
        self.__datastr += data
        while not b"\n" in self.__datastr:
            data = socket.recv( self.__buffersize*buffersize_multiplier)
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


class _SMStates:
    
    class _Common(metaclass=Singleton):
        
        def __init__( self):
            self._fv_is_error = flex.VariableDeMo( id="emlid.reach.is_error", value=0, label="Error", dim="")
                                            # 2DO: Have to merge this with the GPSStatus somehow.
            self._is_open = False
            
            self._is_sensor_state_ok = False
            
            self._socket = None
            
            self._receiver = Receiver()
                                           # Receive and process data.
            self._wP = Vector3()
            
            self._fv_status = GPSStatus()
            
            self._satellite_count = 0
            
            self._time_connection_lost = 0
            self._time_connection_stable = 0
            return
        
        def wP( self):
            return self._wP
        
    
    class _SMState(SMState):
        
        def __init__( self):
            super().__init__()
            return
        
        def common( self):
            common = super().common()
            assert isinstance( common, _SMStates._Common)
            return common
        
        def _ipaddr_increment_( self, ip_addr):
            ipaddr_tuple = self._ipaddr_to_tuple_( ip_addr)
            ipaddr_tuple[ -1] = (ipaddr_tuple[ -1] + 1) % 256
            ipaddr = self._tuple_to_ipaddr_( ipaddr_tuple)
            return ipaddr
        
        def _ipaddr_to_tuple_( self, ip_addr):
            return list( map( int, ip_addr.split( ".")))
        
        def status( self):
            return self.common()._fv_status
    
        def time_connection_found( self):
            return self.common()._time_connection_found
        
        def time_connection_lost( self):
            return self.common()._time_connection_lost
        
        def _tuple_to_ipaddr_( self, tuple):
            return ".".join( map( str, tuple))
        
        def wP( self):
            return self.common()._wP
        
    
    class GPSConnectedAndReceiving(_SMState):
        
        """We are conected and receiving.
        
        Payload:
            Receive data and store them, so that they can be retrieved by a 
            call to _SMStates._Common().wP()
        """
        
        def __init__( self):
            super().__init__()
            
            self._tau4p_on_data = PublisherChannel.Synch( self)
            return
                
        def execute( self):
            try:
                ### Daten im Format LLA lesen (heißt LLH bei Emlid)
                #
                data = self.common()._receiver.data( self.common()._socket)
                
                if data:
                    gps_week, time_of_week, lat, lon, h, quality_flag, satellite_count, *dont_care = map( float, data.strip().split())
        
                    ### Daten in (X, Y) umrechnen
                    #
                    wX, wY = Utils.LL2XY( lat, lon)

                    ### Daten nach {W} transformieren
                    #
                    self.common()._wP << Vector3( wX, wY, h)
                    
                    ### Weitere Daten speichern für Anzeige
                    #
                    self.__satellite_count = satellite_count
                    
                    self.status().to_ok()
                    
                    self._tau4p_on_data()
                    
                else:
                    self.status().to_nok()
                    UsrEventLog().log_error( "Didn't receive data, close socket now!", ThisName( self))
                    self._close_()
                
            except ConnectionResetError as e:
                self.status().to_nok()
                UsrEventLog().log_error( "Lost connection to navi: ConnectionResetError '%s'!" % e, ThisName( self))
        
            except socket.timeout as e:
                self.status().to_nok()
                UsrEventLog().log_error( "Lost connection to navi: '%s'!" % e, ThisName( self))

            return
        
        def is_disconnected( self):
            return self.status().is_nok()
    
    
    class GPSConnecting(_SMState):
        
        """Nimmt die Verbindungsdaten aus einer flex.Varbl und versucht damit eine Verbindung zum Device herzustellen.
        """
    
        def close( self):
            super().close()
            return
        
        def execute( self):
            if not self.common()._socket:
                try:
                    self.common()._socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
                    self.common()._socket.settimeout( EmlidReachSettings().socket_timeout())
                    self.common()._socket.connect( (EmlidReachSettings().ip_addr(), EmlidReachSettings().ip_portnbr()))
                    self.common()._receiver.data( self.common()._socket)
                                                    # Okay, we are connected, but can we receive?
                    EmlidReachSettings().store()
                    self.common()._is_open = True
                    
                except socket.timeout as e:
                    UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                    self.common()._fv_is_error.value( 1)
                    
                except ConnectionRefusedError as e:
                    UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                    self.common()._fv_is_error.value( 1)
                    
                except OSError as e:
                    UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                    self.common()._fv_is_error.value( 1)
                                            
            else:
                self.common()._is_open = True
                EmlidReachSettings().store()
                
            return self
        
        def is_connected( self):
            is_connected = self.common()._socket is not None and self.common()._is_open
            if is_connected:
                UsrEventLog().log_info( "Connection to navi successful.", ThisName( self))
                
            return is_connected
    
        def is_error( self):
            return self.common()._fv_is_error.value() != 0
    
        def open( self, sm):
            super().open( sm)
            self._is_error = False
            self._is_open = False
            return
        
    
    class GPSError(_SMState):
        
        def execute( self):
            return
        
        def is_ackned( self):
            return True  
    

    class GPSIdle(_SMState):
        
        def execute( self):
            return
        
        def is_enabled( self):
            return True
    
    
    class GPSFinding(_SMState):
        
        """Netz nach Devices absuchen.
        """
        
        def __init__( self):
            super().__init__()

            self.__finder = EmlidReachFinder()
            return
        
        def close( self):
            """Close the state.
            
            -   Store the ip address found
            -   Don't reset any data as the next state may need them! If you need 
                data to be rest upon entering this state, do that in open()!
            """
            super().close()

            EmlidReachSettings().store()
            return self
        
        def execute( self):
            ### Connect to te (valid) ip addr and store that ip address
            #
            UsrEventLog().log_info( "IP address tuple = '%s'. " % EmlidReachSettings().ip_addr(), ThisName( self))
            self.common()._socket = self.__finder.socket( EmlidReachSettings().ip_addr(), EmlidReachSettings().ip_portnbr())
                 
            if self.common()._socket is None:
                ### Increment the ip address
                #
                ip_addr_tuple = self._ipaddr_to_tuple_( EmlidReachSettings().ip_addr())
                ip_addr_tuple[ -1] = (ip_addr_tuple[ -1] + 1) % 256
                ip_addr = self._tuple_to_ipaddr_( ip_addr_tuple)
                EmlidReachSettings().ip_addr( ip_addr)
                UsrEventLog().log_info( "Incremented ip address. IP address tuple = '%s'. " % EmlidReachSettings().ip_addr(), ThisName( self))
                
            return
        
        def is_error( self):
            """2DO: Will never happen, which is - okay?
            """
            return self.common()._fv_is_error.value()

        def is_found( self):
            is_found = self.common()._socket is not None
            return is_found
    
        def open( self, sm):
            super().open( sm)
            
            ### Reset the error parameter
            #
            self.common()._fv_is_error.value( 0)            

            ### Make sure that the ip address is valid
            #
            ip_addr_tuple = self._ipaddr_to_tuple_( EmlidReachSettings().ip_addr())
            ip_addr_tuple[ -1] = ip_addr_tuple[ -1] % 256
                        # Just to be sure...
            ip_addr = self._tuple_to_ipaddr_( ip_addr_tuple)
            EmlidReachSettings().ip_addr( ip_addr)

            return


class Utils:

    @staticmethod    
    def LL2XY( lat, lon):
        """(LAT, LON -> (wX, wY).
        """
        y = lat * 111.111 * 1000
        x = 111.111 * cos( radians( lat)) * lon * 1000
        return (x, y)
    