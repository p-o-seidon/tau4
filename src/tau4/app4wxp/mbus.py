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

from tau4.com import mbus


class Messages:
    
    class GPS:
        
        class Error(mbus.Message):
            
            def __init__( self, error):
                super().__init__()
                
                self.__error = error
                return
            
            def __str__( self):
                return "GPS Error: %s.\n" % self.__error

            
        class Data(mbus.Message):
            
            def __init__( self, gps_response):
                super().__init__()
                
                self.__gps_response = gps_response
                return
            
            def count_sats( self):
                return self.__gps_response.sats
            
            def error_margin( self):
                return self.__gps_response.error
            
            def hspeed( self):
                return self.__gps_response.speed()
            
            def ll2xy( self, lat, lon):
                y = lat * 111.111 * 1000
                x = cos( radians( lat)) * 111.111 * 1000
                return (x, y)
            
            def map_url( self):
                return self.__gps_response.map_url()
            
            def pos_precision( self):
                return self.__gps_response.position_precision()
            
            def posLL( self):
                return self.__gps_response.position()
            
            def posXY( self):
                return self.ll2xy( *self.posLL())

