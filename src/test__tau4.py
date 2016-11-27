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

import tau4
import time
import unittest


class _RootClass:
    
    def __init__( self):
        return
    
    
class _SubClassOfBuiltinObject(object):
    
    def __init__( self):
        super().__init__()
        return
        

class _TESTCASE__Objects(unittest.TestCase):

    def test__performance( self):
        """
        """
        print()

        t = time.time()
        i = n = 10000
        while i:
            o = _RootClass()
            
            i -= 1
            
        dt = time.time() - t
        print( "%.3f us per _RootClass creation. " % (dt*1000000/n))


        t = time.time()
        i = n = 10000
        while i:
            o = _SubClassOfBuiltinObject()
            
            i -= 1
            
        dt = time.time() - t
        print( "%.3f us per _SubClassOfBuiltinObject creation. " % (dt*1000000/n))

        return

    def test__adding_to_and_removing_from_Objects( self):
        """
        """
        print()
        
        o = _RootClass()
        
        tau4.Objects().add( 42, o)
        
        oo = tau4.Objects( 42)
        self.assertIs( o, oo)
        
        self.assertRaises( KeyError, tau4.Objects, 43)
        
        self.assertRaises( KeyError, tau4.Objects().add, 42, o)
        
        tau4.Objects().remove( 42)
        self.assertRaises( KeyError, tau4.Objects, 42)
        tau4.Objects().add( 42, o)
        oo = tau4.Objects( 42)
        self.assertIs( o, oo)
        
        return


_Testsuite = unittest.makeSuite( _TESTCASE__Objects)


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



