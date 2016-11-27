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
from tau4.sensors import Locator, Sensor3


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
        return self._gps_().rPm()
    
    def sPm( self):
        return self._gps_().sPm()
    
    def wP( self):
        return self._gps_().wP()
    
    def wXY( self):
        return self.wP().xy()
    
        
    ############################################################################
    ### P R O T E C T E D
    def _gps_( self):
        return self.__gps
    
