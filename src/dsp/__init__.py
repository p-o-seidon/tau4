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


import abc
from tau4.data import flex


class _Filter(metaclass=abc.ABCMeta):
    
    def __init__( self, id, label, dimension):
        self.__fv = flex.VariableDeMo( id=id, value=0.0, label=label, dim=dimension)
        return

    @abc.abstractmethod    
    def execute( self):
        pass
    
    def _fv_( self):
        return self.__fv
    
    def reg_tau4s_on_modified( self, tau4s):
        return self.__fv.reg_tau4s_on_modified( tau4s)
    
    def ureg_tau4s_on_modified( self, tau4s):
        return self.__fv.ureg_tau4s_on_modified( tau4s)
    
    def value( self, value=None):
        if value is None:
            return self.__fv.value()
        
        self.__fv.value( value)
        return
    
    
class SavitzkyGolayFilter(_Filter):
    
    def __init__( self, id, label, dimension):
        super().__init__( id, label, dimension)
        return
    
    def execute( self):
        return
    
    
    
