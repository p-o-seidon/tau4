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

import abc
from tau4.data import flex
from tau4.sweng import Singleton


class PIN(metaclass=abc.ABCMeta):
    
    """PIN eines DAQs.
    
    :param  id:     
        Pin-Id.
        
    :param  fv_raw: 
        Vsriable, die den rohen (alo ugefilterten etc.) Wert hält. Bei digitalen 
        I/Os handelt es sich um die Werte 0 und 1, bei analogen I/Os um die 
        Spannungswerte in V.
    """
    
    def __init__( self, id, fv_raw):
        self.__id = id
        self.__fv_raw = fv_raw

        self.__hal = None
        return

    @abc.abstractmethod
    def execute( self):
        pass
    
    def fv_raw( self):
        """Wert direkt am Pin, also noch bevor gefiltert wird.
        
        ..todo::
            2DO: Umbenennen nach fv_pin()?
        """
        return self.__fv_raw
    
    def id( self):
        return self.__id
    
    def _hal_( self, hal=None):
        """Hardware Abstraction Layer.
        """
        if hal is None:
            return self.__hal
        
        self.__hal = hal
        return self
    
    def hwl( self):
        """Konkreter Hardware Layer des Hardware Abstaction Layers.
        """
        return self.__hal.hwl()
    

class PIN4Unittests(PIN):
    
    """
    
    Usage::

        fv_0900 = flex.Variable( id=-1, value=0.0)
    
        r_0900 = RangerSharpGP2D12( \
            id="irs.09:00",
            ifel=ELIF4SharpInfraredSensor( PIN4Unittests( fv_0900)),
            rTs=T3DFromEuler( -0.5, 0.5/2, 0, radians( 180), 0, 0)
            )
                                            # Der Org sitzt zwischen den 
                                            #   beiden Antriebsrädern.
                                            #   X zeigt vom Org zum rechten 
                                            #   Rad, Y zeigt vom Org zur Front,
                                            #   was EINE BLÖDE ENTSCHEIDUNG war.
                                            #   Der Sensorstrahl läuft entlang der 
                                            #   X-Achse des Sensors, die nach
                                            #   links zeigt.
        fv_0900.value( 42)
                                        # r_0900.fv_raw().value() liefert jetzt 
                                        #   den Wert 42.
    """
    
    def execute( self):
        pass

    
class PINs(dict):
    
    """Alle Pins eines DAQ.
    """
    
    def __init__( self, hal):
        super().__init__()
        
        self.__hal = hal
        return
    
    def __call__( self, id):
        if id is None:
            return self
        
        return self[ id]

    def add( self, pin):
        """Pin hinzufügen.
        
        Dabei wird dem Pin der HAL mitgegeben.
        """
        pin._hal_( self.__hal)
        self[ pin.id()] = pin
    
    def hwl( self):
        """Konkreter Hardware Layer des Hardware Abstraction Layers.
        """
        return self.__hal.hwl()
    

class AINP(PIN):

    def execute( self):
        self.fv_raw().value( self.hwl().ainp_voltage( self.id()))
    
    
class AINPs(PINs):
    
    def add( self, pin):
        assert isinstance( pin, AINP)
        super().add( pin)

    
class AOUT(PIN):

    def execute( self):
        self.hwl().aout_voltage( self.id(), self.fv_raw().value())
    
    
class AOUTs(PINs):
    
    def add( self, pin):
        assert isinstance( pin, AOUT)
        super().add( pin)

    
class DINP(PIN):

    def execute( self):
        self.fv_raw().value( self.hwl().dinp_value( self.id()))
    
    
class DINPs(PINs):
    
    def add( self, pin):
        assert isinstance( pin, DINP)
        super().add( pin)

    
class DOUT(PIN):

    def execute( self):
        self.hwl().dout_value( self.id(), self.fv_raw().value())
    
    
class DOUTs(PINs):
    
    def add( self, pin):
        assert isinstance( pin, DOUT)
        super().add( pin)

    
class HAL4IOs(metaclass=Singleton):
    
    """Hardware Abstraction Layer.
    
    Usage::
    
        id = _AINP_PINBR_IRS_0900
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
        id = _AINP_PINBR_IRS_1030
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
        id = _AINP_PINBR_IRS_1200
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
        id = _AINP_PINBR_IRS_1330
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
        id = _AINP_PINBR_IRS_1500
        HAL4IOs().ainps().add( AINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=2.8, label="%d (AINP: IRS Volts)" % id, dim="V")))
    
        id = _AOUT_PINNBR_MOTOR_LHS
        HAL4IOs().aouts().add( AOUT( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=5, label="%d (AOUT: -)" % id, dim="V")))
        id = _AOUT_PINNBR_MOTOR_RHS
        HAL4IOs().aouts().add( AOUT( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0.0, value_min=0, value_max=5, label="%d (AOUT: -)" % id, dim="V")))

        id = _DINP_PINNBR_FIO05
        HAL4IOs().dinps().add( DINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0, value_min=0, value_max=1, label="%d (DINP: ENABLE)" % id, dim="")))
        id = _DINP_PINNBR_FIO06
        HAL4IOs().dinps().add( DINP( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0, value_min=0, value_max=1, label="%d (DINP: START)" % id, dim="")))
    
        id = _DOUT_PINNBR_FIO07
        HAL4IOs().douts().add( DOUT( id=id, fv_raw=flex.VariableDeClMo( id=id, value=0, value_min=0, value_max=1, label="%d (DOUT: -)" % id, dim="")))


        HAL4IOs().connect_to( NoIOs())
    """
    
    def __init__( self):
        self.__hwl = None
        
        self.__ainps = AINPs( self)
        self.__aouts = AOUTs( self)
        self.__dinps = DINPs( self)
        self.__douts = DOUTs( self)
        return

    def connect_to( self, hwl):
        """Mit konkretem Hardware Layer verbinden.
        """
        self.__hwl = hwl
        return

    def ainps( self, id=None):
        return self.__ainps( id)
    
    def aouts( self, id=None):
        return self.__aouts( id)

    def dinps( self, id=None):
        return self.__dinps( id)
    
    def douts( self, id=None):
        return self.__douts( id)
    
    def execute( self):
        """Alle I/Os lesen und schreiben.
        """
        for pin in self.ainps().values():
            pin.execute()
            
        for pin in self.dinps().values():
            pin.execute()
            
        for pin in self.aouts().values():
            pin.execute()
                
        for pin in self.douts().values():
            pin.execute()
            
        return
    
    def execute_inps( self):
        """Alle INPs lesen.
        """
        for pin in self.ainps().values():
            pin.execute()
            
        for pin in self.dinps().values():
            pin.execute()
            
        return
    
    def execute_outs( self):
        """Alle OUTs schreiben.
        """
        for pin in self.aouts().values():
            pin.execute()
                
        for pin in self.douts().values():
            pin.execute()
            
        return
    
    def hwl( self):
        return self.__hwl


class HWL4IOs(metaclass=abc.ABCMeta):
    
    """Konkreter Hardware Layer, über den der HAL auf die onkrete Hardware zugreift.
    """
    
    @abc.abstractmethod
    def ainp_voltage( self, id):
        pass
    
    @abc.abstractmethod
    def aout_voltage( self, id, v):
        pass
    
    @abc.abstractmethod
    def dinp_value( self, id):
        pass
    
    @abc.abstractmethod
    def dout_value( self, id, v):
        pass
    
    