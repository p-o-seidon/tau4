#   -*- coding: utf8 -*-
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2017
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

"""
**Internal I/Os.**

*vios* for *Virtual I/Os* could have been an other name for this module.

Anyway, the idea behind this package is to mae internal program connections
future proof, in that communication between an application's main parts is done
as if they were distributed on more than one hardware. So, if one day some components
are deployed to other hardware, the *iios* have to be replaced by *ios*.

.. todo::
    Das muss noch verifiziert werden: Sind wirklich keine Programmänderungen notwendig?
"""

import abc
import multiprocessing as mp
import time

from tau4 import Id
from tau4.data import pandora
from tau4.oop import overrides
from tau4.oop import PublisherChannel


class iPin(metaclass=abc.ABCMeta):

    """Internal Pin.

    \param  id      Eindeutige Identifiation.

    \param  p_pin   pandora.Box, die den Wert des Pins aufnimmt.
                    Wenn iPin ein Eingang ist, hält p_pin nach Ausführung von execute
                    des Ausgangs (der mit dem Eingang connected worden ist!) den Wert des
                    Eingangs, mit dem er vebunden ist.

                    Wenn iPin ein Ausgang ist, hält p_pin den Wert, der durch Ausführung
                    von execute() auf den Eingang, der mit dem Ausgang connected ist,
                    geschrieben wird.

    Konzept:
        iPin ist ein Eingang:
            \verbatim
            ------+
                  |
            Pin o-+-o Signal
                  |
            \endverbatim

        iPin ist ein Ausgang:
            \verbatim
            ---------+
                     |
            Signal o-+-o Pin
                     |
            \endverbatim
    """

    def __init__( self, *, id, p_pin : pandora.Box):
        self.__id = id
        self.__p_pin = p_pin
        return

    def __repr__( self):
        return str( self.id())

    @abc.abstractmethod
    def execute( self):
        """Execute the pin (input or output).
        """
        pass

    def p_pin( self) -> pandora.Box:
        """Wert des Pins, mit dem der User den Eingang (wenn's einer ist) analysiert.

        Ist der Pin ein Ausgang, dann hält diese Box den Wert, der beim letzten
        execute() auf den Ausgang geschrieben worden ist.

        \_2DO:
            Umbenennen nach p_raw()?
        """
        return self.__p_pin

    def id( self):
        """The pin's unique id.
        """
        return self.__id

    @abc.abstractmethod
    def value( self, value=None):
        """The pin's value, no matter whether it's an input or an output.
        """
        pass


class iPins(metaclass=abc.ABCMeta):

    def __init__( self):
        self.__ipins = {}
        return

    def execute( self):
        for pin in self.__ipins.values():
            pin.execute()

        return self

    @abc.abstractmethod
    def ipin_add( self, ipin) -> iPin:
        assert isinstance( ipin.id(), (Id, str))
        self.__ipins[ str( ipin.id())] = ipin
        return ipin

    def ipin( self, id: Id):
        assert isinstance( id, (Id, str))
        return self.__ipins[ str( id)]

    def ipinids( self):
        return self.__ipins.keys()

    def ipins( self):
        return self.__ipins.values()


################################################################################
class iAInp(iPin):

    def __init__( self, id, label, dim="V"):
        super().__init__( id=id, p_pin=pandora.BoxGuarded( id=id+".appside", value=0.0, label=label, dim=dim))
        self.__p_signal = pandora.Box( id=id+".signal", value=0.0)
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
        self.p_pin().value( self.__p_signal.value())
        return self

    def value( self, value=None):
        if value is None:
            return self.p_pin().value()

        self.__p_signal.value( value)
        return self


class iAInpMP(iPin):

    """

    _2DO:
        Ableiten von iAInp - wie?
    """

    def __init__( self, id, label, dim="V"):
        super().__init__( id=id, p_pin=pandora.BoxGuarded( id=id+".appside", value=0.0, label=label, dim=dim))

        self.__valueMP = None
        return

    @overrides( iPin)
    def execute( self):
        assert self.is_connected(), "iAInp '%s' is not connected to any iAOut!" % self.id()
        self.p_pin().value( self.__valueMP.value)
        return

    def is_connected( self):
        return self.__valueMP is not None

    @overrides( iPin)
    def value( self):
        """The pin's value.
        """
        return self.p_pin().value()

    def _valueMP_( self, valueMP: mp.Value):
        self.__valueMP = valueMP
        return self


