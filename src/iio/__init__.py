#   -*- coding: utf8 -*-
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2016
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
from tau4.sweng import PublisherChannel


class iPIN(metaclass=abc.ABCMeta):
    
    def __init__( self, *, id, fv_pin):
        self._id = id
        self._fv_pin = fv_pin
        return
    
    @abc.abstractmethod
    def execute( self):
        pass
    
    def fv_pin( self):
        return self._fv_pin
    
    def id( self):
        return self._id
    
    @abc.abstractmethod
    def value( self, value=None):
        pass


class iPINs(metaclass=abc.ABCMeta):
    
    def __init__( self):
        self.__ipins = {}
        return
    
    def execute( self):
        for pin in self.__ipins.values():
            pin.execute()
            
        return self
    
    @abc.abstractmethod
    def ipin_add( self, ipin):
        self.__ipins[ ipin.id()] = ipin
        return self
    
    def ipin( self, id):
        return self.__ipins[ id]
    
    
################################################################################        
class iAINP(iPIN):
    
    def __init__( self, id, label):
        super().__init__( id=id, fv_pin=flex.VariableDeMo( id=id+".appside", value=0.0, label=label, dim=""))
        self.__fv_signal = flex.Variable( id=id+".signal", value=0.0)
                                        # Auf diese FV wird vom Sender geschrieben.
                                        #   Sender sollte dabei ein anderer iDOUT 
                                        #   sein, der mit dem iDINP mit 
                                        #   DOUT2DINPConnector verbunden worden 
                                        #   ist.
                                        #   Innen, also in fv_pin "landet" der 
                                        #   Wert durch execute().
                                        #   Vom Empfänger gelesen kann nur diese
                                        #   fv_pin!
        return

    def execute( self):
        """Wert "hereinnehmen": Signal -> Pin.
        """
        self.fv_pin().value( self.__fv_signal.value())
        return self
    
    def value( self, value=None):
        if value is None:
            return self.fv_pin().value()
        
        self.__fv_signal.value( value)
        return self

    
class iAINPs(iPINs):
    
    def ipin_add( self, ipin):
        assert isinstance( ipin, iAINP)
        return super().ipin_add( ipin)


class iAOUT(iPIN):
    
    def __init__( self, id, label):
        super().__init__( id=id, fv_pin=flex.VariableDeMo( id=id, value=0.0, label=label, dim="", value_min=0, value_max=1))

        self.__fv_signal = flex.Variable( id=id+".signal", value=0.0)
        return
    
    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self._fv_pin.value( self.__fv_signal.value())
        return self
    
    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.
        
        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.__fv_signal.value()
                                            # Wird nur von der PLC gelesen. Die 
                                            #   App muss den mit diesem iAOUT 
                                            #   verbundenen iAINP lesen.       
        self.__fv_signal.value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self
            
        
class iAOUT2iAINPConnector:
    
    """Connect internal I/Os.
    
    Usage::
        See iDOUT2iDINPConnector.
    """
    
    def __init__( self, iaout):
        assert isinstance( iaout, iAOUT)
        self.__iaout = iaout
        return
    
    def connect_to_ainp( self, iainp):
        assert isinstance( iainp, iAINP)
        self.__iaout.fv_pin().reg_tau4s_on_modified( lambda tau4pc, iainp=iainp: iainp.value( tau4pc.client().value()))
                                        # AINP beim AOUT reg'en. Wird auf den 
                                        #   AOUT geschrieben, wird auf den AINP 
                                        #   geschrieben (Signal). "Heirennehmen" 
                                        #   muss der AINP das Signal aber durch 
                                        #   die Ausführung von execute() 
                                        #   (Signal --> Pin).
        return
    

class iAOUTs(iPINs):
    
    def ipin_add( self, ipin):
        assert isinstance( ipin, iAOUT)
        return super().ipin_add( ipin)


