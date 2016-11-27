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

from tau4.sweng import Singleton


class SM:

    """State Machine.

    An app can have more than one state machine. 
    But be aware, that state machine states are singletons and you have to decide at
    runtime, which state machine they belong to!
    """

    def __init__( self, sms_initial):
        self.__sms = sms_initial
        if not self.__sms.sm():
            self.__sms._sm_( self)
            
        return

    def execute( self):
        self.__sms.execute()
        return self
    
    def sms( self, arg=None):
        if arg is None:
            return self.__sms
        
        self.__sms = arg
        return self


class SMState(metaclass=Singleton):

    def __init__( self, sms):
        self.__sm = sms.sm() if sms else None
        return

    @abc.abstractmethod
    def execute( self):
        pass

    @abc.abstractmethod
    def is_condition_met( self):
        pass

    def select( self):
        self.sm().sms( self)

    def sm( self):
        return self.__sm
    
    def _sm_( self, sm):
        self.__sm = sm
        return self
    
    