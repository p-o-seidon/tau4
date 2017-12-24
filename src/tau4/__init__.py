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
import threading
import time
import uuid

from tau4.oop import Singleton
from tau4.setup.setup4app import Setup4 

__VERSION_NUMBER_MAJOR = 0
__VERSION_NUMBER_MINOR = 3
__VERSION_NUMBER_REV = 0


class App(Singleton):
    
    def __init__( self):
        self.__setup = None
        return
    
    def setup( self, setup: Setup4=None) -> Setup4:
        if setup is None:
            return self.__setup
        
        self.__setup = setup
        return self


class DictWithUniqueKeys(dict):

    """Dict aus Lists, das eine Exception wirft, wenn der Key nicht eindeutig ist.
    """

    def __setitem__( self, key, value):
        if key in self:
            raise KeyError( "_DictWithUniqueKeys::__setitem__(): Key '%s' already set!" % key)

        super().__setitem__( key, value)
        return


class Id:

    _PublishedIDs = set()

    def __init__( self, id=None):
        if id in (None, ""):
            id = uuid.uuid4()

        self.__id = str( id)
        if self.__id in Id._PublishedIDs:
            raise KeyError( "Id '%s' is already taken! " % self.__id)

        Id._PublishedIDs.add( self.__id)
        return

    def __eq__( self, other):
        return self.__id == other

    def __hash__( self):
        return hash( str( self))

    def __int__( self):
        return int( self.__id)

    def __lt__( self, other):
        return str( self) < str( other)

    def __ne__( self, other):
        return not self == other

    def __repr__( self):
        return "%s( id='%s')" % (self.__class__.__name__, self)

    def __str__( self):
        return self.__id


class _RevisionHistory:

    def __str__( self):
        return \
"""%s:
    2016-04-19:
        Created.

""" % __file__


class Object(object):

    """Base Class aller TAU4-Klassen mit folgenden Features: Identifikation, Klassenname.

    \param  id
        Id des Objects.

    \note
        Das Object wird nicht automatisch gespeichert in Objects (Singleton _Objects)!
    """

    def __init__( self, *, id: Id):
        self.__id = id
        return

    def classname( self):
        return self.__class__.__name__

    def id( self):
        return self.__id


class ObjectConfigurable(Object):

    """Base Class aller TAU4-Klassen mit folgenden Features: Identifikation, Klassenname, Setup.

    \param  id
        Id des Objects.

    \param  setupdict_default (optional)
        Default Key-Value Pair, das mit Daten aus dem File "setup.ID.dat"
        überschieben wird, wenn es so ein File gibt. Existiert dieses File nicht,
        wird es angelegt - Inhalt: setupdict_default.

    \note
        Das Object wird nicht automatisch gespeichert in Objects (Singleton _Objects)!
    """

    def __init__( self, *, id: Id, setupdict_default=None):
        super().__init__( id=id)
        self.__setup = None
        if setupdict_default:
            self.__setup = _ObjectSetup( id="setup.%s.dat" % id, dict_default=setupdict_default)

        return

    def setupdict_update( self, setupdict):
        """Update existierender Key-Value Pairs oder Erweiterung um neue.
        """
        if not self.__setup:
            self.__setup = _ObjectSetup( id="setup.%s.dat" % id, dict_default=setupdict)
            return self

        self.__setup._update_( setupdict)
        return self

    def setupvalue( self, key=None):
        """Liefert den Wert zum Parameter "key".

        \param  key
            Key, dessen Value geliefert werden soll.

        \par    Usage
            \code
                cycletime = self.setupvalue( "cycletime")
            \endcode
        """
        if key is None:
            return self.__setup

        return self.__setup.value( key)

    def setup_store( self):
        self.__setup.store()
        return self


class _ObjectSetup(Object):

    """Setup zu einem Object (siehe Object.setup()).
    """

    def __init__( self, id, dict_default):
        super().__init__( id=id)

        self.__dict = dict_default

        self.__pathname = self.id()

        self._restore_()
        return

    def _restore_( self):
        try:
            with open( self.__pathname, "r") as f:
                self.__dict.update( eval( f.read()))

        except (FileNotFoundError, SyntaxError) as e:
            self.store()

        return

    def store( self):
        with open( self.__pathname, "w") as f:
            f.write( str( self.__dict))

        return

    def _update_( self, dict):
        self.__dict.update( dict)

    def value( self, key):
        return self.__dict[ key]


class _Objects:

    """Stores all Object instances.
    """

    def __init__( self):
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
        """Neues Objekt in den Speicher _Objects aufnehmen.

        \throws KeyError
            wenn folgende Bedingungen **nicht** erfüllt sind:
            -   **ident** ist eindeutig.

        \throws ValueError
            wenn folgende Bedingungen **nicht** erfüllt sind:
            -   **ident** ist kein String und kein Integer.
        """
        with self.__lock:
            if not isinstance( ident, (str, bytes, int)):
                raise ValueError( "instance.ident() must be a string, but is a " + str( type( ident)))

            if ident in self.__instances:
                raise KeyError( "instance.ident() = '%s' isn't unique!" % ident)

            self.__instances[ ident] = instance
            return self

    def remove( self, ident):
        """Objekt aus dem Speicher _Objects entfernen.
        """
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

