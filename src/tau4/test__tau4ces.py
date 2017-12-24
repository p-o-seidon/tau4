#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
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


from __future__ import division

from matplotlib import pyplot
import math
import tau4
from tau4.ce import EulerBw4P, EulerBw4PDT1, EulerBw4PIDT1, EulerBw4PIDT1p, EulerBw4gPIDT1p
from tau4.automation.ces import Node4C, SISOController
from tau4.data import pandora
import time
import unittest



class Signals:

    class RECTANGLE:
        def __init__( self, A, f):
            self.__A = A
            self.__f = f
            return

        def __call__( self, t):
            f = self.__A if math.sin( 2*math.pi*self.__f*t) >= 0 else -self.__A
            return f


class NodeSummingPoint(Node4C):

    def __init__( self, p_w, p_y, p_e):
        super().__init__()

        self.__p_w = p_w
        self.__p_y = p_y
        self.__p_e = p_e
        return

    def configure( self, p_Ts):
        pass

    def execute( self):
        print( self.__class__.__name__ + ": Read current value. ")
        self.__p_y.value( self._read_y_())
                                        # Istwert von Hardware lesen.
        print( self.__class__.__name__ + ": Cal. control difference. ")
        self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                        # e = w - y
        super().execute()
        return self

    def _read_y_( self):
        return 0


class NodeAlgorithm(Node4C):

    def __init__( self, *, algorithm):
        super().__init__()

        self.__algorithm = algorithm
        return

    def configure( self, p_Ts):
        self.__algorithm.configure( p_Ts)

        super().configure( p_Ts)
        return self

    def execute( self):
        if self.is_running():
            if self.__algorithm:
                self.__algorithm.execute()

        super().execute()
        return self


class NodeActuator(Node4C):

    def __init__( self, p_u):
        super().__init__()

        self.__p_u = p_u
        return

    def configure( self, p_Ts):
        pass

    def execute( self):
        print( self.__class__.__name__ + ": Write actuation signal to plant. ")
        self._write_u_( self.__p_u.value())

        super().execute()
        return self

    def _write_u_( self, u):
        return self


class NodePublisher(Node4C):

    """Publishing der Signalwerte des reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

    \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
    \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
    \param  p_e     Regelabweichung, s. NodeSummingPoint.
    \param  p_u     Stellgröße, s. NodeActuator.
    \param  p_Ts    Abtastzeit.
    """

    def __init__( self, *, p_w, p_y, p_e, p_u):
        super().__init__()

        self.__p_w = p_w
        self.__p_y = p_y
        self.__p_e = p_e
        self.__p_u = p_u
        return

    def configure( self, p_Ts):
        pass

    def execute( self):
        print( self.__class__.__name__ + ": Publish data. ")
        pandora.Shelf().box( "gui.w(t)").value( self.__p_w.value())
        pandora.Shelf().box( "gui.y(t)").value( self.__p_y.value())
        pandora.Shelf().box( "gui.e(t)").value( self.__p_e.value())
        pandora.Shelf().box( "gui.u(t)").value( self.__p_u.value())

        super().execute()
        return self


class NodePrinter(Node4C):

    def __init__( self, *, p_w, p_y, p_e, p_u, p_Ts, algorithm, pdfpages):
        super().__init__()

        self.__p_w = p_w
        self.__p_y = p_y
        self.__p_e = p_e
        self.__p_u = p_u

        self.__p_Ts = p_Ts

        self.__algorithm = algorithm
        self.__pdfpages = pdfpages

        self.__i = 0
        self.__t_ = []
        self.__w_ = []
        self.__y_ = []
        self.__e_ = []
        self.__u_ = []

        return

    def configure( self, p_Ts):
        pass

    def execute( self):
        """Ausgabe in Files mit pylab.
        """
        self.__t_.append( self.__i * self.__p_Ts.value())
        self.__w_.append( self.__p_w.value())
        self.__y_.append( self.__p_y.value())
        self.__e_.append( self.__p_e.value())
        self.__u_.append( self.__p_u.value())

        self.__i += 1

        super().execute()
        return self

    def to_off( self):

        super().to_off()
        return

    def to_ready( self):
        pyplot.ylim( -500, 500)
        pyplot.plot( self.__t_, self.__w_)
        pyplot.plot( self.__t_, self.__e_)
        pyplot.plot( self.__t_, self.__u_)
        pyplot.suptitle( self.__algorithm.info())
        self.__pdfpages.savefig()
        pyplot.clf()

        super().to_ready()
        return self

    def to_running( self):
        self.__i = 0

        super().to_running()
        return self


