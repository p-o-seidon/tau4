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

"""\package mobile2 Alles für die Realisierung mobiler Roboter: Controllers.

\par    Diary
-   2017-11-28: Erstellt. Noch nicht einsatzbereit!

"""

import abc
from math import atan2, degrees, pi

from tau4 import Object, ThisName
from tau4.automation import ces
from tau4.data import pandora
from tau4.datalogging import UsrEventLog
from tau4 import ce
from tau4.ce import eulerbw
from tau4.dsp.filters import MovingAverageFilter
from tau4 import iios3
from tau4.ios2 import MotorDriver, MotorEncoder
from tau4.mathe.linalg import T3D
from tau4.multitasking import threads as mtt
from tau4.robotix.mobile2.rovers import StandardGoal, StandardRover


_USE_THREADED_CONTROLLERS = True


class DriveController(Object, abc.ABC):

    """Antriebsregler für je einen Motor.

    Diese Klasse gibt's "normal" und "threaded". Um in der App de entsprechende
    Wahl treffen zu können, sind die beiden Klassen DriveController und
    ThreadedDriveController von der APp abzuleiten und dort dann eine statische
    Methode

    \code{.py}
        @staticmethod
        def New( rover: StandardRover, p_Ts: pandora.Box):
            if not _USE_THREADED_CONTROLLERS:
                return TheAppsDriveController( rover, p_Ts)

            return TheAppsThreadedDriveController( rover, p_Ts)
    \endcode

    zu definieren und zu verwenden.
    """

    class NodePublisher(ces.Node4C):

        """Publishing der Signalwerte des Reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

        \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
        \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
        \param  p_e     Regelabweichung, s. NodeSummingPoint.
        \param  p_u     Stellgröße, s. NodeActuator.
        \param  p_Ts    Abtastzeit.
        """

        def __init__( self, *, p_w, p_y, p_e, p_u, p_Ts):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            self.__p_u = p_u
            self.__p_Ts = p_Ts
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            ### Abkürzungen
            #
            w = self.__p_w.value()
            y = self.__p_y.value()
            e = self.__p_e.value()
            u = self.__p_u.value()
            Ts = self.__p_Ts.value()

            ### Publishing
            #
            self.publish_values( w, y, e, u, Ts)

            ### Base Class ausführen
            #
            super().execute()
            return self

        @abc.abstractmethod
        def publish_values( self, w: float, y: float, e: float, u: float, Ts: float):
            pass


    class NodeSummingPoint(ces.Node4C):

        def __init__( self, *, p_w, p_y, p_e):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            """Bildet Differenz e = w - y.
            """
            self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                            # e = w - y
            super().execute()
            return self

        def _read_y_( self):
            """Hier ein Dummy.
            """
            return 0


    class NodeUWriter(ces.Node4C):

        """Schreibt auf den Motor einen Geschwindigkeitswert in %.
        """

        def __init__( self, p_u, motordriver: MotorDriver):
            super().__init__()

            self.__p_u = p_u
            self.__motordriver = motordriver
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            """Ausführen: Schreibt v auf den Motor.
            """
            #self.__p_u.value( -self.__p_u.value())

            self._write_u_( self.__p_u.value())

            super().execute()
            return self

        def _write_u_( self, u):
            """Schreibt v in % auf den Motor.
            """
            _names = ( "DriveController", self.__class__.__name__, "_write_u_")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            if self.is_running():
                self.__motordriver.speed_100( u)

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return self


    class NodeWReader(ces.Node4C):

        """Sollwert.

        \note
            Abstimmung mit NodeYReader!
        """

        _GOAL_IN_X_DIRECTION = True
        _GOAL_IN_Y_DIRECTION = not _GOAL_IN_X_DIRECTION

        def __init__( self, p_w):
            super().__init__()

            if self._GOAL_IN_Y_DIRECTION:
                p_w.value( pi/2)
                                                # Goal muss in Y-Richtung liegen.
            else:
                p_w.value( 0)
                                                # Goal muss in X-Richtung liegen,
                                                #   weil wir das CS in
                                                #   NodeYReader um 90° gedreht haben.
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            super().execute()
            return


    class NodeYReader(ces.Node4C):

        """Istwert.

        \param  p_y
            Istwert als Ausgangsparameter dieser Methode, das heißt hier wird
            der Istwert gelesen udn auf p_y geschrieben.
        """
        def __init__( self, p_y: pandora.Box, motorencoder: MotorEncoder):
            super().__init__()

            self.__p_y = p_y
            self.__motorencoder = motorencoder
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            """Berechnet den Istwert.

            \note
                Abstimmung mit NodeWReader!
            """
            _names = ( "DriveController", self.__class__.__name__, "execute")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            self.__p_y.value( self.__motorencoder.encoderticks_per_second())

            super().execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return


    class NodeYReaderFiltering(ces.Node4C):

        """Istwert.
        """
        def __init__( self, p_y : pandora.BoxMonitored, p_y_filtered, motorencoder: MotorEncoder):
            super().__init__()

            self.__filter = MovingAverageFilter( None, "", "", 3)

            self.__p_y = p_y
            self.__p_y_filtered = p_y_filtered
            self.__p_y.reg_tau4s_on_modified( self._tau4s_on_y_modified_)
            self.__motorencoder = motorencoder
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            _names = ( "DriveController", self.__class__.__name__, "execute")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            self.__p_y.value( self.__motorencoder.encoderticks_per_second())
                                            # Führt durch Beschreiben der Box den
                                            #   Filter aus: self._tau4s_on_y_modified_().
            self.__p_y_filtered = self.__filter.value()

            super().execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return

        def _tau4s_on_y_modified_( self, tau4pc):
            _names = ( "GoalDirectionController", self.__class__.__name__, "_tau4s_on_y_modified_")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            self.__filter.value( tau4pc.cient().value())
            self.__filter.execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return


    def __init__( self, *, motorencoder: MotorEncoder, motordriver: MotorDriver, p_Ts: pandora.Box):
        Object.__init__( self, id=self.__class__.__name__)

        ###
        #
        self.__motorencoder = motorencoder
        self.__motordriver = motordriver

        ### Regler
        #
        #   Wir müssen mit hohen Verstärkungen arbeiten, weil die Stellgröße
        #   in % ausgegeben wird. Eine Abweichung von alpha = 1 rad/s = 57.3°/s
        #   ergibt eine regelabweichug von 1 und bei einem Kp = 1 eine Stellgröße
        #   von nur u = 1%!
        #
        self.__controller = ces.SISOController.New( self.nodes(), p_Ts)

        return

    def execute( self):
        self.__controller.execute()
        return

    def _node_algorithm_( self, id, p_Ts, p_e, p_u):
        """Liefert einen fertig konfigurierten Algo-Node.
        """
        if id == "pi":
            self.__p_Kp = pandora.Box( value=10.0)
            self.__p_Ki = pandora.Box( value=0.5)
            algo = NodeAlgorithm( algorithm=ce.EulerBw4PI( id="drivecontroller.algorithm", p_Kp=self.__p_Kp, p_Ki=self.__p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_u))

        elif id == "dt1":
            self.__p_K = pandora.Box( value=10.0)
            self.__p_T = pandora.Box( value=0.1)
            self.__p_alpha = pandora.Box( value=0.5)
            algo = NodeAlgorithm( algorithm=eulerbw.Lead( id="drivecontroller.algorithm", p_K=self.__p_K, p_T=self.__p_T, p_alpha=self.__p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_u))

        else:
            raise ValueError( "Unknown algorithm id = '%s'. " % id)

        return algo

    @abc.abstractmethod
    def nodes( self):
        """Liefert alle Nodes.

        Mögliches Implementierungen:
            \code{.py}
                def nodes( self):
                    nodes = (\
                        self.NodeWReader( p_w),
                        self.NodeYReader( p_y, motorencoder),
                        self.NodeSummingPoint( p_w=p_w, p_y=p_y, p_e=p_e),
                        self._node_algorithm_( "dt1", p_Ts, p_e, p_u),
                        self.NodeUWriter( p_u, motordriver),
                        self.NodePublisher( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts),
                    )
                    return nodes
            \encode
        """
        pass

    def to_on( self):
        #_names = ( self.__class__.__name__, "to_on")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_on()
        return self

    def to_off( self):
        #_names = ( self.__class__.__name__, "to_off")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_off()
        return self

    def to_ready( self):
        #_names = ( self.__class__.__name__, "to_ready")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_ready()
        return self

    def to_running( self):
        #_names = ( self.__class__.__name__, "to_rnning")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_running()
        return self


