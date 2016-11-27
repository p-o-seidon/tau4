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


import logging; _Logger = logging.getLogger()

import abc
import configparser
import os
import sys
import tau4
from tau4.sweng import PublisherChannel, Singleton

import time


class iUniVar(metaclass=abc.ABCMeta):

    """
    
    Wir folgen hier dem Decorator Pattern (s. z.B. https://de.wikipedia.org/wiki/Decorator).
    Diese Klasse ist also die Root der Hierarchie.
    """
    
    @abc.abstractclassmethod
    def value( self, value=None):
        pass
    

class Univar(iUniVar):

    """Klasse für Instanzen von Variablen, die identifiziert, beschrieben und gelesen werden können - sonst nichts.
    
    Nach dem Decorator Pattern ist das hier die konkrete Komponente, die zu dekorieren ist
    
    .. note::
        Der Typ der Variable, den sie die ganze Lebensdauer beibehält, 
        ist durch den Typ des Aktualparameters ``value`` bestimmt!        
    """
    
    @staticmethod
    def New( *, id=-1, value):
        return Univar( id=id, value=value)

    @staticmethod
    def Restore( id):
        """Instanz mit der ``id`` anfordern.
        """
        return tau4.Objects( id)
        
    @staticmethod
    def Store( id, v):
        """Instanz ``fv`` unter der ``id`` speichern.
        
        :param  id: Id der Variable. **Die Id muss eindeutig sein!**
        """
        v._id_( id)
        tau4.Objects().add( id, v)
        return
        
    
    def __init__( self, *, id=-1, value):
        self.__id = id
        self.__value = value

        self.__type = type( value)
        
        return
    
    def __eq__( self, other):
        try:
            return self.__value == other.__value
        
        except AttributeError:
            return self.__value == other
        
    def __lshift__( self, other):
        """Übernimmt einen Zahlenwert.
        """
        try:
            other = other.value()
        
        finally:
            self.value( other)
            
        return self
            
    
    def __ne__( self, other):
        return not self == other
    
    def __repr__( self):
        return self.id()
    
    def dict2varbl( self, d):
        """Daten aus einem Dict übernehmen.
        
        Wird von :py:class:`Persistor` verwendet.
        """
        self.value( d[ "value"])
        return self
    
    def id( self):
        """Id der Variable.
        """
        return self.__id

    def _id_( self, id=None):
        if id is None:
            return self.__id
        
        self.__id = id
        return self
        
    def is_clipping( self):
        """Kann diese Instanz von Variable oder einer ihrer Subclasses clippen?
        """
        return False
    
    def _type_( self, arg):
        return self.__type( arg)
    
    def value( self, value=None):
        """R/W the value.
        
        .. todo::
            2DO: Funzt für Boolean noch nicht: Aus "False" wird True.
        """
        if value is None:
            return self.__value
        
        if isinstance( value, self.__type):
            self.__value = value
            
        else:
            self.__value = self.__type( value)
                                            # Diese Zeile funzt z.B. bei 
                                            #   datetime.date-Objekten NICHT.
            
        return self

    def varbl2dict( self):
        """Liefert die wichtigsten Attribute als Dict.
        """
        d = {}
        d[ "value"] = self.value()
        return d


class _UnivarDecorator(Univar):
    
    def __init__( self, univar):
        self._univar = univar
        return

    def id( self):
        return self._univar.id()
    
    def reg_tau4s_on_limit_violated( self, tau4s):
        return self._univar.reg_tau4s_on_limit_violated( tau4s)
    
    def reg_tau4s_on_limit_unviolated( self, tau4s):
        return self._univar.reg_tau4s_on_limit_unviolated( tau4s)
    
    def value( self,value=None):
        if value is None:
            return self._univar.value()
        
        self._univar.value( value)
        return
    

class UnivarD(_UnivarDecorator):

    @staticmethod    
    def New( *, id, value, value_bounds, label, dimension, value_format="%.3f"):
        return UnivarD( univar=Univar( id=id, value=value), label=label, dimension=dimension, value_format=value_format)

    
    def __init__( self, *, univar, label, dimension, value_format):
        super().__init__( univar)

        self.__label = label
        self.__dimension = dimension
        self.__format = value_format
        return

    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value_formatted(), self.dimension())

    def dimension( self):
        return self.__dimension
    
    def label( self, arg=None):
        if arg is None:
            return self.__label
        
        self.__label = arg
        return self
    
    def value_formatted( self):
        return self.__format % self.value()
    