class _TESTCASE__SISOController(unittest.TestCase):

    def test__simple( self):
        """
        """
        print

        ##  Default-Parameter für die Regler holen
        #
        p_Kp = pandora.Box( value=1.0)
        p_Ki = pandora.Box( value=1.0)
        p_Kd = pandora.Box( value=1.0)
        p_alpha = pandora.Box( value=0.7)

        ##  Variable holen, über die die Nodes zusammenhängen und mit
        #   denen sie arbeiten.
        #
        p_w = pandora.Box( value=100.0)
        p_y = pandora.Box( value=0.0)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.BoxClipping( value=0.0, bounds=(-400, 400))
                                        # p_u als VariableMo def'en, damit
                                        #   Sättigung entdeckt werden kann.
                                        #   Die  B e r e i c h s g r e n z e n
                                        #   m ü s s e n   mit dem Aktuator-Knoten
                                        #   a b g e s t i m m t   werden!
        p_Ts = pandora.BoxClippingMonitored( id="controller.Ts", label="Ts", dim="s", value=0.010, bounds=(0.001, None))

        ##  Variable fürs GUI holen
        #
        p = pandora.BoxMonitored( id="gui.w(t)", label="u(2)", dim="", value=0.0)
        p.reg_tau4s_on_modified( self._controller_data_changed_)
        p = pandora.BoxMonitored( id="gui.y(t)", label="u(2)", dim="", value=0.0)
        p.reg_tau4s_on_modified( self._controller_data_changed_)
        p = pandora.BoxMonitored( id="gui.e(t)", label="u(2)", dim="", value=0.0)
        p.reg_tau4s_on_modified( self._controller_data_changed_)
        p = pandora.BoxMonitored( id="gui.u(t)", label="u(2)", dim="", value=0.0)
        p.reg_tau4s_on_modified( self._controller_data_changed_)

        ##  Algorithmen erzeugen für die anschließenden Tests
        #
        algorithms = []
#        algorithm = EulerBw4gPIDT1p()
#        algorithms.append( algorithm)
        algorithms.append( EulerBw4P( id=id, p_Kp=p_Kp, p_Ts=p_Ts, p_e=p_e, p_u=p_u))
        algorithms.append( EulerBw4PDT1( id=-1, p_Kp=p_Kp, p_Kd=p_Kd, p_alpha=p_alpha, p_e=p_e, p_u=p_u, p_Ts=p_Ts))
        algorithms.append( EulerBw4PIDT1( id=id, p_Kp=p_Kp, p_Ki=pandora.Box( value=0.0), p_Kd=p_Kd, p_alpha=p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_u))
        algorithms.append( EulerBw4PIDT1p( id=-1, p_Kp=p_Kp, p_Ki=pandora.Box( value=0.0), p_Kd=p_Kd, p_alpha=p_alpha, p_e=p_e, p_u=p_u, p_Ts=p_Ts))
        algorithms.append( EulerBw4PIDT1( id=id, p_Kp=p_Kp, p_Ki=p_Ki, p_Kd=p_Kd, p_alpha=p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_u))
        algorithms.append( EulerBw4PIDT1p( id=-1, p_Kp=p_Kp, p_Ki=p_Ki, p_Kd=p_Kd, p_alpha=p_alpha, p_e=p_e, p_u=p_u, p_Ts=p_Ts))

        from matplotlib.backends.backend_pdf import PdfPages
        pdfpages = PdfPages( "NodePrinter-printed_figures.pdf")
        for algorithm in algorithms:

            controller = SISOController.New(
                (
                    NodeSummingPoint( p_w, p_y, p_e),
                    NodeAlgorithm( algorithm=algorithm),
                    NodeActuator( p_u),
                    NodePublisher( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u),
                    NodePrinter( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts, algorithm=algorithm, pdfpages=pdfpages)
                ),
                p_Ts
            )

            controller.to_on()
                                            # Controller ist READY
            controller.to_running()
                                            # Controller läuft
            rectangle = Signals.RECTANGLE( 100, 0.1)
            for i in range( 1000):
                p_w.value( rectangle( i*p_Ts.value()))
                controller.execute()
                print( "Runtime consumption = %.3f ms. " % (controller.runtime() * 1000))

            controller.to_ready()
                                            # Controller ist wieder nur READY
            controller.to_off()

        pdfpages.close()
        return

    def _controller_data_changed_( self, pc):
        print( "Controller data has changed: %s." % pc.client().id())


_Testsuite = unittest.makeSuite( _TESTCASE__SISOController)


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


def _lab_():
    return


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


if __name__ == '__main__':
    _Test_()
    _lab_()
    input( u"Press any key to exit...")