class GoalDirectionController(Object):

    """Regelt Fahrtrichtung in Richtung Goal.

    \param  robot

    \param  goal

    \param  p_Ts
        Abtastzeit.

    Die Reglerparameter werden im Ctor definiert.
    Es muss mit hohen Verstärkungen gearbeitet werden, weil die Stellgröße
    in % ausgegeben wird. Eine Abweichung von alpha = 1 rad/s = 57.3°/s
    ergibt eine regelabweichug von 1 und bei einem Kp = 1 eine Stellgröße
    von nur u = 1%!

    \warning
        Nicht direkt instanzieren sondern über GolaDirectionController.New()!
    """

    @staticmethod
    def New( rover: StandardRover, goal: StandardGoal, p_Ts: pandora.Box):
        """Ctor - direkte Instanzierung vermeiden: Normalen Regler oder threded Regler erzeugen.
        """
        if not _USE_THREADED_CONTROLLERS:
            return GoalDirectionController( rover=rover, goal=goal, p_Ts=p_Ts)

        return ThreadedGoalDirectionController( rover, goal, p_Ts)


    class NodePublisher(ces.Node4C):

        """Publishing der Signalwerte des Reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

        \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
        \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
        \param  p_e     Regelabweichung, s. NodeSummingPoint.
        \param  p_u     Stellgröße, s. NodeActuator.
        \param  p_Ts    Abtastzeit.
        """

        def __init__( self, *, p_w, p_y, p_e, p_u, p_Ts):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            self.__p_u = p_u
            self.__p_Ts = p_Ts
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            ### Abkürzungen
            #
            w = self.__p_w.value()
            y = self.__p_y.value()
            e = self.__p_e.value()
            u = self.__p_u.value()
            Ts = self.__p_Ts.value()

            ### Publishing
            #
            self.publish_values( w, y, e, u, Ts)

            ### Base Class ausführen
            #
            super().execute()
            return self

        @abc.abstractmethod
        def publish_values( self, w: float, y: float, e: float, u: float, Ts: float):
            pass


    class NodeSummingPoint(ces.Node4C):

        def __init__( self, *, p_w, p_y, p_e):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            """Bildet Differenz e = w - y.
            """
            self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                            # e = w - y
            super().execute()
            return self

        def _read_y_( self):
            """Hier ein Dummy.
            """
            return 0


    class NodeUWriter(ces.Node4C):

        """Schreibt aufs Fahrwerk: Positive Werte von u(t) bedeuten 'Fahren nach links', negative Werte von u(t) bedeuten 'Fahren nach rechts'.
        """

        def __init__( self, p_u, rover: StandardRover):
            super().__init__()

            self.__p_u = p_u
            self.__rover = rover
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            """Ausführen: Schreibt v und omega aufs Chassis.

            Ist e > 0, ist alpha < pi/2 zu klein. Wir müssen uns also mehr nach
            rechts drehen, was aber omega < 0 heißt. Hier ist also ein
            Vorzeichendreher nötig.
            """
            self.__p_u.value( -self.__p_u.value())

            self._write_u_( self.__p_u.value())

            super().execute()
            return self

        def _write_u_( self, u):
            """Schreibt v und omega in die IO-Buffers.
            """
            _names = ( "GoalDirectionController", self.__class__.__name__, "_write_u_")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            if self.is_running():
                v_100, omega_100 = self.__rover.body().uck_100()
                omega_100 = u
                #_Logger.debug( "%s.%s.%s(): omega_100 = %.3f %%/s.", *_names, omega_100)
                self.__rover.body().uck_100( v_100=v_100, omega_100=omega_100)
                self.__rover.body().execute()
                                                # Schreibt die berechneten Werte auf die IO-Buffers.
            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return self


    class NodeWReader(ces.Node4C):

        """Sollwert.

        \note
            Abstimmung mit NodeYReader!
        """

        _GOAL_IN_X_DIRECTION = True
        _GOAL_IN_Y_DIRECTION = not _GOAL_IN_X_DIRECTION

        def __init__( self, p_w):
            super().__init__()

            if self._GOAL_IN_Y_DIRECTION:
                p_w.value( pi/2)
                                                # Goal muss in Y-Richtung liegen.
            else:
                p_w.value( 0)
                                                # Goal muss in X-Richtung liegen,
                                                #   weil wir das CS in
                                                #   NodeYReader um 90° gedreht haben.
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            super().execute()
            return


    class NodeYReader(ces.Node4C):

        """Istwert.

        \param  p_y
            Istwert, wird von diesem Node berechnet (ist also AUsgangsparameter).

        \param  rover
            Rover, der eine Hierarchie realisiert. Diese Hierarchy liefert den
            Orietierungswinkel \c alpha relativ BASE.

        \param  goal
            Goal. Goal liefert seine Position relativ BASE. Somit kann zusammen
            mit \c rover eine Wineldifferent berechnet werden (die Null werden muss).
        """
        def __init__( self, p_y: pandora.Box, rover: StandardRover, goal: StandardGoal):
            super().__init__()

            self.__p_y = p_y
            self.__rover = rover
            self.__roverbody = rover.body()
            self.__goal = goal

            self.__p_Ts = None
            return

        def configure( self, p_Ts):
            self.__p_Ts = p_Ts
            return

        def execute( self):
            """Berechnet den Istwert: Richtung des {GOAL} in {ROBOT}.

            Dabei wird angenommen, dass die X-Achse von {ROBOT} in Fahrtrichtung zeigt!

            \note
                Abstimmung mit NodeWReader!
            """
            _names = ( "GoalDirectionController", self.__class__.__name__, "execute")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            assert self.__roverbody.positionsensor().conversiondelay() <= self.__p_Ts.value()

            bTr = self.__roverbody.positionsensor().bT()
                                            # {ROBOT} in {BASE}.
            bTg = self.__goal.bT()
                                            # {GOAL} in {BASE}
            #_Logger.debug( "%s.%s.%s(): bTg = %s", *_names, bTg)
            rTg = bTr.inverted() * bTg
                                            # {GOAL} in {ROBOT}
            #_Logger.debug( "%s.%s.%s.(): rTg = %s", *_names, rTg)
            P = rTg.P()
                                            # Die "Richtung" des {GOALS} relativ {ROBOT}.
            alpha = atan2( P.y(), P.x())
                                            # Der Winkel zur "Richtung".
            self.__p_y.value( alpha)
                                            # Der Winkel ist der Istwert.
            #_Logger.debug( "%s.%s.%s(): Robot position bPr = %s.", *_names, bTr.P())
            #_Logger.debug( "%s.%s.%s(): Robot direction angle bAr = %.3f°.", *_names, degrees( self.__robot.bA()))
            #_Logger.debug( "%s.%s.%s(): Goal position bPg = %s.", *_names, bTg.P())
            #_Logger.debug( "%s.%s.%s(): Goal position rPg = %s.", *_names, P)
            #_Logger.debug( "%s.%s.%s(): Goal direction angle rAg = %.3f°.", *_names, degrees( alpha))

            super().execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return


    class NodeYReaderFiltering(ces.Node4C):

        """Istwert.
        """
        def __init__( self, p_y: pandora.Box, p_y_filtered: pandora.Box, rover: StandardRover, goal: StandardGoal):
            super().__init__()

            self.__filter = MovingAverageFilter( None, "", "", 3)

            self.__p_y = p_y
            self.__p_y_filtered = p_y_filtered
            self.__p_y.reg_tau4s_on_modified( self._tau4s_on_y_modified_)
            self.__rover = rover
            self.__goal = goal
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            _names = ( "GoalDirectionController", self.__class__.__name__, "execute")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            bTr = self.__rover.brain().bT()
                                            # {ROBOT} relativ {BASE}
            bTg = self.__goal.bT()
                                            # {GOAL} relativ {BASE}
            rTg = bTr.inverted() * bTg
                                            # {GOAL} relativ {ROBOT}
            P = rTg.P()
            alpha = atan2( P.y(), P.x())
            #_Logger.debug( "%s.%s.%s(): alpha = %.3f°", *_names, degrees( alpha))
            self.__p_y.value( alpha)
                                            # Führt durch Beschreiben der Box den
                                            #   Filter aus: self._tau4s_on_y_modified_().
            self.__p_y_filtered = self.__filter.value()

            super().execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return

        def _tau4s_on_y_modified_( self, tau4pc):
            _names = ( "GoalDirectionController", self.__class__.__name__, "_tau4s_on_y_modified_")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            self.__filter.value( tau4pc.cient().value())
            self.__filter.execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return


    def __init__( self, *, rover: StandardRover, goal: StandardGoal, p_Ts: pandora.Box):
        Object.__init__( self, id=self.__class__.__name__)

        ### Transformationen, aus denen die Regelabweichung gebildet wird
        #
        self.__bTr = rover.brain().bT()
        self.__bTg = goal.bT()

        ### Chassis, d.i. die Strecke
        #
        self.__rover = rover

        ### Signale zum Rechnen
        #
        p_w = pandora.Box( value=0.0)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.BoxClippingMonitored( value=0.0)
        p_y = pandora.Box( value=0.0)
        p_y_filtered = pandora.BoxMonitored( value=0.0)

        ### Regler
        #
        #   Wir müssen mit hohen Verstärkungen arbeiten, weil die Stellgröße
        #   in % ausgegeben wird. Eine Abweichung von alpha = 1 rad/s = 57.3°/s
        #   ergibt eine regelabweichug von 1 und bei einem Kp = 1 eine Stellgröße
        #   von nur u = 1%!
        #
        nodes = (\
            self.NodeWReader( p_w),
            self.NodeYReader( p_y, rover, goal),
            self.NodeSummingPoint( p_w=p_w, p_y=p_y, p_e=p_e),
            self._node_algorithm_( "dt1", p_Ts, p_e, p_u),
            self.NodeUWriter( p_u, rover),
            self.NodePublisher( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts),
        )
        self.__controller = ces.SISOController.New( nodes, p_Ts)

        return

    def _node_algorithm_( self, id, p_Ts, p_e, p_u):
        """Liefert einen fertig konfigurierten Algo-Node.
        """
        if id == "pi":
            self.__p_Kp = pandora.Box( value=10.0)
            self.__p_Ki = pandora.Box( value=0.5)
            algo = NodeAlgorithm( algorithm=ce.EulerBw4PI( id="directioncontroller.algorithm", p_Kp=self.__p_Kp, p_Ki=self.__p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_u))

        elif id == "dt1":
            self.__p_K = pandora.Box( value=10.0)
            self.__p_T = pandora.Box( value=0.1)
            self.__p_alpha = pandora.Box( value=0.5)
            algo = NodeAlgorithm( algorithm=eulerbw.Lead( id="directioncontroller.algorithm", p_K=self.__p_K, p_T=self.__p_T, p_alpha=self.__p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_u))

        else:
            raise ValueError( "Unknown algorithm id = '%s'. " % id)

        return algo

    def execute( self):
        self.__controller.execute()
        return

    def to_on( self):
        _names = ( self.__class__.__name__, "to_on")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_on()
        return self

    def to_off( self):
        _names = ( self.__class__.__name__, "to_off")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_off()
        return self

    def to_ready( self):
        _names = ( self.__class__.__name__, "to_ready")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_ready()
        return self

    def to_running( self):
        _names = ( self.__class__.__name__, "to_rnning")
        #_Logger.info( "%s.%s(). ", *_names)

        self.__controller.to_running()
        return self