################################################################################
class iDINP(iPIN):
    
    """Internal DINP.
    
    Reg'en für tau4p_on_modified kann man sich nur bei iDINPs, nicht bei DOUTs.
    """
    
    def __init__( self, id, label, is_edge_sensitive=False):
        super().__init__( id=id, fv_pin=flex.VariableDeMo( id=id, value=0, label=label, dim="", value_min=0, value_max=1))
        
        self.__fv_signal_k = flex.Variable( id=id+".signal[ k]", value=0)
                                        # Auf diese FV wird vom Sender geschrieben.
                                        #   Sender sollte dabei ein anderer iDOUT 
                                        #   sein, der mit dem iDINP mit 
                                        #   DOUT2DINPConnector verbunden worden 
                                        #   ist.
                                        #   Innen, also in fv_pin "landet" der 
                                        #   Wert durch execute().
                                        #   Vom Empfänger gelesen kann nur diese
                                        #   fv_pin!
        self.__fv_signal_j = flex.Variable( id=id+".signal[ k-1]", value=0)
                                        # Diese FV braucht's für die Flankendetektion
        self.__is_edge_sensitive = is_edge_sensitive
        return

    def execute( self):
        """Liest fv_signal_k und schreibt fv_pin.
        """
        if self.__is_edge_sensitive:
            if self.__fv_signal_k.value() == self.__fv_signal_j.value():
                self._fv_pin.value( 0)
                
            elif self.__fv_signal_k.value() > self.__fv_signal_j.value():
                self._fv_pin.value( 1)
    
            elif self.__fv_signal_k.value() < self.__fv_signal_j.value():
                self._fv_pin.value( -1)
            
            self.__fv_signal_j.value( self.__fv_signal_k.value())
            
        else:
            self._fv_pin.value( self.__fv_signal_k.value())
            
        return self
    
    def reg_tau4p_on_modified( self, tau4s):
        self._fv_pin.reg_tau4p_on_modified( tau4s)
        return
    
    def value( self, value=None):
        ### Lesen
        #
        #   execute() hat fv_signal_k geslesen und fv_pin beschrieben.
        #
        if value is None:
            return self._fv_pin.value()
        
        ### Schreiben
        #
        #   execute() liest fv_signal_k und schreibt fv_pin.
        #
        self.__fv_signal_k.value( 1 if value else 0)
        return self

    
class iDINPs(iPINs):
    
    def ipin_add( self, ipin):
        assert isinstance( ipin, iDINP)
        return super().ipin_add( ipin)


class iDOUT(iPIN):
    
    def __init__( self, id, label):
        super().__init__( id=id, fv_pin=flex.VariableDeMo( id=id, value=0, label=label, dim="", value_min=0, value_max=1))

        self.__fv_signal_k = flex.Variable( id=id+".signal[ k]", value=0)
        return
    
    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self._fv_pin.value( self.__fv_signal_k.value())
        return self
    
    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.
        
        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.__fv_signal_k.value()
                                            # Wird nur von der PLC gelesen. Die 
                                            #   App muss den mit diesem iDOUT 
                                            #   verbundenen iDINP lesen.       
        self.__fv_signal_k.value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self
    
    
class iDOUT2iDINPConnector:
    
    """Connect internal I/Os.
    
    Usage::
        class iIOs(metaclass=Singleton):
            
            def __init__( self):
                self.__idinps_at_mmi = iDINPsAtMMI()
                self.__idouts_at_mmi = iDOUTsAtMMI()
        
                self.__idinps_at_plc = iDINPsAtPLC()
                self.__idouts_at_plc = iDOUTsAtPLC()
                
                self.__idinps_at_rop = iDINPsAtROP()
                self.__idouts_at_rop = iDOUTsAtROP()
        
                self._connect_idouts_to_idinps_()
                return
            
            def _connect_idouts_to_idinps_( self):
                
                ### ROP --> MMI
                #
                #idc = rop.DOUT2DINPConnector( rop.ROP().idouts().ipin( "rop.rop_is_enabled"))
                #idc.connect_to_dinp( plc.PLC().idinps( "mmi.rop_is_enabled"))
            
                ### ROP --> PLC
                #
                idc = iDOUT2iDINPConnector( self.idouts_rop().idout_ROP_IS_ENABLED())
                idc.connect_to_dinp( self.idinps_plc().idinp_ROP_IS_ENABLED())
            
                ### PLC --> MMI
                #
                idc = iDOUT2iDINPConnector( self.idouts_plc().idout_MMI_ENABLE())
                idc.connect_to_dinp( self.idinps_mmi().idinp_MMI_ENABLE())
            
                ### PLC --> ROP
                #
                idc = iDOUT2iDINPConnector( self.idouts_plc().idout_ROP_ENABLE())
                idc.connect_to_dinp( self.idinps_rop().idinp_ROP_ENABLE())
            
                ### MMI --> PLC
                #
                idc = iDOUT2iDINPConnector( self.idouts_mmi().idout_BUTTON_START())
                idc.connect_to_dinp( self.idinps_plc().idinp_BUTTON_START())
                
                return
            
            def idinps_mmi( self):
                return self.__idinps_at_mmi
            
            def idinps_plc( self):
                return self.__idinps_at_plc
            
            def idinps_rop( self):
                return self.__idinps_at_rop
        
            def idouts_mmi( self):
                return self.__idouts_at_mmi
        
            def idouts_plc( self):
                return self.__idouts_at_plc
        
            def idouts_rop( self):
                return self.__idouts_at_rop
        
    """
    
    def __init__( self, idout):
        assert isinstance( idout, iDOUT)
        self.__idout = idout
        return
    
    def connect_to_dinp( self, idinp):
        assert isinstance( idinp, iDINP)
        self.__idout.fv_pin().reg_tau4s_on_modified( lambda tau4pc, idinp=idinp: idinp.value( tau4pc.client().value()))
        return
    
 

class iDOUTs(iPINs):
    
    def ipin_add( self, ipin):
        assert isinstance( ipin, iDOUT)
        return super().ipin_add( ipin)



