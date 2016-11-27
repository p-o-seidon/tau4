#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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


from __future__ import division

import logging; _Logger = logging.getLogger()

from matplotlib import pyplot
import math
import tau4
from tau4.ce import EulerBw4P, EulerBw4PDT1, EulerBw4PIDT1, EulerBw4PIDT1p, EulerBw4gPIDT1p
from tau4.automation import Node4C, SISOController
from tau4.data import flex
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

    def __init__( self, fv_w, fv_y, fv_e):
        super().__init__()
        
        self.__fv_w = fv_w
        self.__fv_y = fv_y
        self.__fv_e = fv_e
        return
        
    def configure( self, fv_Ts):
        pass
    
    def execute( self):
        print( self.__class__.__name__ + ": Read current value. ")
        self.__fv_y.value( self._read_y_())
                                        # Istwert von Hardware lesen.
        print( self.__class__.__name__ + ": Cal. control difference. ")
        self.__fv_e.value( self.__fv_w.value() - self.__fv_y.value())
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
    
    def configure( self, fv_Ts):
        self.__algorithm.configure( fv_Ts)
        
        super().configure( fv_Ts)
        return self
        
    def execute( self):
        print( self.__class__.__name__ + ": Exec. control law. ")
        if self.is_running():
            if self.__algorithm:
                self.__algorithm.execute()
            
        super().execute()
        return self
        
        
class NodeActuator(Node4C):

    def __init__( self, fv_u):
        super().__init__()
        
        self.__fv_u = fv_u
        return
        
    def configure( self, fv_Ts):
        pass
    
    def execute( self):
        print( self.__class__.__name__ + ": Write actuation signal to plant. ")
        self._write_u_( self.__fv_u.value())

        super().execute()
        return self
        
    def _write_u_( self, u):
        return self
    
        
class NodePublisher(Node4C):

    def __init__( self, *, fv_w, fv_y, fv_e, fv_u):
        super().__init__()

        self.__fv_w = fv_w
        self.__fv_y = fv_y
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        return
        
    def configure( self, fv_Ts):
        pass
    
    def execute( self):
        print( self.__class__.__name__ + ": Publish data. ")
        flex.Variable.Instance( "gui.w(t)").value( self.__fv_w.value())
        flex.Variable.Instance( "gui.y(t)").value( self.__fv_y.value())
        flex.Variable.Instance( "gui.e(t)").value( self.__fv_e.value())
        flex.Variable.Instance( "gui.u(t)").value( self.__fv_u.value())

        super().execute()
        return self
        

class NodePrinter(Node4C):
    
    def __init__( self, *, fv_w, fv_y, fv_e, fv_u, fv_Ts, algorithm, pdfpages):
        super().__init__()

        self.__fv_w = fv_w
        self.__fv_y = fv_y
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        self.__fv_Ts = fv_Ts
        
        self.__algorithm = algorithm
        self.__pdfpages = pdfpages
        
        self.__i = 0
        self.__t_ = []
        self.__w_ = []
        self.__y_ = []
        self.__e_ = []
        self.__u_ = []
        
        return
        
    def configure( self, fv_Ts):
        pass
    
    def execute( self):
        """Ausgabe in Files mit pylab.
        """
        self.__t_.append( self.__i * self.__fv_Ts.value())
        self.__w_.append( self.__fv_w.value())
        self.__y_.append( self.__fv_y.value())
        self.__e_.append( self.__fv_e.value())
        self.__u_.append( self.__fv_u.value())
        
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
        fv_Kp = flex.Variable( value=1.0) 
        fv_Ki = flex.Variable( value=1.0) 
        fv_Kd = flex.Variable( value=1.0) 
        fv_alpha = flex.Variable( value=0.7) 
        
        ##  Variable holen, über die die Nodes zusammenhängen und mit 
        #   denen sie arbeiten.
        #
        fv_w = flex.Variable( value=100.0)
        fv_y = flex.Variable( value=0.0)
        fv_e = flex.Variable( value=0.0)
        fv_u = flex.VariableMo( id=-1, value=0.0, value_min=-400, value_max=400)
                                        # fv_u als VariableMo def'en, damit 
                                        #   Sättigung entdeckt werden kann.
                                        #   Die  B e r e i c h s g r e n z e n  
                                        #   m ü s s e n   mit dem Aktuator-Knoten 
                                        #   a b g e s t i m m t   werden!
        fv_Ts = flex.VariableDeClMoPe( id="controller.Ts", label="Ts", dim="s", value=0.010, value_min=0.001, value_max=None)
        
        ##  Variable fürs GUI holen
        #
        fv = flex.VariableDeClMo( id="gui.w(t)", label="u(2)", dim="", value=0.0, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        fv.reg_tau4s_on_modified( self._controller_data_changed_)
        fv = flex.VariableDeClMo( id="gui.y(t)", label="u(2)", dim="", value=0.0, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        fv.reg_tau4s_on_modified( self._controller_data_changed_)
        fv = flex.VariableDeClMo( id="gui.e(t)", label="u(2)", dim="", value=0.0, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        fv.reg_tau4s_on_modified( self._controller_data_changed_)
        fv = flex.VariableDeClMo( id="gui.u(t)", label="u(2)", dim="", value=0.0, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        fv.reg_tau4s_on_modified( self._controller_data_changed_)

        ##  Algorithmen erzeugen für die anschließenden Tests
        #
        algorithms = []
#        algorithm = EulerBw4gPIDT1p()
#        algorithms.append( algorithm)
        algorithms.append( EulerBw4P( id=id, fv_Kp=fv_Kp, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u))
        algorithms.append( EulerBw4PDT1( id=-1, fv_Kp=fv_Kp, fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_e=fv_e, fv_u=fv_u, fv_Ts=fv_Ts))
        algorithms.append( EulerBw4PIDT1( id=id, fv_Kp=fv_Kp, fv_Ki=flex.Variable( value=0.0), fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u))
        algorithms.append( EulerBw4PIDT1p( id=-1, fv_Kp=fv_Kp, fv_Ki=flex.Variable( value=0.0), fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_e=fv_e, fv_u=fv_u, fv_Ts=fv_Ts))
        algorithms.append( EulerBw4PIDT1( id=id, fv_Kp=fv_Kp, fv_Ki=fv_Ki, fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u))
        algorithms.append( EulerBw4PIDT1p( id=-1, fv_Kp=fv_Kp, fv_Ki=fv_Ki, fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_e=fv_e, fv_u=fv_u, fv_Ts=fv_Ts))

        from matplotlib.backends.backend_pdf import PdfPages        
        pdfpages = PdfPages( "NodePrinter-printed_figures.pdf")
        for algorithm in algorithms:

            controller = SISOController.New( 
                (
                    NodeSummingPoint( fv_w, fv_y, fv_e),
                    NodeAlgorithm( algorithm=algorithm),
                    NodeActuator( fv_u),
                    NodePublisher( fv_w=fv_w, fv_y=fv_y, fv_e=fv_e, fv_u=fv_u),
                    NodePrinter( fv_w=fv_w, fv_y=fv_y, fv_e=fv_e, fv_u=fv_u, fv_Ts=fv_Ts, algorithm=algorithm, pdfpages=pdfpages)
                ),
                fv_Ts
            )
                    
            controller.to_on()
                                            # Controller ist READY
            controller.to_running()
                                            # Controller läuft
            rectangle = Signals.RECTANGLE( 100, 0.1)
            for i in range( 1000):
                fv_w.value( rectangle( i*fv_Ts.value()))
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



