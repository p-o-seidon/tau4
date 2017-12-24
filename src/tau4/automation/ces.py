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


"""
###########################
Control Engineering Systems
###########################

This is about control engineering for automation projects. The algorithms needed
are defined in the package tau4.ce!

"""

import abc, time

from tau4.data import pandora
from tau4.oop import overrides, PublisherChannel
from tau4.threads import Cycler


class Node4C(metaclass=abc.ABCMeta):

    """Node for controller.

    A controller consists of nodes.

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
    def configure( self, p_Ts: pandora.Box):
        """Konfigurieren des Nodes.

        Beispielsweise wird der Algorithmus hier die Koeffizienten der
        Differenzengleichung berechnen wollen.

        .. caution::
            Diese Methode muss am Ende von configure() jeder abgeleiteten Klasse
            aufgerufen werden - **zwingend**!

        **Parameters**
            p_Ts : pandora : Box
                Sampling time.
        """
        if self.__node_next:
            self.__node_next.configure( p_Ts)

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

    def __init__( self, p_Ts):
        super().__init__()
        p_Ts.reg_tau4s_on_modified( self._tau4s_on_Ts_modified_)
        self.__is_dirty = True
                                        # Bei Erstausführung muss auf
                                        #   jeden Fall eine Konfiguration
                                        #   erfolgen.
        self.__p_Ts = p_Ts
        return

    def configure( self, p_Ts):
        if self.__is_dirty:
            self.__is_dirty = False
            super().configure( self.__p_Ts)

        return self


    def execute( self):
        self.configure( self.__p_Ts)

        super().execute()
        return self

    def _tau4s_on_Ts_modified_( self, tau4pc):
        self.__Ts = tau4pc.client().value()
        self.__is_dirty = True
        return self


class SISOController:

    """Container für die Nodes, aus denen der Regler besteht.

    Im folgenden ein Beispiel, wie die Konstruktion eines Reglers aussehen kann.

    **Usage**

        .. code-block:: Python

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
            p_u = pandora.BoxClippingMonitored( value=0.0, bounds=(-400, 400))
                                            # p_u als BoxClippingMonitored def'en, damit
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
            algorithms.append( EulerBw4P( id=id, p_Kp=p_Kp, p_Ts=p_Ts, p_e=p_e, p_u=p_u))
            algorithms.append( EulerBw4PDT1( id=-1, p_Kp=p_Kp, p_Kd=p_Kd, p_alpha=p_alpha, p_e=p_e, p_u=p_u, p_Ts=p_Ts))
            algorithms.append( EulerBw4PIDT1( id=id, p_Kp=p_Kp, p_Ki=flex.Variable( value=0.0), p_Kd=p_Kd, p_alpha=p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_u))
            algorithms.append( EulerBw4PIDT1p( id=-1, p_Kp=p_Kp, p_Ki=flex.Variable( value=0.0), p_Kd=p_Kd, p_alpha=p_alpha, p_e=p_e, p_u=p_u, p_Ts=p_Ts))
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

    .. todo::
        Controller von :py:class:`Node4C` ableiten?
    """

    class _SentinelNode(Node4C):

        def __init__( self, p_is_called):
            super().__init__()
            self.__p_is_called = p_is_called
            return

        def configure( self):
            pass

        def execute( self):
            self.__p_is_called.value( 1)

            super().execute()
            return

    @staticmethod
    def New( nodes, p_Ts):
        node1 = NodeReconfigurator( p_Ts)
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

        self.__p_is_sentinel_called = pandora.Box( value=0)
        self.__node1.node_last().node_next( self._SentinelNode( self.__p_is_sentinel_called))
        return

    def execute( self):
        """Regler ausführen.
        """
        dt = time.time()
        if self.__node1:
            self.__node1.execute()

        if not self.__p_is_sentinel_called.value():
            raise Exception( "You forgot to call super().execute() in one of your nodes' subclass execute()!")

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
        self.__is_running = False
        self.__node1.to_off()
        return

    def to_on( self):
        """Regler einschalten.

        Nodes müssen so implementiert werden, dass zwar keine Einflussnahme auf
        die Strecke erfolgt, weiterhin aber Werte angezeigt werden können.
        """
        self.__is_on = True
        self.__is_running = False
        self.__node1.to_on()
        return

    def to_ready( self):
        """Regler von RUNNING auf READY (ENABLED) schalten.

        Nodes müssen so implementiert werden, dass zwar keine Einflussnahme auf
        die Strecke erfolgt, weiterhin aber Werte angezeigt werden können.

        \_2DO
            Wozu diese Methode? Sei macht, was to_on() schon macht.
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


