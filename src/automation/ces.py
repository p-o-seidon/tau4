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


import logging; _Logger = logging.getLogger()

import abc, time

from tau4.data import flex
from tau4.io.hal import HAL4IOs
from tau4.sweng import overrides, PublisherChannel
from tau4.threads import Cycler


class Node4C(metaclass=abc.ABCMeta):
    
    """
    
    .. note::
        Es ist die Frage, ob ein _Node einen Eingang und einen Ausgang braucht,
        denn das kann mit den Variablen erledigt werden, von denen gelesen und 
        auf die geschrieben wird und die ja dem Ctor übergeben werden. 
        Schließlich sind alle Subclasses von _Node appspez. und damit weiß die 
        App, wie die Nodes über welche Variablen zusammenhängen müssen.
    """

    def __init__( self):
        self.__node_next = None
        self.__is_on = False
        self.__is_running = False
        return
    
    @abc.abstractmethod
    def configure( self, fv_Ts):
        """Konfigurieren des Nodes.
        
        Beispielsweise wird der Algorithmus hier die Koeffizienten der 
        Differenzengleichung berechnen wollen.
       
        .. caution::
            Diese Methode muss am Ende von configure() jeder abgeleiteten Klasse 
            aufgerufen werden - **zwingend**!
           
        :param  FlexVarblLL fv_Ts:  Abtastzeit.
        """
        if self.__node_next:
            self.__node_next.configure( fv_Ts)
            
        return self
    
    @abc.abstractmethod
    def execute( self):
        """Ausführen des Nodes.
        
        .. caution::
            Diese Methode muss am Ende von execute() jeder abgeleiteten Klasse 
            aufgerufen werden - **zwingend**!
        """
        if self.__node_next:
            self.__node_next.execute()
            
        return self
    
    def is_on( self):
        """Es werden nur von der Hardware eingelesene Werte angezeigt, der Algorithmus wird nicht ausgeführt.
       """
        return self.__is_on
    
    def is_ready( self):
        """Es werden nur von der Hardware eingelesene Werte angezeigt, der Algorithmus wird nicht ausgeführt.
        """
        return self.__is_on and not self.__is_running
    
    def is_running( self):
        """Es werden nur von der Hardware eingelesene sowie berechnete Werte angezeigt, **der Algorithmus wird also ausgeführt**.
       """
        return self.__is_running
    
    def node_last( self):
        """Liefert den letzten Node der Kette, zu der dieser Node gehört.
        """
        node = self
        while node:
            if not node.node_next():
                return node
            
            node = node.node_next()
            
        return None
                
    def node_next( self, node=None):
        """Next node in the linked list.
        """
        if node is None:
            return self.__node_next
        
        self.__node_next = node
        return self
    
    def to_off( self):
        """Switch OFF Node.
        """
        self.__is_on = False
        if self.__node_next:
            self.__node_next.to_off()

        return
    
    def to_on( self):
        """Switch ON Node.
        """
        self.__is_on = True
        if self.__node_next:
            self.__node_next.to_on()

        return
        
    def to_ready( self):
        """Switch from RUNNING to READY.
        """
        self.__is_running = False
        if self.__node_next:
            self.__node_next.to_ready()

        return
    
    def to_running( self):
        """Switch to RUNNING.
        
        Node must be ON already.
        """
        if self.is_on():
            self.__is_running = True
            
        if self.__node_next:
            self.__node_next.to_running()

        return
    
    