class iAInps(iPins):

    def ipin_add( self, ipin) -> iPin:
        assert isinstance( ipin, (iAInp, iAInpMP))
        return super().ipin_add( ipin)


class iAOut(iPin):

    def __init__( self, id, label):
        super().__init__( id=id, p_pin=pandora.BoxMonitored( id=id, value=0.0, label=label, dim=""))

        self.__p_signal = pandora.Box( id=id+".signal", value=0.0)
        return
    
    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self.p_pin().value( self.__p_signal.value())
        return self

    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.

        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.__p_signal.value()
                                            # Wird nur von der PLC gelesen. Die
                                            #   App muss den mit diesem iAOUT
                                            #   verbundenen iAINP lesen.
        self.__p_signal.value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self


class iAOutMP(iPin):

    def __init__( self, id, label, dim=""):
        """

        Input                         Output
        --------+                  +--------
                |                  |
        pin o---+---o mp.Value o---+---o pin
                |                  |
                |                  |
                |                  |

        output pin <-- app:         value()
        mp.value <-- output pin:    execute() of output
        input pin <-- mp.value:     execute() of input
        app <-- input pin:          value()

        """
        super().__init__( id=id, p_pin=pandora.BoxMonitored( id=id, value=0.0, label=label, dim=dim))

        self.__valueMP = mp.Value( "f", 0.0)
        return

    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self.__valueMP.value = self.p_pin().value()
        return self

    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.

        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.p_pin().value()
                                            # Wird nur von der PLC gelesen. Die
                                            #   App muss den mit diesem iAOUT
                                            #   verbundenen iAINP lesen.
        self.p_pin().value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self

    def _valueMP_( self):
        """Wird fürs Connecten gebraucht.
        """
        return self.__valueMP


class iAOut2iAInpConnector:

    """Connects internal analog I/Os.

    **Usage**
        See :py:class:`iDOUT2iDINPConnector`.
    """

    def __init__( self, iaout : iAOut):
        assert isinstance( iaout, iAOut)
        self.__iaout = iaout
        return

    def connect_to_ainp( self, iainp: iAInp):
        assert isinstance( iainp, iAInp)
        self.__iaout.p_pin().reg_tau4s_on_modified( lambda tau4pc, iainp=iainp: iainp.value( tau4pc.client().value()))
                                        # AINP beim AOUT reg'en. Wird auf den
                                        #   AOUT geschrieben, wird auf den AINP
                                        #   geschrieben (Signal). "Hereinnehmen"
                                        #   muss der AINP das Signal aber durch
                                        #   die Ausführung von execute()
                                        #   (Signal --> Pin).
        return


class iAOut2iAInpConnectorMP:

    """Connects internal analog I/Os.

    **Usage**
        See :py:class:`iDOUT2iDINPConnector`.
    """

    def __init__( self, iaout : iAOutMP):
        assert isinstance( iaout, iAOutMP)
        self.__iaout = iaout
        return

    def connect_to_ainp( self, iainp: iAInpMP):
        assert isinstance( iainp, iAInpMP)
        iainp._valueMP_( self.__iaout._valueMP_())
        return


class iAOuts(iPins):

    def ipin_add( self, ipin):
        assert isinstance( ipin, (iAOut, iAOutMP))
        return super().ipin_add( ipin)


