#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
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


import copy
import sys
import uuid

#from _4all import _settings


__VERSION_NUMBER_MAJOR = 0
__VERSION_NUMBER_MINOR = 3
__VERSION_NUMBER_REV = 0


class _RevisionHistory:
    
    def __str__( self):
        return \
"""%s:
    2016-04-19:
        Created.
    
""" % __file__


class _Objects:

    """Stores all Object instances.
    """
    
    def __init__( self):
        import threading

        self.__instances = {}
        self.__lock = threading.RLock()
        return
    
    def __call__( self, ident=None):
        with self.__lock:
            if ident is None:
                return self
            
            return self.__instances[ ident]
        
    def __contains__( self, ident):
        return ident in self.__instances
    
    def __len__( self):
        return len( self.__instances)
    
    def add( self, ident, instance):
        """Neues Objekt aufnehmen.
        
        \throws KeyError    wenn folgende Bedingungen **nicht** erfüllt sind: 
                            \li **ident** ist eindeutig.

        \throws ValueError  wenn folgende Bedingungen **nicht** erfüllt sind: 
                            \li **ident** ist ein String oder ein Integer\.
        """
        with self.__lock:
            if not isinstance( ident, (str, bytes, int)):
                raise ValueError( "instance.ident() must be a base string, but is a " + str( type( ident)))
            
            if ident in self.__instances:
                raise KeyError( "instance.ident() = '%s' isn't unique!" % ident)
                
            self.__instances[ ident] = instance
            return self
        
    def remove( self, ident):
        with self.__lock:
            del self.__instances[ ident]

    def lock( self):
        return self.__lock.acquire()
    
    def unlock( self):
        return self.__lock.release()
    
    
Objects = _Objects()


def ThisName( self=None, timestamp=False):
    """Name of the currently executed method or function.

    :param  self:   Instance of class of calling method.
                    Used to document the class the method belongs to.
    """
    level = 1
    if self is not None:
        if timestamp:
            return "[%f] %s::%s" % (time.time(), self.__class__.__name__, sys._getframe( level).f_code.co_name)

        return "%s::%s" % (self.__class__.__name__, sys._getframe( level).f_code.co_name)

    else:
        if timestamp:
            return "[%f] %s" % (time.time(), sys._getframe( level).f_code.co_name)

        return sys._getframe( level).f_code.co_name

    assert not "Trapped! "

        
class VersionInfo:
    
    """Revision history of all the tau4 packages found.
    """

    def __init__( self):
        self._version_tuple = ( __VERSION_NUMBER_MAJOR, __VERSION_NUMBER_MINOR, __VERSION_NUMBER_REV)
        return

    def __str__( self):
        return ".".join( self._version_tuple)

    def as_str( self):
        return str( self)
    
    def as_tuple( self):
        return self._version_tuple
    
    def changes( self):
        pn = "CHANGES.txt"
        try:
            f = open( pn, "rb")
            text = f.read()
            
        except IOError as e:
            text = u"Could not open file '%s' containing all changes of this version: '%s'" % (pn, e)

        return text

    def number_major( self):
        return self._version_tuple[ 0]
        
    def number_minor( self):
        return self._version_tuple[ 1]
        
    def number_revision( self):
        return self._version_tuple[ 2]
        