class GoalDistanceController(Object):

    """Regelt die Fahrgeschwinndigkeit in Abhängigkeit der Distanz zum Goal.

    \param  robot

    \param  goal

    \param  p_Ts
        Abtastzeit.

    \warning
        Nicht direkt instanzieren sondern über GolaDirectionController.New()!
    """

    @staticmethod
    def New( rover: StandardRover, goal: StandardGoal, p_Ts: pandora.Box, p_is_goal_reached: pandora.Box):
        """Ctor - direkte Instanzierung vermeiden!
        """
        if not _USE_THREADED_CONTROLLERS:
            return GoalDistanceController( rover=rover, goal=goal, p_Ts=p_Ts, p_is_goal_reached=p_is_goal_reached)

        return ThreadedGoalDistanceController( rover, goal, p_Ts, p_is_goal_reached)


    class NodePublisher(ces.Node4C):

        """Publishing der Signalwerte des reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

        \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
        \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
        \param  p_e     Regelabweichung, s. NodeSummingPoint.
        \param  p_u     Stellgröße, s. NodeActuator.
        \param  p_Ts    Abtastzeit.
        """

        def __init__( self, *, id_controller, p_w, p_y, p_e, p_u, p_Ts):
            super().__init__()

            self.__id_controller = id_controller

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            self.__p_u = p_u
            self.__p_Ts = p_Ts
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            ### Abkürzungen
            #
            w = self.__p_w.value()
            y = self.__p_y.value()
            e = self.__p_e.value()
            u = self.__p_u.value()
            Ts = self.__p_Ts.value()

            ### Publishing DEPRECATED
            #
            pandora.Shelf().box( "gui.goaldistancecontroller.w(t)").value( w)
            pandora.Shelf().box( "gui.goaldistancecontroller.y(t)").value( y)
            pandora.Shelf().box( "gui.goaldistancecontroller.e(t)").value( e)
            pandora.Shelf().box( "gui.goaldistancecontroller.u(t)").value( u)
            pandora.Shelf().box( "gui.goaldistancecontroller.Ts").value( Ts)

            ### Publishing auf die Ausgänge
            #
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._GOALDISTANCECONTROLLER_W, w)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._GOALDISTANCECONTROLLER_Y, y)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._GOALDISTANCECONTROLLER_E, e)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._GOALDISTANCECONTROLLER_U, u)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._GOALDISTANCECONTROLLER_TS, Ts)

            ### Base Class ausführen
            #
            super().execute()
            return self


    class NodeStopCriterion(ces.Node4C):

        def __init__( self, *, p_e : pandora.Box, rover: StandardRover, p_is_goal_reached : pandora.Box):
            super().__init__()

            self.__p_e = p_e
            self.__rover = rover
            self.__p_is_goal_reached = p_is_goal_reached
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            if abs( self.__p_e.value()) <= self.__rover.body().perimeter().radius():
                self.__p_is_goal_reached.value( 1)
                UsrEventLog().log_warning( "Goal reached, p_e = '%.3f'.  " % self.__p_e.value(), ThisName( self))

            super().execute()
            return self


    class NodeSummingPoint(ces.Node4C):

        def __init__( self, p_w, p_y, p_e):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                            # e = w - y
            super().execute()
            return self

        def _read_y_( self):
            return 0


    class NodeUWriter(ces.Node4C):

        """Schreibt aufs Fahrwerk: Positive Werte von u(t) bedeuten 'Fahren nach links', negative Werte von u(t) bedeuten 'Fahren nach rechts'.
        """

        def __init__( self, p_u, rover: StandardRover):
            super().__init__()

            self.__p_u = p_u
            self.__rover = rover
            self.__roverbody = rover.body()
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_u.value( -self.__p_u.value())

            self._write_u_( self.__p_u.value())

            super().execute()
            return self

        def _write_u_( self, u):
            _names = ( "GoalDistanceController", self.__class__.__name__, "_write_u_")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            if self.is_running():
                v_100, omega_100 = self.__roverbody.uck_100()
                v_100 = u

                #_Logger.debug( "%s.%s.%s(): (v_100, omega_100) = (%.3f, %.3f).", *_names, v_100, omega_100)

                self.__roverbody.uck_100( v_100=v_100, omega_100=omega_100)

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return self


    class NodeWReader(ces.Node4C):

        """Sollwert.
        """
        def __init__( self, p_w):
            super().__init__()

            p_w.value( 0)
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            super().execute()
            return


    class NodeYReader(ces.Node4C):

        """Istwert.
        """

        def __init__( self, p_y, rover: StandardRover, goal: StandardGoal):
            super().__init__()

            self.__p_y = p_y
            self.__rover = rover
            self.__roverbody = rover.body()
            self.__roverbrain = rover.brain()
            self.__goal = goal
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            _names = ( "GoalDistanceController", self.__class__.__name__, "execute")
            #_Logger.debug( "%s.%s.%s(): E n t e r e d. ", *_names)

            bTr = self.__roverbody.bT( self.__roverbrain.wTb())
            bTg = self.__goal.bT()
            rTg = bTr.inverted() * bTg
            P = rTg.P()
            distance = P.magnitude()
            #_Logger.debug( "%s.%s.%s(): distance = %.3f m.", *_names, distance)
            self.__p_y.value( distance)

            super().execute()

            #_Logger.debug( "%s.%s.%s(): Exit now.\n", *_names)
            return


    def __init__( self, *, rover: StandardRover, goal: StandardGoal, p_Ts: pandora.Box, p_is_goal_reached: pandora.Box):
        Object.__init__( self, id=self.__class__.__name__)

        ### Transformartionen, aus denen die Regelabweichung gebildet wird
        #
        self.__bTr = rover.body().bT()
        self.__bTg = goal.bT()

        ### Chassis, d.i. die Strecke
        #
        self.__rover = rover

        ### Signale zum Rechnen
        #
        p_w = pandora.Box( value=0.0)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.Box( value=0.0)
        p_y = pandora.Box( value=0.0)

        ### Signale zum Anzeigen
        #