################################################################################
class iDInp(iPin):

    """Internal DINP.

    Reg'en für tau4p_on_modified kann man sich nur bei iDINPs, nicht bei DOUTs.
    """

    def __init__( self, id, label):
        super().__init__( id=id, p_pin=pandora.BoxClippingMonitored( id=id, value=0, label=label, dim="", bounds=(0, 1)))

        self.__p_signal = pandora.Box( id=id+".signal", value=0)
        return

    def execute( self):
        """Liest p_signal_k und schreibt p_pin.
        """
        self.p_pin().value( self.__p_signal.value())
        return self

    def is_hi( self):
        return self.value() == 1

    def is_lo( self):
        return self.value() == 0

    def _p_signal_( self):
        return self.__p_signal

    def reg_tau4p_on_modified( self, tau4s):
        self.p_pin().reg_tau4p_on_modified( tau4s)
        return

    def value( self, value=None):
        ### Lesen
        #
        #   execute() hat fv_signal_k geslesen und fv_pin beschrieben.
        #
        if value is None:
            return self.p_pin().value()

        ### Schreiben
        #
        #   execute() liest p_signal und schreibt p_pin.
        #
        self.__p_signal.value( 1 if value else 0)
        return self


class iDInpMP(iPin):

    def __init__( self, id, label):
        super().__init__( id=id, p_pin=pandora.BoxMonitored( id=id+".appside", value=0, label=label, dim=""))

        self.__valueMP = None
        return

    @overrides( iPin)
    def execute( self):
        assert self.is_connected(), "iDInp '%s' is not connected to any iDOut!" % self.id()
        self.p_pin().value( self.__valueMP.value)
        return

    def is_connected( self):
        return self.__valueMP is not None

    def is_hi( self):
        return self.value() == 1

    def is_lo( self):
        return self.value() == 0

    @overrides( iPin)
    def value( self):
        """The pin's value.
        """
        return self.p_pin().value()

    def _valueMP_( self, valueMP: mp.Value):
        self.__valueMP = valueMP
        return self


class iDInpEdgeSensitiveSenderDriven(iDInp):

    """Internal DINP.

    Reg'en für tau4p_on_modified kann man sich nur bei iDINPs, nicht bei DOUTs.

    CAUTION:
        is_edge-sensitive kann nicht richtig funktionieren: 2-mal execute() ausführen
        und die Flanke "ist weg". Aber hat der, der den DInp liest, sie gesehen?
    """

    def __init__( self, id, label):
        super().__init__( id=id, label=label)

        self.__p_signal_k = pandora.Box( id=id+".signal[ k]", value=0)
                                        # Auf diese Box wird vom Sender geschrieben.
                                        #   Sender sollte dabei ein anderer iDOUT
                                        #   sein, der mit dem iDINP mit
                                        #   DOUT2DINPConnector verbunden worden
                                        #   ist.
                                        #   Innen, also in p_pin "landet" der
                                        #   Wert durch execute().
                                        #   Vom Empfänger gelesen werden kann nur
                                        #   diese p_pin!
        self.__p_signal_j = pandora.Box( id=id+".signal[ k-1]", value=0)
                                        # Diese Box braucht's für die Flankendetektion
        self.__is_detected_pos_edge = False
        return

    def execute( self):
        """Liest p_signal_k und schreibt p_pin.
        """
        if self.__p_signal_k.value() == self.__p_signal_j.value():
            #self.p_pin().value( 0)
            pass

        elif self.__p_signal_k.value() > self.__p_signal_j.value():
            self.p_pin().value( 1)

#        elif self.__p_signal_k.value() < self.__p_signal_j.value():
#            self.p_pin().value( -1)

        self.__p_signal_j.value( self.__p_signal_k.value())
        return self

    def value( self, value=None):
        ### Lesen
        #
        #   execute() hat p_signal_k geslesen und p_pin beschrieben.
        #
        if value is None:
            value = self.p_pin().value()
            self.p_pin().value( 0)
            return value

        ### Schreiben
        #
        #   execute() liest p_signal_k und schreibt p_pin.
        #
        self.__p_signal_k.value( 1 if value else 0)
        return self


