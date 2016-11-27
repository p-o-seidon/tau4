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

from tau4.automation.sm import SM, SMState


class _SMStates:

    class Idle(SMState):
        
        def __init__( self, sms):
            super().__init__( sms)
            return

        def execute( self):
            if _SMStates.Ready( self).is_condition_met():
                _SMStates.Ready( self).select()
                return

            return
        

    class Finished(SMState):
        
        def __init__( self, sms):
            super().__init__( sms)
            return
        
        def execute( self):
            pass

        def is_condition_met( self):
            return True


    class Ready(SMState):

        def __init__( self, sms):
            super().__init__( sms)
            self.__time_created = time.time()
            return
        
        def is_condition_met( self):
            return time.time() - self.__time_created > 1
        
        def execute( self):
            if _SMStates.Finished( self).is_condition_met():
                _SMStates.Finished( self).select()
                return

            return


class _TESTCASE__SM(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()
        
        sm = SM( _SMStates.Idle( None))
        t = time.time()
        while time.time() - t < 2:
            print( "Current state = " + sm.sms().__class__.__name__)
            sm.execute()
            time.sleep( 0.100)
            
        self.assertIs( sm.sms(), _SMStates.Finished( None))

        return


_Testsuite = unittest.makeSuite( _TESTCASE__SM)


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



