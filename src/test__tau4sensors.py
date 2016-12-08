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
from math import *

import tau4
from tau4.mathe.linalg import T3D, Vector3
from tau4.sensors import gps, IRS, IRSDummy, Locator, navi, Rangers, Sensors2, SensorSpecDataIRS, SensorSpecDataUSS, USS
import time
import unittest


class _TESTCASE__Sensors(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        ### Create and add some sensors to tau4
        #
        sensors = Sensors2()
        
        
        ### Visit all sensors
        #
        for sensor in sensors( id_group=None):
            s = """
Sensor id (unique among all groups):    %s
Sensor pose rel rack:                   %s
Measurement position rel sensor:        %s
Measurement position rel rack:          %s
""" % ( \
        sensor.id(),
                                        # Unique among all groups.
        sensor.rT(),
                                        # Lage des Sensors rel. eines Racks {R}.
        sensor.sPm(),
                                        # Position der Messung rel. des Sensors.
        sensor.rPm(),
                                        # Position der Messung rel. des Racks, 
                                        #   auf dem der Sensor montiert ist.
        )

            print( s)
            
            
        ### Visit IRS only
        #
        sensors.add_group( id_group="irs")
        sensors.add_sensor( \
            id_group="irs", 
            sensor=IRS( \
                id=-1, 
                specs_io=None, 
                specs_data=SensorSpecDataIRS( 42), 
                rT=tau4.mathe.linalg.T3DFromEuler()
            )
        )

        for sensor in sensors( id_group="irs"):
            print( """
Sensor Id (unique among all groups):    %s
Sensor pose rel rack:                   %s
Measurement position rel sensor:        %s
Measurement position rel rack:          %s
""" % ( \
        sensor.id(),
                                        # Unique among all groups.
        sensor.rT(),
                                        # Lage des Sensors rel. eines Racks {R}.
        sensor.sPo(),
                                        # Rohmesswert des Sensors: Position eines
                                        #   Hindernisses rel. eines Racks.
                                        #   R a n g e r   o n l y.
        sensor.rPo(),
                                        # Rechenwert des Sensors: Position des 
                                        #   Hindernisses rel. eines Racks, auf 
                                        #   dem der Sensor montiert ist.
                                        #   R a n g e r   o n l y.
        )
    )
            self.assertEqual( sensor.sPo(), sensor.sPm())
            self.assertEqual( sensor.rPo(), sensor.rPm())


        ### Visit USS only
        #
        sensors.add_group( "uss")
        sensors.add_sensor( \
            id_group="uss", 
            sensor=USS( \
                id=-1, 
                specs_io=None, 
                specs_data=SensorSpecDataUSS(), 
                rT=tau4.mathe.linalg.T3DFromEuler()
            )
        )

        for sensor in sensors( id_group="uss"):
            print( """
Sensor Id (unique among all groups):    %s
Sensor pose rel rack:                   %s
Measurement position rel sensor:        %s
Measurement position rel rack:          %s
""" % ( \
        sensor.id(),
                                        # Unique among all groups.
        sensor.rT(),
                                        # Lage des Sensors rel. eines Racks {R}.
        sensor.sPo(),
                                        # Rohmesswert des Sensors: Position eines
                                        #   Hindernisses rel. eines Racks.
                                        #   R a n g e r   o n l y.
        sensor.rPo(),
                                        # Rechenwert des Sensors: Position des 
                                        #   Hindernisses rel. eines Racks, auf 
                                        #   dem der Sensor montiert ist.
                                        #   R a n g e r   o n l y.
        )
    )
            self.assertEqual( sensor.sPo(), sensor.sPm())
            self.assertEqual( sensor.rPo(), sensor.rPm())

        ### Visit GPS only
        #
        sensors.add_group( "gps")
        rTs = tau4.mathe.linalg.T3DFromEuler()
                                        # Lage des Sensors rel. eines Racks, 
                                        #   auf dem er montiert ist.
        sensor = gps.EmlidReachGPS( id="gps.emlid_reach", ip_addr="10.0.0.62", ip_portnbr=1962, rT=rTs)
        sensors.add_sensor( id_group="gps", sensor=sensor)
        self.assertAlmostEqual( 1, len( sensors( id_group="gps")))
        self.assertIs( sensor, sensors( id_group="gps")[ 0])
                                        # Wir haben nur einen GPS-Sensor eingehängt, als muss er das sein.
        wTb = tau4.mathe.linalg.T3D.FromEuler()
        for sensor in sensors( id_group="gps"):
            print( """
Sensor Id (unique among all groups):    %s
Transform of sensor rel rack:           %s
Position of sensor rel {W}:             %s
Position of sensor rel {B}:             %s
Position of rack rel {B}:               %s
""" % ( \
        sensor.id(),
                                        # Unique among all groups.
        sensor.rT(),
                                        # Eigene Lage rel. eines Racks {R}.
        sensor.wP(),
                                        # Rohmesswert des GPS: Position des Sensors 
                                        #   rel. {W}. 
                                        #   G P S   o n l y. Allerdings könnte hier 
                                        #   auch sPm() ausgeführt werden, dieses 
                                        #   Interface haben alle Sensoren.
        Locator().bases().wB().bP( sensor.wP()),
                                        # Das GPS berechnet KEINE Position bez. {B}, 
                                        #   etwa mit einer Methode bP( wTb).
                                        #   Das muss über den Locator erledigt werden.
        Locator().bases().wB().bP( sensor.wP()) - sensor.rT()._P_(),
                                        # Das GPS berechnet KEINE Rack-Position bez. {B}, 
                                        #   etwa mit einer Methode bPr( wTb).
                                        #   Das muss über den Locator erledigt werden.
        )
    )
            self.assertEqual( sensor.wP(), sensor.sPm())
            self.assertEqual( sensor.rT()._P_(), sensor.rPm())
            
        sensor_gps = sensor
        

        ### Visit NavSys only
        #
        sensors.add_group( "navi")
        rTs = tau4.mathe.linalg.T3DFromEuler()
                                        # Lage des Sensors rel. eines Racks, 
                                        #   auf dem er montiert ist.
        sensor = navi.NavSys( id="navi.emlid_reach", gps=sensor_gps)
        sensors.add_sensor( id_group="navi", sensor=sensor)
        self.assertAlmostEqual( 1, len( sensors( id_group="navi")))
        self.assertIs( sensor, sensors( id_group="navi")[ 0])
                                        # Wir haben nur einen GPS-Sensor eingehängt, als muss er das sein.
        wTb = tau4.mathe.linalg.T3D.FromEuler()
        for sensor in sensors( id_group="navi"):
            print( """
Sensor Id (unique among all groups):    %s
Transform of sensor rel rack:           %s
Position of sensor rel {W}:             %s
Position of sensor rel {B}:             %s
Position of rack rel {B}:               %s
""" % ( \
        sensor.id(),
                                        # Unique among all groups.
        sensor.rT(),
                                        # Eigene Lage rel. eines Racks {R}.
        sensor.wP(),
                                        # Rohmesswert des GPS: Position des Sensors 
                                        #   rel. {W}. 
                                        #   G P S   o n l y. Allerdings könnte hier 
                                        #   auch sPm() ausgeführt werden, dieses 
                                        #   Interface haben alle Sensoren.
        Locator().bases().wB().bP( sensor.wP()),
                                        # Das GPS berechnet KEINE Position bez. {B}, 
                                        #   etwa mit einer Methode bP( wTb).
                                        #   Das muss über den Locator erledigt werden.
        Locator().bases().wB().bP( sensor.wP()) - sensor.rT()._P_(),
                                        # Das GPS berechnet KEINE Rack-Position bez. {B}, 
                                        #   etwa mit einer Methode bPr( wTb).
                                        #   Das muss über den Locator erledigt werden.
        )
    )
            self.assertEqual( sensor.wP(), sensor.sPm())
            self.assertEqual( sensor.rT()._P_(), sensor.rPm())

        return


_Testsuite = unittest.makeSuite( _TESTCASE__Sensors)


class _TESTCASE__Rangers(unittest.TestCase):

    def test( self):
        """
        """
        print()
    
        ### Create the container being a Singleton
        #
        sensors = Sensors2()
    
        ### We work with some IRS sitting on a mobile robot.
        #
        #   The y-axis of the robot's frame points to its front, the x-axis as 
        #   a consequence to its right hand side.
        #
        #   The frame sits in the robot's centre.
        #
        sensors.add_group( id_group="rangers")
    
        sensor = IRSDummy( id="irs.11:00", specs_io=None, specs_data=SensorSpecDataIRS( 42), rT=tau4.mathe.linalg.T3DFromEuler( 0.250, 0.500, 0, radians( +15), 0, 0))
        sensors.add_sensor( id_group="rangers", sensor=sensor)
    
        sensor = IRSDummy( id="irs.13:00", specs_io=None, specs_data=SensorSpecDataIRS( 42), rT=tau4.mathe.linalg.T3DFromEuler( -0.250, 0.500, 0, radians( -15), 0, 0))
        sensors.add_sensor( id_group="rangers", sensor=sensor)
    
        ### Cal. the transform of an obstacle relative to the robot {R}
        #
        for sensor in sensors( id_group="rangers"):
            sensor.execute()

        sensorLHS = sensors( id_sensor="irs.11:00"); self.assertIs( sensorLHS, sensors.sensor( "irs.11:00"))
        sensorRHS = sensors( id_sensor="irs.13:00"); self.assertIs( sensorRHS, sensors.sensor( "irs.13:00"))

        ### Mock distances and check alpha of the resultant poses (obstacle absent)
        #
        sensorLHS._distance_( 0.800)
        sensorRHS._distance_( 0.800)

        rangers = sensors( id_group="rangers")
        P = Vector3()
        for sensor in rangers:
            rPo = sensor.rTo().P()
            P += rPo
            
        alpha = atan2( P.y(), P.x())            
        self.assertAlmostEqual( radians( 90), alpha)

        ### Mock distances and check alpha of the resultant poses (obstacle present)
        #
        sensorLHS._distance_( 0.400)
                                        # Obstacle approachng on the lhs
        sensorRHS._distance_( 0.800)

        rangers = sensors( id_group="rangers")
        P = Vector3()
        for sensor in rangers:
            P += sensor.rTo().P()
            
        alpha = atan2( P.y(), P.x())
        self.assertAlmostEqual( Sensors2.rAlpha( rangers), alpha)
        self.assertTrue( degrees( alpha) < 90)
                                        # Vektor zeigt nach rechts, wenn das 
                                        #   Hindernis von links kommt
        self.assertAlmostEqual( 87.25481647, degrees( alpha))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Rangers))


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


def _lab_():
    def tau4s( tau4pc):
        print( tau4pc.client().wP())
        
    sensor = gps.EmlidReachGPS( id=-1, ip_addr="192.168.42.0", ip_portnbr=1962, rT=T3D.FromEuler())
    sensor.reg_tau4s_on_modified( tau4s)
    t = time.time()
    while True:
        sensor.execute()
        print( "State: '%s'. " % sensor._sm_().smstate_current().__class__.__name__)
                                        # Only a GPS can do this.

    return


def _lab2_():
    def tau4s( tau4pc):
        print( tau4pc.client().wP())
        
    sensor = navi.NavSys( id=-1, gps=gps.EmlidReachGPS( id=-1, ip_addr="192.168.42.0", ip_portnbr=1962, rT=T3D.FromEuler()))
    sensor.reg_tau4s_on_modified( tau4s)
    t = time.time()
    while True:
        sensor.execute()
        print( "The navisys' current state is '%s'. " % sensor.statename())
                                        # Only a GPS can do this.

    return


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


if __name__ == '__main__':
    _Test_()
    #_lab_()
    #_lab2_()
    input( u"Press any key to exit...")



