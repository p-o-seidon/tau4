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


import random
from tau4.io.hal import HWL4IOs


class NoIOs(HWL4IOs):
    
    def ainp_voltage( self, id):
        return random.randint( 0, 500)/100.0
    
    def aout_voltage( self, id, v):
        pass
    
    def dinp_value( self, id):
        return random.randint( 0, 1)
    
    def dout_value( self, id, v):
        pass
    

