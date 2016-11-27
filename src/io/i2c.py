#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2015
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
import smbus

from tau4 import ThisName


class I2CBus:
    
    def __init__( self, channelnbr):
        self.__channelnbr = channelnbr
        
        self.__smbus = None
        try:
            self.__smbus = smbus.SMBus( self.__channelnbr)
        
        except FileNotFoundError as e:
            logging.critical( ThisName( self) + "(): %s! " % e)
                              
        self.__is_open = False
        return
    
    def close( self):
        assert self.__is_open
        self.__is_open = False
        return self
    
    def open( self):
        self.__is_open = True
        return self
    
    def read_byte( self, address_device, address_register):
        assert self.__is_open
        return 0
    
    def value( self):
        return 0
    
    def write_byte( self, address_device, address_register, value):
        assert self.__is_open
        return
    