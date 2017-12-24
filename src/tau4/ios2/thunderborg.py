#   -*- coding: utf8 -*- #
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

import abc
import time

from tau4 import Id
from tau4.data import pandora
from tau4 import ios2
from tau4.ios2._common import MotorDriver, MotorEncoder
from tau4.oop import overrides, Singleton
from tau4.robotix.mobile2 import controllers as tau4controllers


class MD2000(MotorDriver):

    """Ein konkretes Board MD2000 bestehend aus einem MotorDriverTB und zwei MotorEncoder.

    \param  id

    \param  motorencoderLHS

    \param  motorencoderRHS

    \param  is_setup

    \note
        Die beiden Motorregler sind threaded mit einer Ts = 5 ms.

    """

    ############################################################################
    ### Ctor
    #
    def __init__( self, *, id, motorencoderLHS: MotorEncoder, motorencoderRHS: MotorEncoder, is_setup=True):
        MotorDriver.__init__( self, id=id)

        ### ThunderBorg
        #
        self.__motordriver = MotorDriverTB( id="MotorDriverTB", is_setup=is_setup)
                                        # Kann 2 Motoren
        ### Encoder
        #
        self.__motorencoder_1 = motorencoderLHS
        self.__motorencoder_2 = motorencoderRHS

        ### DriveController
        #
        p_Ts = pandora.Box( value=0.005)
        self.__motorcontroller_1 = _MotorController( motornumber=1, motorencoder=self.__motorencoder_1, motordriver=self.__motordriver, p_Ts=p_Ts)
        self.__motorcontroller_2 = _MotorController( motornumber=2, motorencoder=self.__motorencoder_2, motordriver=self.__motordriver, p_Ts=p_Ts)

        ### Status
        #
        self.status_to_on()
        self.status_to_running()
        return

    ############################################################################
    ### Overrides
    #
    @overrides(MotorDriver)
    def speed_100( self) -> (float, float):
        """Geschwindigkeitsistwert aus den Encodern(!) lesen.
        """
        lhs = self.__motorencoder_1.speed_100()
        rhs = self.__motorencoder_2.speed_100()
        return lhs, rhs

    @overrides(MotorDriver)
    def speed_100( self, lhs_100: float, rhs_100: float):
        """Geschwindigkeitssollwert in den Regler(!) schreiben.
        """
        self.__motorcontroller_1.p_w_100().value( lhs_100)
        self.__motorcontroller_2.p_w_100().value( rhs_100)
        return self

    @overrides(MotorDriver)
    def status_change( self, status):
        assert self.status_is_valid( status)
        if self.status_is_off():
            self.__motorcontroller_1.to_off()
            self.__motorcontroller_2.to_off()

        elif self.status_is_on():
            self.__motorcontroller_1.to_on()
            self.__motorcontroller_2.to_on()

        elif self.status_is_running():
            self.__motorcontroller_1.to_running()
            self.__motorcontroller_2.to_running()

        else:
            self.__motorcontroller_1.to_off()
            self.__motorcontroller_2.to_off()

        return self


class _MotorController(tau4controllers.ThreadedDriveController):

    """Drehzahlregler, threaded, selbststartend,

    Es handelt sich hier also um eine abgeschlossene, eisatzbereite Einheit,
    die nicht darauf angwiesen ist, wie (schnell) sie von der App ausgeführt wird.

    \param  motorencoder
        Braucht der NodeYReader zum Lesen des Istwertes.

    \param  motordriver
        Braucht der NodeUWriter zum Schreiben des Sollwerts.
    """

    def __init__( self, motornumber, motorencoder, motordriver, p_Ts):

        self.__motornumber = motornumber
        self.__motordriver = motordriver
        self.__motorencoder = motorencoder

        self.__p_w_100 = pandora.Box( value=0.0)
        self.__p_e_100 = pandora.Box( value=0.0)
        self.__p_u_100 = pandora.BoxClippingMonitored( value=0.0)
        self.__p_y_100 = pandora.Box( value=0.0)
        self.__p_y_filtered_100 = pandora.BoxMonitored( value=0.0)

        super().__init__( motorencoder=motorencoder, motordriver=motordriver, p_Ts=p_Ts)
        return

    def nodes( self):
        nodes = (\
            self.NodeWReader( self.__pw_100),
            self.NodeYReader( self.__p_y_100, self.__motorencoder),
            self.NodeSummingPoint( p_w=self.__p_w_100, p_y=self.__p_y_100, p_e=self.__p_e_100),
            self._node_algorithm_( "dt1", self.p_Ts(), self.__p_e_100, self.__p_u_100),
            self.NodeUWriter( self.__p_u_100, self.__motordriver),
            self.NodePublisher( p_w=self.__p_w_100, p_y=self.__p_y_100, p_e=self.__p_e_100, p_u=self.__p_u_100, p_Ts=self.p_Ts()),
            )

        return nodes

    def p_w_100( self):
        return self.__pw_100


class MotorDriverTB(MotorDriver):

    """Ein konkretes Board, ThunderBorg - siehe https://www.piborg.org/blog/thunderborg-getting-started und https://www.piborg.org/blog/thunderborg-examples.

    Die Kommunikation mit dem TB erfolgt über I2C.

    \note
        MotorDriverTB ist nicht vom IOSystem abhängig, die Kommunikation mit der
        Harwdare erfolgt über I2C und damit \b sofort!

    \note
        Der TunderBorg kann soviel mehr, als hier implementiert ist! Siehe
        https://www.piborg.org/blog/thunderborg-getting-started und https://www.piborg.org/blog/thunderborg-examples.
    """

    def __init__( self, *, id, address=0x15, is_setup=True):
        MotorDriver.__init__( self, id=id)

        import ThunderBorg3
        self.__tb = ThunderBorg3.ThunderBorg()
        self.__tb.i2cAddress = address
                                        # Adresse könnte sw-mäßig geändert werden.
        self.__tb.Init()

        return

    @overrides(MotorDriver)
    def speed_100( self) -> (float, float):
        """Geschwindigkeitsistwert aus dem TB lesen (wie weiß der TB die Geschwindigkeit?!).
        """
        lhs = self.__tb.GetMotor1()
                                        # Wie macht das der ThunderBorg? Liest
                                        #   er einfach, was vorher geschrieben
                                        #   worden ist? Wohl schon, denn dass man
                                        #   Encoder anschließen könnte, habe ich
                                        #   nicht gesehen.
        rhs = self.__tb.GetMotor2()
        return lhs, rhs

    @overrides(MotorDriver)
    def speed_100( self, lhs: float, rhs: float):
        """Geschwindigkeitssollwert in den TB schreiben.
        """
        if self.is_direction_inverted():
            lhs, rhs = -rhs, -lhs

        if lhs is not None:
            lhs = lhs/100*self.speed_max_100()
            lhs /= 100
            self.__tb.SetMotor1( lhs)

        if rhs is not None:
            rhs = rhs/100*self.speed_max_100()
            rhs /= 100
            self.__tb.SetMotor2( rhs)

        return self

    @overrides( MotorDriver)
    def status_change( self, status):
        pass


def main():
    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")
