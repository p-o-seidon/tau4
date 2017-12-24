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

import tau4
from tau4.data import flex
from tau4.data import univars as uv
import time
import unittest


class _TESTCASE__Persistor(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        v = flex.VariableDeMoPe( id="motor.voltage", value=42.0, label="Motor Voltage", dim="V", value_min=-42, value_max=42, dirname="./")
        v.store()
        v.value( 0.0)
        self.assertAlmostEqual( 0, v.value())
        v.restore()
        self.assertAlmostEqual( 42, v.value())
        return


_Testsuite = unittest.makeSuite( _TESTCASE__Persistor)


class _TESTCASE__Univar(unittest.TestCase):

    def test__storage( self):
        """
        """
        print()

        v = uv.Univar( id=-1, value=42.0)
        uv.Univar.Store( "Hollodrio", v)
        v.value( 13)
        self.assertAlmostEqual( 13, v.value())

        w = uv.Univar.Restore( "Hollodrio")
        self.assertAlmostEqual( 13, w.value())
        self.assertIs( v, w)

        return

    def test__performance( self):
        """
        """
        print()

        t = time.time()
        i = n = 10000
        while i:
            v = uv.Univar( value=42)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Univar creation. " % (dt*1000000/n))


        v = uv.Univar( value=42)
        t = time.time()
        i = n = 10000
        while i:
            dont_care = v.value()

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Univar read access. " % (dt*1000000/n))


        v = uv.Univar( value=42)
        t = time.time()
        i = n = 10000
        while i:
            v.value( i)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Univar write access. " % (dt*1000000/n))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Univar))


class _TESTCASE__UnivarM(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        return


    def test__performance( self):
        """
        """
        print()

        t = time.time()
        i = n = 10000
        while i:
            v = uv.UnivarM.New( value=42)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM creation. " % (dt*1000000/n))


        v = uv.UnivarM.New( value=42)
        t = time.time()
        i = n = 10000
        while i:
            dont_care = v.value()

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM read access. " % (dt*1000000/n))


        v = uv.UnivarM.New( value=42)
        t = time.time()
        i = n = 10000
        while i:
            v.value( i)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM write access. " % (dt*1000000/n))

        return

    def test__tau4p_on_modified( self):
        """
        """
        print()

        is_v_modified = uv.Univar( value=False)
        is_v_violated = uv.Univar( value=False)
        is_v_unviolated = uv.Univar( value=False)

        def tau4s_on_modified( pc, v=is_v_modified):
            print( "%s( id=%s) has been modified. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_violated( pc, v=is_v_violated):
            print( "%s( id=%s) has been violated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_unviolated( pc, v=is_v_unviolated):
            print( "%s( id=%s) has been unviolated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        v = uv.UnivarM.New( value=13, value_bounds=(-42, 42))
        self.assertAlmostEqual( 13, v.value())
        v.reg_tau4s_on_modified( tau4s_on_modified)
        v.reg_tau4s_on_limit_violated( tau4s_on_limit_violated)
        v.reg_tau4s_on_limit_unviolated( tau4s_on_limit_unviolated)

        v.value( 42)
        self.assertTrue( is_v_modified.value())
        self.assertFalse( is_v_violated.value())

        v.value( 43)
        self.assertAlmostEqual( 43, v.value())
                                        # Der Monitor clippt NICHT!
        self.assertTrue( is_v_violated.value())
        self.assertFalse( is_v_unviolated.value())

        v.value( 42)
        self.assertTrue( is_v_unviolated.value())

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__UnivarM))


class _TESTCASE__UnivarDM(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        v = uv.UnivarDM.New( id=42, value=42, label="Speed", dimension="m/s", value_bounds=(-42, None))
        self.assertEquals( "Speed: 42.000 m/s", str( v))

        return

    def test__performance( self):
        """
        """
        print()

        t = time.time()
        i = n = 10000
        while i:
            v = uv.UnivarDM.New( value=42, label="UnivarDM", dimension="Angstroem/w")

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM creation. " % (dt*1000000/n))


        v = uv.UnivarDM.New( value=42, label="UinivarDM", dimension="Angstroem/w")
        t = time.time()
        i = n = 10000
        while i:
            dont_care = v.value()

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM read access. " % (dt*1000000/n))


        v = uv.UnivarDM.New( value=42, label="UinivarDM", dimension="Angstroem/w")
        t = time.time()
        i = n = 10000
        while i:
            v.value( i)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per UnivarDM write access. " % (dt*1000000/n))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__UnivarDM))


class _TESTCASE__UnivarDCM(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        is_called_tau4s_on_limit_violated = uv.Univar.New( value=False)
        is_called_tau4s_on_limit_unviolated = uv.Univar.New( value=False)

        def tau4s_on_limit_violated( pc, v=is_called_tau4s_on_limit_violated):
            print( "%s( id=%s) has been violated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_unviolated( pc, v=is_called_tau4s_on_limit_unviolated):
            print( "%s( id=%s) has been unviolated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        v = uv.UnivarDCM.New( id=42, value=13, label="Speed", dimension="m/s", value_bounds=(-42, 42))
        self.assertEquals( "Speed: 13.000 m/s", str( v))

        v.reg_tau4s_on_limit_violated( tau4s_on_limit_violated)
        v.reg_tau4s_on_limit_unviolated( tau4s_on_limit_unviolated)

        v.value( 43)
        self.assertFalse( is_called_tau4s_on_limit_violated.value())
        self.assertFalse( is_called_tau4s_on_limit_unviolated.value())
        self.assertAlmostEqual( 42, v.value())

        v.value( 0)
        self.assertFalse( is_called_tau4s_on_limit_unviolated.value())
        self.assertAlmostEqual( 0, v.value())

        v.value( -43)
        self.assertAlmostEqual( -42, v.value())

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__UnivarDCM))


class _TESTCASE__UnivarC(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        is_called_tau4s_on_limit_violated = uv.Univar.New( value=False)
        is_called_tau4s_on_limit_unviolated = uv.Univar.New( value=False)

        def tau4s_on_limit_violated( pc, v=is_called_tau4s_on_limit_violated):
            print( "%s( id=%s) has been violated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_unviolated( pc, v=is_called_tau4s_on_limit_unviolated):
            print( "%s( id=%s) has been unviolated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        v = uv.UnivarC.New( id=42, value=13, value_bounds=(-42, 42))
        with self.assertRaises( AttributeError):
            v.reg_tau4s_on_limit_violated( tau4s_on_limit_violated)
            v.reg_tau4s_on_limit_unviolated( tau4s_on_limit_unviolated)

        v.value( 43)
        self.assertAlmostEqual( 42, v.value())

        v.value( 0)
        self.assertAlmostEqual( 0, v.value())

        v.value( -43)
        self.assertAlmostEqual( -42, v.value())

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__UnivarC))


class _TESTCASE__VarblCats(unittest.TestCase):

    def test( self):
        """
        """
        print
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__VarblCats))


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