#        self.__p_w_published = pandora.BoxMonitored( id="gui.goaldistancecontroller.w(t)", value=0.0, label="w(t)", dim="m")
#        self.__p_e_published = pandora.BoxMonitored( id="gui.goaldistancecontroller.e(t)", value=0.0, label="e(t)", dim="m")
#        self.__p_u_published = pandora.BoxMonitored( id="gui.goaldistancecontroller.u(t)", value=0.0, label="u(t) = v_100", dim="%")
#        self.__p_y_published = pandora.BoxMonitored( id="gui.goaldistancecontroller.y(t)", value=0.0, label="y(t)", dim="m")
#        self.__p_Ts_published = pandora.BoxMonitored( id="gui.goaldistancecontroller.Ts", value=0.0, label="Ts", dim="s")

        ### Regler
        #
        self.__p_Kp = pandora.Box( value=5.0)
        nodes = (\
            self.NodeWReader( p_w),
            self.NodeYReader( p_y, rover, goal),
            self.NodeSummingPoint( p_w, p_y, p_e),
            NodeAlgorithm( algorithm=ce.EulerBw4P( id="directioncontroller.algorithm", p_Kp=self.__p_Kp, p_Ts=p_Ts, p_e=p_e, p_u=p_u)),
            self.NodeUWriter( p_u, rover),
            self.NodeStopCriterion( p_e=p_e, rover=rover, p_is_goal_reached=p_is_goal_reached),
            self.NodePublisher( id_controller=self.id(), p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts),
        )
        self.__controller = ces.SISOController.New( nodes, p_Ts)
        return

    def execute( self):
        self.__controller.execute()
        return