class UnivarM(_UnivarDecorator):
    
    @staticmethod    
    def New( *, id=-1, value, value_bounds=(None, None), value_format="%.3f"):
        return UnivarM( Univar( id=id, value=value), value_bounds=value_bounds, value_format=value_format)


    def __init__( self, univar, value_bounds, value_format="%.3f"):
        super().__init__( univar)
        
        self.__value_format = value_format
        self.__value_bounds = list( value_bounds)

        self._tau4p_on_modified = PublisherChannel.Synch( self)
    
        self._tau4p_on_limit_violated = PublisherChannel.Synch( self)
        self._tau4p_on_limit_unviolated = PublisherChannel.Synch( self)
    
        self.__is_limit_violated = False
        return

    def reg_tau4s_on_limit_violated( self, tau4s):
        """Subscriber anmelden, die über Bereichsüberschreitungen des Wertes informiert werden wollen.
        
        .. note::
            Damit das funktioniert, muss ein Scaler per :py:meth:`value_mangler_add` übergeben worden sein.
        """
        self._tau4p_on_limit_violated += tau4s
        return self
    
    def reg_tau4s_on_limit_unviolated( self, tau4s):
        """Subscriber anmelden, die über Bereichsgrenzenunterschreitungen des Wertes informiert werden wollen.
        
        .. note::
            Damit das funktioniert, muss ein Scaler per :py:meth:`value_mangler_add` übergeben worden sein.
        """
        self._tau4p_on_limit_unviolated += tau4s
        return self
 
    def reg_tau4s_on_modified( self, tau4s):
        """Subscriber anmelden, die über Änderungen des Wertes informiert werden wollen.
        """
        self._tau4p_on_modified += tau4s
        return self
    
    def ureg_tau4s_on_limit_violated( self, tau4s):
        """Subscriber abmelden.
        """
        self._tau4p_on_limit_violated -= tau4s
        return self
    
    def ureg_tau4s_on_limit_unviolated( self, tau4s):
        """Subscriber abmelden.
        """
        self._tau4p_on_limit_unviolated -= tau4s
        return self
    
    def ureg_tau4s_on_modified( self, tau4s):
        """Subscriber abmelden.
        """
        self._tau4p_on_modified -= tau4s
        return self
    
    def value( self, value=None):
        """Wert R/W.
        
        Bereichsüberschreitungen werden publiziert.
        """
        ##  Lesen
        #
        if value is None:
            return self._univar.value()
        
        ##  Schreiben
        #
        self._univar.value( value)
        
        ### Monitoren
        #
        self._tau4p_on_modified()

        min, max = self.__value_bounds
        is_limit_violated = False
        if min is not None:
            is_limit_violated = not min <= value
            
        if max is not None:
            is_limit_violated = not value <= max
            
        if is_limit_violated:
            if not self.__is_limit_violated:
                self._tau4p_on_limit_violated()
                self.__is_limit_violated = True
                
        else:
            if self.__is_limit_violated:
                self._tau4p_on_limit_unviolated()
                self.__is_limit_violated = False
                
        return self

    def value_max( self, arg=None):
        """Zugriff auf Grenzwert.
        
        Manche Apps müssen die Grenzwerte nachstellen können.
        """
        if arg is None:
            return self.__value_bounds[ 1]
        
        self.__value_bounds[ 1] = arg
        return self
            
    def value_min( self, arg=None):
        """Zugriff auf Grenzwert.
        
        Manche Apps müssen die Grenzwerte nachstellen können.
        """
        if arg is None:
            return self.__value_bounds[ 0]
        
        self.__value_bounds[ 0] = arg
        return self

    
class UnivarMT(_UnivarDecorator):
    
    """Univar, that's Monitoring and Timestamping.
    """
    
    @staticmethod    
    def New( *, id=-1, value, value_bounds=(None, None), value_format="%.3f"):
        uv = UnivarT( id=id, value=value)
        uvT = UnivarT( univar=uv)
        uvMT = UnivarM( univar=uvT, value_bounds=value_bounds, value_format=value_format)
        return uvMT


    def __init__( self, univar):
        super().__init__( univar)
        return