class iDInpPulsativeSenderDriven(iDInp):

    """Internal DINP.

    Reg'en für tau4p_on_modified kann man sich nur bei iDINPs, nicht bei DOUTs.
    """

    class _States:

        _IS_LO = 0
        _IS_HI = 1




    def __init__( self, id, label, pulseduration_min):
        super().__init__( id=id, label=label)

        self.__p_signal_k = pandora.Box( id=id+".signal[ k]", value=0)
                                        # Auf diese Box wird vom Sender geschrieben.
                                        #   Sender sollte dabei ein anderer iDOUT
                                        #   sein, der mit dem iDINP mit
                                        #   DOUT2DINPConnector verbunden worden
                                        #   ist.
                                        #   Innen, also in p_pin "landet" der
                                        #   Wert durch execute().
                                        #   Vom Empfänger gelesen werden kann nur
                                        #   diese p_pin!
        self.__p_signal_j = pandora.Box( id=id+".signal[ k-1]", value=0)
                                        # Diese Box braucht's für die Flankendetektion
        self.__pulsetime_min = pulseduration_min
        self.__state = self._States._IS_LO
        return

    def execute( self):
        if self.__state == self._States._IS_LO:
            if self.__p_signal_k.value() == self.__p_signal_j.value():
                pass

            elif self.__p_signal_k.value() > self.__p_signal_j.value():
                self.p_pin().value( 1)
                self.__time = time.time()
                self.__state = self._States._IS_HI

            elif self.__p_signal_k.value() < self.__p_signal_j.value():
                pass

        elif self.__state == self._States._IS_HI:
            if time.time() - self.__time > self.__pulsetime_min:
                self.p_pin().value( 0)
                self.__state = self._States._IS_LO

        self.__p_signal_j.value( self.__p_signal_k.value())
        return self

    def value( self, value=None):
        ### Lesen
        #
        #   execute() hat fv_signal_k geslesen und fv_pin beschrieben.
        #
        if value is None:
            return self.p_pin().value()

        ### Schreiben
        #
        #   execute() liest p_signal_k und schreibt p_pin.
        #
        self.__p_signal_k.value( 1 if value else 0)
        return self


class iDInpEdgeSensitiveReceiverDriven(iDInp):

    """Internal DINP.

    Reg'en für tau4p_on_modified kann man sich nur bei iDINPs, nicht bei DOUTs.
    """

    def __init__( self, id, label):
        super().__init__( id=id, label=label)

        self.__p_signal_k = pandora.Box( id=id+".signal[ k]", value=0)
                                        # Auf diese Box wird vom Sender geschrieben.
                                        #   Sender sollte dabei ein anderer iDOUT
                                        #   sein, der mit dem iDINP mit
                                        #   DOUT2DINPConnector verbunden worden
                                        #   ist.
                                        #   Innen, also in p_pin "landet" der
                                        #   Wert durch execute().
                                        #   Vom Empfänger gelesen werden kann nur
                                        #   diese p_pin!
        self.__p_signal_j = pandora.Box( id=id+".signal[ k-1]", value=0)
                                        # Diese Box braucht's für die Flankendetektion
        return

    def execute( self):
        """Excecuted by senders.
        """
        pass

    def _execute_( self):
        """Executed by receivers.
        """
        if self.__p_signal_k.value() == self.__p_signal_j.value():
            self.p_pin().value( 0)

        elif self.__p_signal_k.value() > self.__p_signal_j.value():
            self.p_pin().value( 1)
                                            # Pos. Flanke
        elif self.__p_signal_k.value() < self.__p_signal_j.value():
            self.p_pin().value( -1)
                                            # Neg. Flanke
        self.__p_signal_j.value( self.__p_signal_k.value())
        return self

    def value( self, value=None):
        ### Lesen
        #
        #   execute() hat fv_signal_k geslesen und fv_pin beschrieben.
        #
        if value is None:
            self._execute_()
            return self.p_pin().value()

        ### Schreiben
        #
        #   execute() liest p_signal_k und schreibt p_pin.
        #
        self.__p_signal_k.value( 1 if value else 0)
        return self


class iDInps(iPins):

    def ipin_add( self, ipin: iDInp):
        assert isinstance( ipin, (iDInp, iDInpMP))
        return super().ipin_add( ipin)


