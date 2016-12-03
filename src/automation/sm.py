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

import abc

from tau4 import ThisName
from tau4.datalogging import UsrEventLog
from tau4.sweng import Singleton


class SM:

    """State Machine.

    An app can have more than one state machine. 
    But be aware, that state machine states are singletons and you have to decide at
    runtime, which state machine they belong to!
    """

    def __init__( self, sms_table, sms_initial, sms_common_data):
        self.__sms_table = sms_table
        self.__sms_current = sms_initial
        self.__sms_common_data = sms_common_data
        
        self.__sms_current.open( self.__sms_common_data)
        return

    def execute( self):
        self.__sms_current.execute()
        try:
            for method in self.__sms_table[ self.__sms_current]:
                if method():
                    self.__sms_current.close()
                                                    # Close this state
                    self.__sms_current = self.__sms_table[ self.__sms_current][ method]
                                                    # Get the next state and set 
                                                    #   it as the (new) current one
                    self.__sms_current.open( self.__sms_common_data)
                                                    # Open the new current state
                    break
                
        except KeyError as e:
            UsrEventLog().log_error( e, ThisName( self))
            
        return self
    
    def sms_current( self):
        return self.__sms_current
    

class SMState(metaclass=Singleton):

    def __init__( self):
        self.__common = None
        self.__is_open = False
        return

    def close( self):
        """Close the state.
        
        May be overridden, but doesn't need to be.
        """
        assert self.__is_open
        self.__is_open = False
        return
    
    @abc.abstractmethod
    def execute( self):
        assert self.__is_open

    def open( self, common):
        """Open the state.
        
        May be overridden, but doesn't need to be.
        
        In case, the overriding method needs to call this class' method!
        """
        self.__common = common
        self.__is_open = True
        return self
    
    def common( self):
        return self.__common
    