#    def p_Ts_published( self): return self.__p_Ts_published
#
#    def p_w_published( self): return self.__p_w_published
#    def p_e_published( self): return self.__p_e_published
#    def p_u_published( self): return self.__p_u_published
#    def p_y_published( self): return self.__p_y_published

    def to_on( self):
        _names= ( self.__class__.__name__, "to_on")
        #_Logger.info( "%s.%s().", *_names)

        self.__controller.to_on()
        return self

    def to_off( self):
        _names= ( self.__class__.__name__, "to_off")
        #_Logger.info( "%s.%s().", *_names)

        self.__controller.to_off()
        return self

    def to_ready( self):
        _names= ( self.__class__.__name__, "to_ready")
        #_Logger.info( "%s.%s().", *_names)

        self.__controller.to_ready()
        return self

    def to_running( self):
        _names= ( self.__class__.__name__, "to_running")
        #_Logger.info( "%s.%s().", *_names)

        self.__controller.to_running()
        return self


class NodeAlgorithm(ces.Node4C):

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


class ObstacleAvoidingController(Object):

    """

    \param  robot   Convenience-Klasse, die transparent auf die iIOs schreibt.

    \param  rAlpha  Richtungswinkel, der auf 90° gehalten werden muss.

    \param  p_Ts    Abtastzeit.

    History:
        -   2017-08-18
            -   Verstärkung Kp von 50 auf 200 vergrößert.
            -   Verstätkung Ki von 0.1 auf 0.5 vergrößert.
    """

    class NodeWReader(ces.Node4C):

        """Sollwert.

        Istwert ist der Winkel, den die Resultiernde aller Distanzsensorstrahlen
        mit der Y-Achse des {ROBOT} einschließt. Und der muss 90° sein.
        """

        def __init__( self, p_w):
            super().__init__()

            p_w.value( pi/2)
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            super().execute()
            return


    class NodeYReader(ces.Node4C):

        """Istwert.

        Istwert ist der Winkel, den die Resultiernde aller Distanzsensorstrahlen
        mit der Y-Achse des {ROBOT} einschließt. Und der muss Null sein.
        """

        def __init__( self, *, p_y : pandora.Box, p_rAlpha : pandora.Box):
            super().__init__()

            self.__p_y = p_y
            self.__p_rAlpha = p_rAlpha
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_y.value( self.__p_rAlpha.value())

            super().execute()
            return


    class NodeSummingPoint(ces.Node4C):

        def __init__( self, *, p_w, p_y, p_e):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                            # e = w - y
            super().execute()
            return self

        def _read_y_( self):
            return 0


    class NodeUWriter(ces.Node4C):

        """Schreibt aufs Fahrwerk: Positive Werte von u(t) bedeuten 'Fahren nach links', negative Werte von u(t) bedeuten 'Fahren nach rechts'.
        """

        def __init__( self, p_u, rover: StandardRover):
            super().__init__()

            self.__p_u = p_u
            self.__rover = rover
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_u.value( -self.__p_u.value())

            self._write_u_( self.__p_u.value())

            super().execute()
            return self

        def _write_u_( self, u):
            _names = ( self.__class__.__name__, "_write_u_")
            #_Logger.debug( "ObstacleAvoidingController.%s.%s(): E n t e r e d.", *_names)

            if self.is_running():
                v_100, omega_100 = self.__rover.body().uck_100()
                omega_100 = u
                #_Logger.debug( "%s.%s(): omega_100 = %.3f. ", *_names, omega_100)

                v_100 = setupdata.Setup().v_avoiding_100()

