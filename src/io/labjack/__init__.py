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


from tau4.io.labjack import u3
from tau4.io.hal import HWL4IOs


class LabJackU3HV(HWL4IOs):
    
    """abJack U3-HS - Manual siehe https://labjack.com/products/u3.
    
    **Usage**::
    
        id = 1
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
        
        id = 10
        HAL4IOs().aouts().add( AOUT( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=5, label="%d (AOUT: -)" % id, dim="V")))
        
        id = 20
        HAL4IOs().dinps().add( DINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0, value_min=0, value_max=1, label="%d (DINP: -)" % id, dim="")))

        id = 30
        HAL4IOs().douts().add( DOUT( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0, value_min=0, value_max=1, label="%d (DOUT: -)" % id, dim="")))
        
        
        HAL4IOs().connect_to( LabJackU3HV())
        
    """
    
    def __init__( self, fioids4ainp, fioids4aout, fioids4dinp, fioids4dout):
        super().__init__()
        
        self.__fioids4ainp = fioids4ainp
        self.__fioids4aout = fioids4aout
        self.__fioids4dinp = fioids4dinp
        self.__fioids4dout = fioids4dout
        
        self.__labjack = u3.U3()
        self.__labjack.getCalibrationData()
        
        for fionbr in (4, 5, 6, 7):
            if fionbr in self.__fioids4ainp:
                self.__labjack.configAnalog( fionbr)
                
            elif fionbr in self.__fioids4dinp:
                self.__labjack.configDigital( fionbr)
            
            elif fionbr in self.__fioids4dout:
                self.__labjack.configDigital( fionbr)

        return

    def ainp_voltage( self, id):
        assert id in self.__fioids4ainp
        voltage = self.__labjack.getAIN( id)
        return voltage
        
    def aout_voltage( self, id, value):
        assert id in self.__fioids4aout
        pass
    
    def dinp_value( self, id):
        assert id in self.__fioids4dinp
        value = self.__labjack.getFIOState( id)
        return value
    
    def dout_value( self, id, value):
        assert id in self.__fioids4dout
        self.__labjack.setFIOState( id, 1 if value else 0)
        return self
    
    
    
    
    