class UnivarC(_UnivarDecorator):
    
    """Variable, die clippt.
    
    Die Variable clippt NUR, sie publiziert nicht.
    """
    
    @staticmethod    
    def New( *, id, value, value_bounds, value_format="%.3f"):
        return UnivarC( univar=Univar( id=id, value=value), value_bounds=value_bounds, value_format=value_format)

    def __init__( self, *, univar, value_bounds, value_format):
        super().__init__(univar)
        
        if None in value_bounds:
            raise ValueError( "Bounds must not be 'None'!")
        
        self.__value_bounds = value_bounds
        self.value( self.value())
                                        # Clipping sicherstellen
        return
    
    def dict2varbl( self, d):
        self.value( d[ "value"])
        self.__value_bounds = d[ "value_min"], d[ "value_max"]
        return self

    def is_clipping( self):
        return True
    
    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._univar.value()
        
        ##  Clippen und schreiben
        #
        i, x = self.__value_bounds
        value = max( min( value, x), i)
        self._univar.value( value)

        return self

    def value_min( self):
        return self.__value_bounds[ 0]
    
    def value_max( self):
        return self.__value_bounds[ 1]
    
    def varbl2dict( self):
        d = {}
        d[ "value"] = self.value()
        d[ "value_bounds"] = self.__value_bounds
        return d


class UnivarCM(_UnivarDecorator):
    
    @staticmethod
    def New( *, id=-1, value, value_bounds=(None, None), value_format="%.3f"):
        return UnivarC( univar=UnivarM( univar=Univar( id=id, value=value), value_bounds=value_bounds, value_format=value_format), value_bounds=value_bounds, value_format=value_format)

    def __init__( self, univar):
        super().__init__( univar)
        return
        
    
class UnivarDM(_UnivarDecorator):
    
    @staticmethod
    def New( *, id=-1, value, value_bounds=(None, None), value_format="%.3f", label, dimension):
        return UnivarD( univar=UnivarM( univar=Univar( id=id, value=value), value_bounds=value_bounds, value_format=value_format), label=label, dimension=dimension, value_format=value_format)

    def __init__( self, univar):
        super().__init__( univar)
        return


class UnivarDCM(_UnivarDecorator):
    
    @staticmethod
    def New( *, id, value, value_bounds, value_format="%.3f", label, dimension):
        uv = Univar( id=id, value=value)
        uvM = UnivarM( univar=uv, value_bounds=value_bounds, value_format=value_format)
        uvCM = UnivarC( univar=uvM, value_bounds=value_bounds, value_format=value_format)
        uvDCM = UnivarD( univar=uvCM, label=label, dimension=dimension, value_format=value_format)
        return uvDCM


    def __init__( self, univar):
        super().__init__( univar)
        return


class UnivarT(_UnivarDecorator):

    @staticmethod    
    def New( *, id, value, value_bounds, value_format="%.3f"):
        return UnivarT( univar=Univar( id=id, value=value), value_format=value_format)

    
    def __init__( self, *, univar, label, dimension, value_format):
        super().__init__( univar)

        self.__ctime = time.time()
        self.__dimension = dimension
        self.__format = value_format
        return

    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value_formatted(), self.dimension())

    def ctime( self):
        """Creation time.
        """
        return self.__ctime
    
    def mtime( self):
        """Modification time.
        """
        return self.__mtime

    def value_formatted( self):
        return self.__format % self.value()
    
    def value( self, value=None):
        if value is None:
            return self._univar.value()
        
        self._univar.value( value)
        self.__mtime = time.time()
        return
    
    
class VarblCat:
    
    def __init__( self, *, id):
        self.__id = id
        self.__varbls = {}
        
        VarblCats().varblcat_add( self)
        return
        
    def varbl_add( self, varbl):
        if varbl.id() in self.__varbls.keys():
            raise KeyError( "Varbl '%s' of type '%s' already exists in VarblCat '%s. " % (varbl.id(), varbl.__class__.__name__, self.id()))
        
        self.__varbls[ varbl.id()] = varbl
        return self
    
    def varbl( self, id):
        return self.__varbls[ id]


class VarblCats(metaclass=Singleton):
    
    def __init__( self):
        self.__varblcats = {}
        return
    
    def varblcat_add( self, varblcat):
        if varblcat.id() in self.__varblcats.keys():
            raise KeyError( "VarblCat '%s' of type '%s' already exists in VarblCats. " % (varblcat.id(), varblcat.__class__.__name__))
        
        self.__varblcats[ varblcat.id()] = varblcat
        return self