#            else:
#                v_100, omega_100 = 0, 0
# ##### Einfach nur nichts tun, sonst spucken wir anderen Reglern in die Suppe.

            self.__rover.body().uck_100( v_100, omega_100)

            #_Logger.debug( "%s.%s(): Exit now.", *_names)
            return self


    class NodePublisher(ces.Node4C):

        """Publishing der Signalwerte des reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

        \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
        \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
        \param  p_e     Regelabweichung, s. NodeSummingPoint.
        \param  p_u     Stellgröße, s. NodeActuator.
        \param  p_Ts    Abtastzeit.
        """

        def __init__( self, *, p_w, p_y, p_e, p_u, p_Ts):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            self.__p_u = p_u
            self.__p_Ts = p_Ts
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            ### Abkürzungen
            #
            w = self.__p_w.value()
            y = self.__p_y.value()
            e = self.__p_e.value()
            u = self.__p_u.value()
            Ts = self.__p_Ts.value()

            ### Publishing DEPRECATED
            #
            pandora.Shelf().box( "gui.obstacleavoidingcontroller.w(t)").value( w)
            pandora.Shelf().box( "gui.obstacleavoidingcontroller.y(t)").value( y)
            pandora.Shelf().box( "gui.obstacleavoidingcontroller.e(t)").value( e)
            pandora.Shelf().box( "gui.obstacleavoidingcontroller.u(t)").value( u)
            pandora.Shelf().box( "gui.obstacleavoidingcontroller.Ts").value( Ts)

            ### Publishing auf die Ausgänge
            #
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_W, w)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_W_DEG, degrees( w))
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_Y, y)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_Y_DEG, degrees( y))
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_E, e)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_E_DEG, degrees( e))
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_U, u)
            #iios3.IOutShelves( "rc").iout_value( iiossetup.IIoIds.RC._AVOIDCONTROLLER_TS, Ts)

            ### Base Class ausführen
            #
            super().execute()
            return self




    def __init__( self, rover: StandardRover, p_rAlpha: pandora.Box, p_Ts: pandora.Box):
        super().__init__( id=self.__class__.__name__)

        ### Transformationen, aus denen die Regelabweichung gebildet wird
        #
        self.__bTr = rover.brain().bT()

        ### Chassis, d.i. die Strece
        #
        self.__rover = rover

        ### Signale zum Rechnen
        #
        p_w = pandora.Box( value=0.0)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.BoxClippingMonitored( value=0.0, id="obstacleavoidingcontroller.u(t)")
        p_y = pandora.Box( value=0.0)
        p_y_filtered = pandora.BoxMonitored( value=0.0)

        ### Regler
        #
        self.__p_Kp = pandora.Box( value=200.0)
        self.__p_Ki = pandora.Box( value=0.5)
        nodes = (\
            self.NodeWReader( p_w),
            self.NodeYReader( p_y=p_y, p_rAlpha=p_rAlpha),
            self.NodeSummingPoint( p_w=p_w, p_y=p_y, p_e=p_e),
            NodeAlgorithm( algorithm=ce.EulerBw4PI( id="avoidingcontroller.algorithm", p_Kp=self.__p_Kp, p_Ki=self.__p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_u)),
            self.NodeUWriter( p_u, rover),
            self.NodePublisher( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts),
        )
        self.__controller = ces.SISOController.New( nodes, p_Ts)
        return

    def execute( self):
        self.__controller.execute()
        return

    def to_on( self): self.__controller.to_on()
    def to_off( self): self.__controller.to_off()
    def to_ready( self): self.__controller.to_ready()
    def to_running( self): self.__controller.to_running()


