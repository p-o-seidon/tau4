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
from tau4.mathe.linalg import T3D, Vector3
from tau4.sensors import Locator, Sensor3
from tau4.sweng import PublisherChannel


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
        return self
    
    def fv_default( self):
        return self._gps_().fv_default()
    
    def read( self):
        return self._gps_().read()
    
    def reset( self):
        self._gps_().reset()
        return self
    
    def rPm( self):
        """Position of the measured thing (here it is the position) relative to the rack {R}.
        """
        return self._gps_().rPm()
    
    def sPm( self):
        """Position of the measured thing (here it is the position) relative to the sensor {S} itself.
        """
        return self._gps_().sPm()
    
    def satellite_count( self):
        return self._gps_().satellite_count()
    
    def statename( self):
        return self._gps_().statename()
    
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
        
    