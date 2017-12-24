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


class _TESTCASE__Variable(unittest.TestCase):

    def test__storage( self):
        """
        """
        print()

        v = flex.Variable( id=-1, value=42.0)
        flex.Variable.InstanceStore( "Hollodrio", v)
        v.value( 13)
        self.assertAlmostEqual( 13, v.value())

        w = flex.Variable.Instance( "Hollodrio")
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
            v = flex.Variable( value=42)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Variable creation. " % (dt*1000000/n))


        v = flex.Variable( value=42)
        t = time.time()
        i = n = 10000
        while i:
            dont_care = v.value()

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Variable read access. " % (dt*1000000/n))


        v = flex.Variable( value=42)
        t = time.time()
        i = n = 10000
        while i:
            v.value( i)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per Variable write access. " % (dt*1000000/n))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Variable))


class _TESTCASE__VariableMo(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        return


    def test__tau4p_on_modified( self):
        """
        """
        print()

        is_v_modified = flex.Variable( value=False)
        is_v_violated = flex.Variable( value=False)
        is_v_unviolated = flex.Variable( value=False)

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

        v = flex.VariableMo( value=13, value_min=-42, value_max=42)
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


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__VariableMo))


class _TESTCASE__VariableDeMo(unittest.TestCase):

    def _tau4s_on_value_changed_( self, tau4pc):
        return


    def test__basic_use( self):
        """
        """
        print()

        v = flex.VariableDeMo( id=42, value=42, label="Speed", dim="m/s", value_min=-42, value_max=None)
        self.assertEqual( 42, v.id())
        self.assertNotEqual( "Speed: 42.000 m/s", str( v))
        self.assertEquals( "Speed", v.label())
        self.assertEquals( 42, v.value())
        self.assertEquals( "m/s", v.dim())
        self.assertNotEqual( "42.000", str( v))

        w = flex.VariableDeMo( id=-1, value=4242, label="Speed", dim="m/s", value_min=-42, value_max=None)
        v << w
        self.assertEqual( 42, v.id())
        self.assertNotEqual( "Speed: 4242.000 m/s", str( v))
        self.assertEquals( "Speed", v.label())
        self.assertEquals( 4242, v.value())
        self.assertEquals( "m/s", v.dim())
        self.assertNotEqual( "4242.000", str( v))

        return

    def test__performance( self):
        """
        """
        print()

        t = time.time()
        i = n = 10000
        while i:
            v = flex.VariableDeMo( value=42, label="VariableDeMo", dim="Angstroem/w")

            i -= 1

        dt = time.time() - t
        print( "%.3f us per VariableDeMo creation. " % (dt*1000000/n))


        v = flex.VariableDeMo( value=42, label="VariableDeMo", dim="Angstroem/w")
        v.reg_tau4s_on_modified( self._tau4s_on_value_changed_)
        t = time.time()
        i = n = 10000
        while i:
            dont_care = v.value()

            i -= 1

        dt = time.time() - t
        print( "%.3f us per VariableDeMo read access. " % (dt*1000000/n))


        v = flex.VariableDeMo( value=42, label="VariableDeMo", dim="Angstroem/w")
        v.reg_tau4s_on_modified( self._tau4s_on_value_changed_)
        t = time.time()
        i = n = 10000
        while i:
            v.value( i)

            i -= 1

        dt = time.time() - t
        print( "%.3f us per VariableDeMo write access. " % (dt*1000000/n))

        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__VariableDeMo))


class _TESTCASE__VariableDeClMo(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        is_called_tau4s_on_limit_violated = flex.Variable( value=False)
        is_called_tau4s_on_limit_unviolated = flex.Variable( value=False)

        def tau4s_on_limit_violated( pc, v=is_called_tau4s_on_limit_violated):
            print( "%s( id=%s) has been violated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_unviolated( pc, v=is_called_tau4s_on_limit_unviolated):
            print( "%s( id=%s) has been unviolated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        v = flex.VariableDeClMo( id=42, value=13, label="Speed", dim="m/s", value_min=-42, value_max=42)
        self.assertEquals( "Speed: 13 m/s", str( v))

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


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__VariableDeClMo))


class _TESTCASE__VariableCl(unittest.TestCase):

    def test__basic_use( self):
        """
        """
        print()

        is_called_tau4s_on_limit_violated = flex.Variable( value=False)
        is_called_tau4s_on_limit_unviolated = flex.Variable( value=False)

        def tau4s_on_limit_violated( pc, v=is_called_tau4s_on_limit_violated):
            print( "%s( id=%s) has been violated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        def tau4s_on_limit_unviolated( pc, v=is_called_tau4s_on_limit_unviolated):
            print( "%s( id=%s) has been unviolated. " % (pc.publisher().__class__.__name__, pc.publisher().id()))
            v.value( True)
            return

        v = flex.VariableCl( id=42, value=13, value_min=-42, value_max=42)
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


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__VariableCl))


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