class NodeReconfigurator(Node4C):
    
    """Konfigurations-Node. 
    
    Er veranlasst z.B. die Neu/berechnung der 
    Koeffizenten der Differenzengleichung.
    
    Mit diesem Knoten beginnt die Linked List, die den Regler ausmacht, 
    **automatsich**, d.h. dieser Node muss vom User nicht eingehängt werden.
    """

    def __init__( self, fv_Ts):
        super().__init__()
        fv_Ts.reg_tau4s_on_modified( self._tau4s_on_Ts_modified_)
        self.__is_dirty = True
                                        # Bei Erstausführung muss auf 
                                        #   jeden Fall eine Konfiguration 
                                        #   erfolgen.
        self.__fv_Ts = fv_Ts
        return

    def configure( self, fv_Ts):
        if self.__is_dirty:
            self.__is_dirty = False
            super().configure( self.__fv_Ts)

        return self
            
        
    def execute( self):
        self.configure( self.__fv_Ts)

        super().execute()
        return self
        
    def _tau4s_on_Ts_modified_( self, tau4pc):
        self.__Ts = tau4pc.client().fv_Ts.value()
        self.__is_dirty = True
        return self
        

class SISOController:
    
    """Container für die Nodes, aus denen der Regler besteht.
    
    Im folgenden ein Beispiel, wie die Konstruktion eines Reglers aussehen kann.
    
    Usage::
    
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
            
    .. todo::
        Controller von :py:class:`Node4C` ableiten?
    """
    
    @staticmethod
    def New( nodes, fv_Ts):
        node1 = NodeReconfigurator( fv_Ts)
                                        # Konfigurations-Node. Er veranlasst z.B. die Neu/berechnung der 
                                        #   Koeffizenten der Differenzengleichung.
                                        #   
                                        #   Mit diesem Knoten begint die Linked List, die den Regler ausmacht.
                                        #
        for node in nodes:
            node1.node_last().node_next( node)
        
        controller = SISOController( node1)
                                        # Es fällt auf, dass dem Regler die 
                                        #   Abtastzeit nicht übergeben wird, die 
                                        #   für die Berechnung der Koeffizienten 
                                        #   der Differenzengleichung benötigt wird.
                                        #   Da diese Berechnung in der Methode
                                        #   configure() erfolgt, wird dort die 
                                        #   Abtastzeit und nur die Abtastzeit 
                                        #   übergeben.
        return controller
    
    def __init__( self, node1):
        self.__node1 = node1
        
        self.__is_on = False
        self.__is_ready = False
        
        self.__runtime = 0
        return
    
    def execute( self):
        """Regler ausführen.
        """
        dt = time.time()
        if self.__node1:
            self.__node1.execute()
            
        dt = time.time() - dt
        self.__runtime = dt
        return
        
    def is_on( self):
        """Es werden nur von der Hardware eingelesene Werte angezeigt, der Algorithmus wird nicht ausgeführt.
        """
        return self.__is_on
    
    def is_ready( self):
        """Es werden nur von der Hardware eingelesene Werte angezeigt, der Algorithmus wird nicht ausgeführt.
        """
        return self.__is_on and not self.__is_running
    
    def is_running( self):
        """Es werden nur von der Hardware eingelesene sowie berechnete Werte angezeigt, **der Algorithmus wird also ausgeführt**.
        """
        return self.__is_running
    
    def runtime( self):
        """Laufzeitbedarf für execute().
        """
        return self.__runtime
        
    def to_off( self):
        """Regler ausschalten. 
        """
        self.__is_on = False
        self.__node1.to_off()
        return
    
    def to_on( self):
        """Regler einschalten.
        
        Nodes müssen so implementiert werden, dass zwar keine Einflussnahme auf 
        die Strecke erfolgt, weiterhin aber Werte angezeigt werden können.
        """
        self.__is_on = True
        self.__node1.to_on()
        return
        
    def to_ready( self):
        """Regler von RUNNING auf READY schalten.
        
        Nodes müssen so implementiert werden, dass zwar keine Einflussnahme auf 
        die Strecke erfolgt, weiterhin aber Werte angezeigt werden können.
        """
        self.__is_running = False
        self.__node1.to_ready()
        return
    
    def to_running( self):
        """Regler auf RUNNING schalten.
        """
        if self.is_on():
            self.__is_running = True
            
        self.__node1.to_running()
        return
    
    