class ObstacleDistanceController(Object):

    """

    **Parameters**
        bTr : T3D
            Frame (= pose) of the Robot relative {BASE}.

        bTg : T3D
            Frame (= pose) of the Goal relative {BASE}.
    """

    class NodeWReader(ces.Node4C):

        """Sollwert.

        Istwert ist der Winkel, den die Resultiernde aller Distanzsensorstrahlen
        mit der Y-Achse des {ROBOT} einschließt. Und der muss Null sein.
        """

        def __init__( self, p_w):
            """Nix zu tun hier, Sollwert kommt von außen.
            """
            super().__init__()
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            super().execute()
            return


    class NodeYReader(ces.Node4C):

        """Istwert.

        Istwert ist der Winkel, den die Resultiernde aller Distanzsensorstrahlen
        mit der Y-Achse des {ROBOT} einschließt. Und der muss Null sein.
        """

        def __init__( self, *, p_y : pandora.Box, p_rDistance : pandora.Box):
            super().__init__()

            self.__p_y = p_y
            self.__p_rDistance = p_rDistance
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_y.value( self.__p_rDistance.value())

            super().execute()
            return


    class NodeSummingPoint(ces.Node4C):

        def __init__( self, *, p_w, p_y, p_e):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_e.value( self.__p_w.value() - self.__p_y.value())
                                            # e = w - y
            super().execute()
            return self

        def _read_y_( self):
            return 0


    class NodeUWriter(ces.Node4C):

        """Schreibt aufs Fahrwerk: Positive Werte von u(t) bedeuten 'Fahren nach links', negative Werte von u(t) bedeuten 'Fahren nach rechts'.
        """

        def __init__( self, p_u, rover: StandardRover):
            super().__init__()

            self.__p_u = p_u
            self.__rover = rover
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            self.__p_u.value( -self.__p_u.value())

            self._write_u_( self.__p_u.value())

            super().execute()
            return self

        def _write_u_( self, u):
            if self.is_running():
                v_100, omega_100 = self.__rover.body().uck_100()
                omega_100 = u