class iDOut(iPin):

    def __init__( self, id, label):
        super().__init__( id=id, p_pin=pandora.BoxClippingMonitored( id=id, value=0, label=label, dim="", bounds=(0, 1)))

        self.__p_signal_k = pandora.Box( id=id+".signal[ k]", value=0)
        return

    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self.p_pin().value( self.__p_signal_k.value())
        return self

    def to_hi( self):
        return self.value( 1)

    def to_lo( self):
        return self.value( 0)

#    def _p_signal_k_( self):
#        return self.__p_signal_k

    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.

        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.__p_signal_k.value()
                                            # Wird nur von der PLC gelesen. Die
                                            #   App muss den mit diesem iDOUT
                                            #   verbundenen iDINP lesen.
        self.__p_signal_k.value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self


class iDOutMP(iPin):

    def __init__( self, id, label):
        """

        Input                         Output
        --------+                  +--------
                |                  |
        pin o---+---o mp.Value o---+---o pin
                |                  |
                |                  |
                |                  |

        output pin <-- app:         value()
        mp.value <-- output pin:    execute() of output
        input pin <-- mp.value:     execute() of input
        app <-- input pin:          value()

        """
        super().__init__( id=id, p_pin=pandora.BoxMonitored( id=id, value=0, label=label, dim=""))

        self.__valueMP = mp.Value( "i", 0)
        return

    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        self.__valueMP.value = self.p_pin().value()
        return self

    def to_hi( self):
        return self.value( 1)

    def to_lo( self):
        return self.value( 0)

    def value( self, value=None):
        """Lesen und Schreiben des Ausgangs.

        Der Ausgang auf App-Seite ändert sich nur bei Ausführung von execute(),
        das von der PLC ausgeführt wird.
        """
        if value is None:
            return self.p_pin().value()
                                            # Wird nur von der PLC gelesen. Die
                                            #   App muss den mit diesem iAOUT
                                            #   verbundenen iAINP lesen.
        self.p_pin().value( value)
                                        # Wird nach self._fv_pin geschrieben.
        return self

    def _valueMP_( self):
        """Wird fürs Connecten gebraucht.
        """
        return self.__valueMP


class iDOutPulsative(iDOut):

    class _State:

        _IS_LO = 0
        _IS_HI = 1


    def __init__( self, id, label, pulseduration_min=0.100):
        super().__init__( id=id, label=label)

        self.__pulseduration_min = pulseduration_min
        self.__time = 0
        self.__state = self._State._IS_LO
        return

    def execute( self):
        """Schaltung des Ausgangs, Ausführung durch die PLC, publishing an App.
        """
        if self.__state == self._State._IS_LO:
            if self.value() == 1:
                self.p_pin().value( 1)
                self.__time = time.time()
                self.__state = self._State._IS_HI

        elif self.__state == self._State._IS_HI:
            if self.value() == 0 or time.time() - self.__time > self.__pulseduration_min:
                self.value( 0)
                self.p_pin().value( 0)
                self.__state = self._State._IS_LO

        else:
            assert not "Trapped!"

        return self


class iDOut2iDInpConnector:

    """Connect internal I/Os.

    **Usage**

    .. code-block:: Python

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
        assert isinstance( idout, iDOut)
        self.__idout = idout
        return

    def connect_to_dinp( self, idinp):
        assert isinstance( idinp, iDInp)
        self.__idout.p_pin().reg_tau4s_on_modified( lambda tau4pc, idinp=idinp: idinp.value( tau4pc.client().value()))
        return



class iDOut2iDInpConnectorMP:

    """Connects internal digital I/Os.

    **Usage**
        See :py:class:`iDOUT2iDINPConnector`.
    """

    def __init__( self, idout: iDOutMP):
        assert isinstance( idout, iDOutMP)
        self.__idout = idout
        return

    def connect_to_ainp( self, idinp: iDInpMP):
        assert isinstance( idinp, iDInpMP)
        idinp._valueMP_( self.__idout._valueMP_())
        return


class iDOuts(iPins):

    def ipin_add( self, ipin):
        assert isinstance( ipin, (iDOut, iDOutMP))
        return super().ipin_add( ipin)



