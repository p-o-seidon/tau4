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
import matplotlib.pyplot as plt
import time
import unittest

import tau4
from tau4 import Id
from tau4.data import pandora

from tau4 import ce
from tau4.ce import eulerbw


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()

        p_Kp = pandora.Box( value=100.0)
        p_Ki = pandora.Box( value=0.01)
        p_Ts = pandora.BoxMonitored( value=0.100)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.BoxClippingMonitored( value=0.0)
        alg = eulerbw.PI( id=None, p_Kp=p_Kp, p_Ki=p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_u)
        t0 = time.time()
        dT = 3
        t_ = []
        e_ = []
        u_ = []
        t0 = time.time()
        t_.append( time.time() - t0)
        while t_[ -1] <= dT:
            p_e.value( 1)
            e_.append( p_e.value())
            alg.execute()
            u = p_u.value()
            u_.append( u)

            t_.append( time.time() - t0)

        t_.pop()

        fig = plt.figure()
        ax = fig.add_subplot( 111)
        ax.plot( t_, u_)
        ax.set_ylim( 0, max( u_))
        plt.savefig( __file__ + ".EulerBw4PI.pdf")
        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__eulerbw_PT1PT1(unittest.TestCase):

    def test__aperodischer_Grenzfall( self):
        """
        """
        print()

        p_T1 = p_T2 = pandora.Box( value=10.0)
                                        # Aperiodischer Grenzfall
        p_Ts = pandora.BoxMonitored( value=0.1)

        p_e = pandora.Box( value=1.0)
        p_u = pandora.Box( value=0.0)

        tf = eulerbw.PT1PT1( \
            id=Id( "pt1pt1"),
            p_K=pandora.Box( value=1.0),
            p_T1=p_T1,
            p_T2=p_T2,
            p_Ts=p_Ts,
            p_e=p_e, p_u=p_u
        )

        t_ = [t*p_Ts.value() for t in range( 1000)]
        u_ = []
        for t in t_:
            tf.execute()
            u_.append( p_u.value())

        fig = plt.figure()
        ax = fig.add_subplot( 111)
        ax.plot( t_, u_)
        ax.set_ylim( 0, max( u_))
        pathname = __file__ + ".%s.T1=T2.pdf" % tf.name()
        plt.savefig( pathname)
        return


    def test__steifes_System( self):
        """
        """
        print()

        p_T1 = pandora.Box( value=1.0)
        p_T2 = pandora.Box( value=10.0)

        p_Ts = pandora.BoxMonitored( value=0.1)

        p_e = pandora.Box( value=1.0)
        p_u = pandora.Box( value=0.0)

        tf = eulerbw.PT1PT1( \
            id=Id( "pt1pt1.2"),
            p_K=pandora.Box( value=1.0),
            p_T1=p_T1,
            p_T2=p_T2,
            p_Ts=p_Ts,
            p_e=p_e, p_u=p_u
        )

        t_ = [t*p_Ts.value() for t in range( 1000)]
        u_ = []
        for t in t_:
            tf.execute()
            u_.append( p_u.value())

        fig = plt.figure()
        ax = fig.add_subplot( 111)
        ax.plot( t_, u_)
        ax.set_ylim( 0, max( u_))
        pathname = __file__ + ".%s.steif.pdf" % tf.name()
        plt.savefig( pathname)
        return


    def test__rampe_fuer_cruiser( self):
        """
        """
        print()

        Ts_ROP = 0.025
        T = Ts_ROP*5

        p_T1 = pandora.Box( value=T)
        p_T2 = p_T1

        p_Ts = pandora.BoxMonitored( value=Ts_ROP)

        p_e = pandora.Box( value=100.0)
        p_u = pandora.Box( value=0.0)

        tf = eulerbw.PT1PT1( \
            id=Id( "pt1pt1.cruiser"),
            p_K=pandora.Box( value=1.0),
            p_T1=p_T1,
            p_T2=p_T2,

            p_Ts=p_Ts,
            p_e=p_e, p_u=p_u
        )

        t_ = [t*p_Ts.value() for t in range( 2*int( 4*T/Ts_ROP))]
        u_ = [ 0]
        for t in t_[ 1:]:
            tf.execute()
            u_.append( p_u.value())

        fig = plt.figure()
        ax = fig.add_subplot( 111)
        ax.plot( t_, u_)
        ax.set_ylim( 0, max( u_))
        pathname = __file__ + ".%s.cruiser.pdf" % tf.name()
        plt.savefig( pathname)
        return

_Testsuite.addTest( unittest.makeSuite( _TESTCASE__eulerbw_PT1PT1))


class _TESTCASE__eulerbw_PT1(unittest.TestCase):

    def test__rampe_fuer_cruiser( self):
        """
        """
        print()

        Ts_ROP = 0.025
        T = Ts_ROP*4

        p_T1 = pandora.Box( value=T)

        p_Ts = pandora.BoxMonitored( value=Ts_ROP)

        p_e = pandora.Box( value=100.0)
        p_u = pandora.Box( value=0.0)

        tf = eulerbw.PT1( \
            id=Id( "pt1.cruiser"),
            p_K1=pandora.Box( value=1.0),
            p_T1=p_T1,

            p_Ts=p_Ts,
            p_e=p_e, p_u=p_u
        )

        t_ = [t*p_Ts.value() for t in range( 2*int( 4*T/Ts_ROP))]
        u_ = [ 0]
        for t in t_[ 1:]:
            tf.execute()
            u_.append( p_u.value())

        fig = plt.figure()
        ax = fig.add_subplot( 111)
        ax.plot( t_, u_)
        ax.set_ylim( 0, max( u_))
        pathname = __file__ + ".%s.cruiser.pdf" % tf.name()
        plt.savefig( pathname)
        return

_Testsuite.addTest( unittest.makeSuite( _TESTCASE__eulerbw_PT1))


class _TESTCASE__Lead(unittest.TestCase):

    def test( self):
        """
        """
        print()

        p_Ts = pandora.BoxMonitored( value=0.001)
        p_e = pandora.Box( value=0.0)
        p_u = pandora.Box( value=0.0)

        controller = eulerbw.Lead( None, pandora.Box( value=1), pandora.Box( value=0.1), pandora.Box( value=0.01), p_Ts, p_e, p_u)
        p_e.value( 42)
        controller.execute()
        print( "u = %.3f. " % p_u.value())
        self.assertAlmostEqual( controller._u_by_2nd_algorithm_(), controller.p_u().value())

        p_e.value( 0)
        controller.execute()
        print( "u = %.3f. " % p_u.value())
        self.assertAlmostEqual( controller._u_by_2nd_algorithm_(), controller.p_u().value())
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Lead))


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()
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



