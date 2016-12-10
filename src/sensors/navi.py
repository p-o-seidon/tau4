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

from math import *
import threading

from tau4 import ThisName
from tau4.datalogging import UsrEventLog
from tau4.data import buffers
from tau4.mathe.linalg import T3D, Vector3
from tau4.sensors import Locator, Sensor3
from tau4.sweng import PublisherChannel
from tau4 import threads


class LockedRingbufferStatistix(buffers.RinbufferStatistix):
    
    def __init__( self, elemcount_max, elems=None):
        super().__init__( elemcount_max, elems)
        
        self.__lock = threading.Lock()
        return

    def elem( self, elem=None):
        with self.__lock:
            return super().elem( elem)
        
    def mean( self):
        with self.__lock:
            return super().mean()
    
    def median( self):
        with self.__lock:
            return super().median()
    
    def stddev( self):
        with self.__lock:
            return super().stddev()
        
    def stdev( self):
        with self.__lock:
            return super().stdev()
        
        
class NavSys(Sensor3):
    
    """GPS + Base
    """
    
    @staticmethod
    def LL2XY( lat, lon):
        """(LAT, LON -> (wX, wY).
        """
        y = lat * 111.111 * 1000
        x = 111.111 * cos( radians( lat)) * lon * 1000
        return (x, y)
    
    
    def __init__( self, id, gps):
        super().__init__( id, None, None, gps.rT())
        
        self.__gps = gps
        self.__gps.reg_tau4s_on_modified( lambda tau4pc, self=self: self._tau4p_on_modified_())
        
        self.__statistixbuffer_wX = LockedRingbufferStatistix( 10)
        self.__statistixbuffer_wY = LockedRingbufferStatistix( 10)
        self.__statistixbuffer_bX = LockedRingbufferStatistix( 10)
        self.__statistixbuffer_bY = LockedRingbufferStatistix( 10)
        
        UsrEventLog().log_info( self.__class__.__name__ + " is created. ", ThisName( self))
        return

    ############################################################################
    ### P U B L I C
    def base( self):
        """Der geteachte BaseFrame, weil wir mit dem {W} nichts anfangen können.
        
        Unser Navi liefert also nicht nur Koordinaten relativ {W} sondern auch 
        relativ {B}! Letzteres muss natürlich geteacht worden sein!
        """
        return Locator().bases().wB()
    
    def bP( self):
        bP = Locator().bases().wB().bP( self._gps_().wP())
        #                      ^                    ^ 
        #                      |                    |
        #                      |                    w
        #                      |                     P...Aktuelle Position relativ 
        #                      |                         {W} - gemessener Wert
        #                      w
        #                       B...Org der Base relativ {W}
        return bP
    
    def bXY( self):
        bP = Locator().bases().wB().bP( self._gps_().wP())
        #                      ^                    ^ 
        #                      |                    |
        #                      |                    w
        #                      |                     P...Aktuelle Position relativ 
        #                      |                         {W} - gemessener Wert
        #                      w
        #                       B...Org der Base relativ {W}
        return bP.xy()
    
    def execute( self):
        self._gps_().execute()
        
        x, y = self.bP().xy()
        self.__statistixbuffer_bX.elem( x)
        self.__statistixbuffer_bY.elem( y)

        x, y = self.wP().xy()
        self.__statistixbuffer_wX.elem( x)
        self.__statistixbuffer_wY.elem( y)
        return self
    
    def fv_default( self):
        return self._gps_().fv_default()
    
    def fv_name_smstate( self):
        return self._gps_().sm().fv_name_state_executed()
    
    def read( self):
        return self._gps_().read()
    
    def meanvalue_bX( self):
        return self.__statistixbuffer_bX.mean()

    def meanvalue_bY( self):
        return self.__statistixbuffer_bY.mean()
    
    def meanvalue_wX( self):
        return self.__statistixbuffer_wX.mean()

    def meanvalue_wY( self):
        return self.__statistixbuffer_wY.mean()
    
    def reset( self):
        self._gps_().reset()
        return self
    
    def rPm( self):
        """Position of the measured thing (here it is the position) relative to the rack {R}.
        """
        return self._gps_().rPm()
    
    def rTm( self):
        """Position of the measured thing (here it is the position) relative to the rack {R}.
        """
        return self._gps_().rTm()
    
    def sm( self):
        return self._gps_().sm()
    
    def sPm( self):
        """Position of the measured thing (here it is the position) relative to the sensor {S} itself.
        """
        return self._gps_().sPm()
    
    def satellite_count( self):
        return self._gps_().satellite_count()
    
    def statename( self):
        assert self.sm().fv_smstate_name().value() == self._gps_().statename()
        return self._gps_().statename()
    
    def status( self):
        return self._gps_().status()
    

    def stdev_bX( self):
        return self.__statistixbuffer_bX.stdev()

    def stdev_bY( self):
        return self.__statistixbuffer_bY.stdev()

    def stdev_wX( self):
        return self.__statistixbuffer_wX.stdev()

    def stdev_wY( self):
        return self.__statistixbuffer_wY.stdev()

    def wP( self):
        """Position of the measured thing (here it is the position) relative to the world {W}.
        """
        return self._gps_().wP()
    
    def wXY( self):
        """2D coordinates of the position of the measured thing (here it is the position) relative to the world {W}.
        """
        return self.wP().xy()
    
        
    ############################################################################
    ### P R O T E C T E D
    def _gps_( self):
        return self.__gps


class NavSysThreaded(NavSys, threads.Cycler):

    """Unlike to NavSys NavSysThreaded doesn't block the PLC upon troubles with the connection.
    """

    def __init__( self, id, gps, cycletime=2.5):
        NavSys.__init__( self, id, gps)
        threads.Cycler.__init__( self, cycletime=cycletime, udata=0)

        self.start()
        return
    
    def execute( self):
        """In the threaded version a user call to execute doesn't need to have an effect, because the thread itself calls the execute method of the base class.
        """
        return
    
    def _run_( self, udata):
        super().execute()
        return
    
    
class _NaviSysReading:
    
    def __init__( self, data, time):
        self._data = data
        self.__time = time
        return
    
    def time( self):
        return self.__time
    

class NaviSysReadingFrame:
    
    def __init__( self, T, time):
        super().__init__( T, time)
        assert isinstance( self._data, T3D)
        return
    
    def T( self):
        return self._data
        

class NaviSysReadingPosition:
    
    def __init__( self, P, time):
        super().__init__( P, time)
        assert isinstance( self._data, Vector3)
        return
    
    def P( self):
        return self._data
        
    