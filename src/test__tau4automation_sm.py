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
import socket

import tau4
from tau4 import ThisName
from tau4.datalogging import UsrEventLog
import time
import unittest

from tau4.automation.sm import SM, SMState


class _SMStates:

    class Idle(SMState):
        
        def __init__( self):
            super().__init__()
            return

        def execute( self):
            return
        
        def is_button_1_pressed( self):
            return True
            
        def is_button_2_pressed( self):
            return False
                    
                
    class Finished(SMState):
        
        def __init__( self):
            super().__init__()
            return
        
        def execute( self):
            pass


    class Ready(SMState):

        def __init__( self):
            super().__init__()
            self.__time_created = time.time()
            return
        
        def execute( self):
            return
        
        def is_timeout( self):
            is_timeout = time.time() - self.__time_created > 1.5
            return is_timeout
 

class _TESTCASE__SM(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()
        
        _SMSTable = {\
            _SMStates.Idle(): \
                {\
                    _SMStates.Idle().is_button_1_pressed: _SMStates.Ready(),
                    _SMStates.Idle().is_button_2_pressed: _SMStates.Finished()
                },
   
            _SMStates.Ready():
                { _SMStates.Ready().is_timeout: _SMStates.Finished()},
            
            _SMStates.Finished():
                { lambda: True: _SMStates.Finished()}
        }

        sm = SM( _SMSTable, _SMStates.Idle())
        t = time.time()
        while time.time() - t < 2:
            print( "Current state = " + sm.sms_current().__class__.__name__)
            sm.execute()
            time.sleep( 0.100)
            
        self.assertIs( sm.sms_current(), _SMStates.Finished())

        return


_Testsuite = unittest.makeSuite( _TESTCASE__SM)


class _SMSStatesEmlidReach:
    
    class Idle(SMState):
        
        def execute( self):
            return
        
        def is_enabled( self):
            return True


    class Connecting(SMState):

        def __init__( self):
            super().__init__()
            
            self.__ip_addr, self.__ip_portnbr = "10.0.0.13", 1962
            self.__is_error = False
            self.__is_open = False
            return
        
        def execute( self):
            try:
                self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
                self.__socket.settimeout( 10)
                self.__socket.connect( (self.__ip_addr, self.__ip_portnbr))
                self.__is_open = True
                
            except socket.timeout as e:
                UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                
            except ConnectionRefusedError as e:
                UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                self.__is_error = True
                
            except OSError as e:
                UsrEventLog().log_error( "Cannot connect to navi: '%s'!" % e, ThisName( self))
                self.__is_error = True
                
            return self
        
        def is_connected( self):
            return self.__is_open

        def is_error( self):
            return self.__is_error


    class Connected(SMState):
        
        def execute( self):
            return
        
        def is_disconnected( self):
            return True


    class Error(SMState):
        
        def execute( self):
            return
        
        def is_ackned( self):
            return True


class _TESTCASE__EMlidREach(unittest.TestCase):

    def test( self):
        """
        """
        print()

        _SMSTable = {\
            _SMSStatesEmlidReach.Idle():\
                { _SMSStatesEmlidReach.Idle().is_enabled: _SMSStatesEmlidReach.Connecting()},
                
            _SMSStatesEmlidReach.Connecting():\
                {\
                    _SMSStatesEmlidReach.Connecting().is_connected: _SMSStatesEmlidReach.Connected(),
                    _SMSStatesEmlidReach.Connecting().is_error: _SMSStatesEmlidReach.Error()
                },
                
            _SMSStatesEmlidReach.Connected():\
                { _SMSStatesEmlidReach.Connected().is_disconnected: _SMSStatesEmlidReach.Connecting()},

            _SMSStatesEmlidReach.Error():\
                { _SMSStatesEmlidReach.Error().is_ackned: _SMSStatesEmlidReach.Idle()},
        }
            
        sm = SM( _SMSTable, _SMSStatesEmlidReach.Idle())
        t = time.time()
        while time.time() - t < 2:
            print( "Current state = " + sm.sms_current().__class__.__name__)
            sm.execute()
            time.sleep( 0.100)
            
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__EMlidREach))


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



