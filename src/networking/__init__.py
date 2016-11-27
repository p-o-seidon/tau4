#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by F. Geiger, 1998 - 2016
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


import socket
from subprocess import check_output


class IpAddress:
    
    def __init__( self):
        s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect( ('google.com', 0))
            self.__ipaddr = s.getsockname()[ 0]

        except socket.gaierror:
            self.__ipaddr = "-1.-1.-1.-1"
        return
    
    def as_str( self):
        return str( self.__ipaddr)
    
    def as_numbers( self):
        return map( int, self.as_str().split( "."))