#            else:
#                v_100, omega_100 = 0, 0
# ##### Einfach nur nichts tun, sonst spucken wir anderen Reglern in die Suppe.

            self.__rover.body().uck_100( v_100, omega_100)

            return self


    class NodePublisher(ces.Node4C):

        """Publishing der Signalwerte des reglers, um sie zum Beispiel durch Subscribers anzuzeigen.

        \param  p_w     Sollwert. Wird gelesen durch den Node NodeWReader.
        \param  p_y     Istwert. Wird gelesen durch den Node NodeYReader.
        \param  p_e     Regelabweichung, s. NodeSummingPoint.
        \param  p_u     Stellgröße, s. NodeActuator.
        \param  p_Ts    Abtastzeit.
        """

        def __init__( self, *, p_w, p_y, p_e, p_u, p_Ts):
            super().__init__()

            self.__p_w = p_w
            self.__p_y = p_y
            self.__p_e = p_e
            self.__p_u = p_u
            self.__p_Ts = p_Ts
            return

        def configure( self, p_Ts):
            pass

        def execute( self):
            pandora.Shelf().box( "gui.obstacledistancecontroller.w(t)").value( self.__p_w.value())
            pandora.Shelf().box( "gui.obstacledistancecontroller.y(t)").value( self.__p_y.value())
            pandora.Shelf().box( "gui.obstacledistancecontroller.e(t)").value( self.__p_e.value())
            pandora.Shelf().box( "gui.obstacledistancecontroller.u(t)").value( self.__p_u.value())
            pandora.Shelf().box( "gui.obstacledistancecontroller.Ts").value( self.__p_Ts.value())

            super().execute()
            return self




    def __init__( self, rover: StandardRover, p_rDistance : pandora.Box, p_Ts : pandora.Box):
        super().__init__( id=self.__class__.__name__)

        ### Transformationen, aus denen die Regelabweichung gebildet wird
        #
        self.__bTr = rover.brain().bT()

        ### Chassis, d.i. die Strece
        #
        self.__rover = rover

        ### Signale zum Rechnen
        #
        p_w = pandora.Box( value=1.0)
                                        # Max. reach of rangers. Kann das aus den
                                        #   Settings kommen? Auf jeden Fall mit
                                        #   den USS abstimmen, weil die clippen!
        p_e = pandora.Box( value=0.0)
        p_u = pandora.BoxClippingMonitored( value=0.0)
        p_y = pandora.Box( value=0.0)
        p_y_filtered = pandora.BoxMonitored( value=0.0)

        ### Signale zum Anzeigen
        #
#        self.__p_w_published = pandora.BoxMonitored( id="gui.obstacledistancecontroller.w(t)", value=0.0, label="w(t)", dim="rad")
#        self.__p_e_published = pandora.BoxMonitored( id="gui.obstacledistancecontroller.e(t)", value=0.0, label="e(t)", dim="rad")
#        self.__p_u_published = pandora.BoxMonitored( id="gui.obstacledistancecontroller.u(t)", value=0.0, label="u(t) = omega_100", dim="%")
#        self.__p_y_published = pandora.BoxMonitored( id="gui.obstacledistancecontroller.y(t)", value=0.0, label="y(t)", dim="rad")
#        self.__p_Ts_published = pandora.BoxMonitored( id="gui.obstacledistancecontroller.Ts", value=0.0, label="Ts", dim="s")

        ### Regler
        #
        self.__p_Kp = pandora.Box( value=2.0)
        self.__p_Ki = pandora.Box( value=0.01)
        nodes = (\
            self.NodeWReader( p_w),
            self.NodeYReader( p_y=p_y, p_rDistance=p_rDistance),
            self.NodeSummingPoint( p_w=p_w, p_y=p_y, p_e=p_e),
            NodeAlgorithm( algorithm=ce.EulerBw4PI( id="obstacledistancecontroller.algorithm", p_Kp=self.__p_Kp, p_Ki=self.__p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_u)),
            self.NodeUWriter( p_u, rover),
            self.NodePublisher( p_w=p_w, p_y=p_y, p_e=p_e, p_u=p_u, p_Ts=p_Ts),
        )
        self.__controller = ces.SISOController.New( nodes, p_Ts)
        return

    def execute( self):
        self.__controller.execute()
        return

#    def p_Ts_published( self): return self.__p_Ts_published
#
#    def p_w_published( self): return self.__p_w_published
#    def p_e_published( self): return self.__p_e_published
#    def p_u_published( self): return self.__p_u_published
#    def p_y_published( self): return self.__p_y_published

    def to_on( self): self.__controller.to_on()
    def to_off( self): self.__controller.to_off()
    def to_ready( self): self.__controller.to_ready()
    def to_running( self): self.__controller.to_running()


class ThreadedDriveController(DriveController, mtt.CyclingThread):

    def __init__( self, rover: StandardRover, p_Ts: pandora.Box):
        DriveController.__init__( self, rover=rover, p_Ts=p_Ts)
        mtt.CyclingThread.__init__( self, id=self.classname(), cycletime=p_Ts.value(), udata=None)

        self.start( syncly=True)
        return

    def execute( self):
        pass

    def _run_( self, udata):
        DriveController.execute( self)
        return


class ThreadedGoalDirectionController(GoalDirectionController, mtt.CyclingThread):

    def __init__( self, rover: StandardRover, goal: StandardGoal, p_Ts : pandora.Box):
        GoalDirectionController.__init__( self, rover=rover, goal=goal, p_Ts=p_Ts)
        mtt.CyclingThread.__init__( self, id=self.classname(), cycletime=p_Ts.value(), udata=None)

        self.start( syncly=True)
        return

    def execute( self):
        pass

    def _run_( self, udata):
        GoalDirectionController.execute( self)
        return


class ThreadedGoalDistanceController(GoalDistanceController, mtt.CyclingThread):

    def __init__( self, rover: StandardRover, goal: StandardGoal, p_Ts: pandora.Box, p_is_goal_reached: pandora.Box):
        GoalDistanceController.__init__( self, rover=rover, goal=goal, p_Ts=p_Ts, p_is_goal_reached=p_is_goal_reached)
        mtt.CyclingThread.__init__( self, id=self.classname(), cycletime=p_Ts.value(), udata=None)

        self.start( syncly=True)
        return

    def execute( self):
        pass

    def _run_( self, udata):
        GoalDistanceController.execute( self)
        return

