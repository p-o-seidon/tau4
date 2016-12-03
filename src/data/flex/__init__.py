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


################################################################################
##
##  Version mit Mixins
##
##  Vorteil dieses Konzepts: Die Variable kann "komponiert" werden und das 
##  zur Compile Time.
##
##  Würden wir mit Vererbung arbeiten, müssten wir Code mehrfach schreiben. Ein
##  Beispiel:
##
##  Variable
##      VariableM...Soweit alles okay: Wir fügen Monitoring hinzu.
##      VariableC...Soweit alles okay: Wir fügen Clipping hinzu.
##      
##  VariableMC (oder VariableCM)....Nun geht's los: Wollen wir
##
##      Variable
##          VariableM
##              VariableMC..Wir müssen das CLipping neu hinzuprogrammieren, obwohl
##                          wir's schon programmiert haben (nämlich VariableC).
##
##      oder wollen wir Multiple Inheritance, indem wir VariableMC eben von 
##      VariableM und VariableC ableiten? In diesem Fall müssten wir dann aber 
##      zwei Ctoren aufrufen, die beide den Ctor von Variable ausführen, was sich 
##      im Laufzeitbedarf benerkbar machen wird.
##
################################################################################
class Variable:

    """Klasse für Instanzen von Variablen, die identifiziert, beschrieben und gelesen werden können - sonst nichts.
    
    Alle weiteren Features müssen in Subclasses per Mixin-Klassen "dazugemixt" werden.
    
    .. note::
        Der Typ der Variable, den sie die ganze Lebensdauer beibehält, 
        ist durch den Typ des Aktualparameters ``value`` bestimmt!        
    """
    
    @staticmethod
    def IsStored( id):
        """Instanz mit der ``id`` vorhanden?
        """
        return id in tau4.Objects

    
    @staticmethod
    def Instance( id):
        """Instanz mit der ``id`` anfordern.
        """
        return tau4.Objects( id)
    Restore = Instance
        
    @staticmethod
    def InstanceStore( id, v):
        """Instanz ``fv`` unter der ``id`` speichern.
        
        :param  id: Id der Variable. **Die Id muss eindeutig sein!**
        """
        v._id_( id)
        tau4.Objects().add( id, v)
        return
    Store = InstanceStore
        
    
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
    
    def __lshift__( self, other):
        """Neuen Value zuweisen.
        """
        self.value( other.value()) # 2016-10-31: Changed from self.value( other)

    def __repr__( self):
        return "%s: value=%s" % ( self.id(), self.value())
    
    def app2value( self, value):
        """Sollte von den Subclasses überschrieben werden!
        """
        self._value_( value)
        return
    
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

    def is_numeric( self):
        return isinstance( self.__type, (int, float))
    
    def _type_( self, arg):
        return self.__type( arg)
    
    def _value_( self, value=None):
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
    
    def value( self, value=None):
        if value is None:
            return self.value2app( self._value_())
        
        self._value_( self.app2value( value))
        return self

    def value2app( self, value):
        """Sollte von den Subclasses überschrieben werden!
        """
        return value
    
    def varbl2dict( self):
        """Liefert die wichtigsten Attribute als Dict.
        """
        d = {}
        d[ "value"] = self.value()
        return d


class _VariableMixin(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def app2value( self, value):
        pass
    
    @abc.abstractmethod
    def value2app( self, value):
        pass

    
class _VariableMixinClipper(_VariableMixin):
    
    """Mixin für Varible, der den Value clippt.
    
    Wird geclippt, werden alle hier angemeldeten Subscriber ausgeführt (Publishing).
    **ACHTUNG:** Das Publishing ist "flankengesteuert". Ist der Maximalwert bspw. 42,
    dann hat die Wertefolge 41, 42, 43, 44, 45 nur **ein** Publishing zur Folge!

    Wird nicht mehr geclippt, werden alle hier angemeldeten Subscriber ausgeführt.
    Auch dieses Publishing ist ebenfalls **flankengesteuert**.
    """
    
    def __init__( self, value_min, value_max):
        self.__value_min = value_min if value_min is not None else -sys.float_info.max
        self.__value_max = value_max if value_max is not None else sys.float_info.max
        return
    
    def app2value( self, value):
        """
        """
        value = max( min( value, self.__value_max), self.__value_min)
        return value
    
    def dict2varbl( self, d):
        self.value( d[ "value"])
        self.__min = d[ "value_min"]
        self.__max = d[ "value_max"]
        return self

    def is_clipping( self):
        return True
    
    def value2app( self, value):
        """
        """
        return value

    def value_min( self):
        return self.__value_min
    
    def value_max( self):
        return self.__value_max
    
    def varbl2dict( self):
        d = {}
        d[ "value"] = self.value()
        d[ "value_min"] = self.__min
        d[ "value_max"] = self.__max
        return d


class _VariableMixinDecorator(_VariableMixin):
    
    """Mixin-Klasse, die :py:class:`Variable` mit Label und Dimension versieht und den Wert formatieren kann.

    
    Folgendes wird durch diese Klasse möglich::

        +--------+------------+----+
        | Länge: | 123456.789 | mm |
        +--------+------------+----+
        
    2DO:
        Default valueformat ist falsch für Strings! Automatisch ändern? 
        Oder nur bei Exceptions in value_formatted()?
    """
    
    def __init__( self, varbllabel, varbldim, valueformat="%.3f"):
        self.__label = varbllabel
        self.__dim = varbldim
        self.__format = valueformat
        return
    
#    def __str__( self):
#        return "%s: %s %s" % (self.label(), self.value_formatted(), self.dim())
# ##### Ergibt bei Strings falsche Ergebnisse!

    def dim( self):
        return self.__dim
    
    def label( self, arg=None):
        if arg is None:
            return self.__label
        
        self.__label = arg
        return self
    
    def value_formatted( self):
        return self.__format % self.value()
    
    
class _VariableMixinMonitor(_VariableMixin):
    
    """Mixin-Klasse, die den Wert einer :py:class:`Variable` monitort und publisht, wenn der Wert geändert oder die Breichsgrenzen überschritten werden.
    """
    
    def __init__( self, value_min, value_max):
        self.__value_min = None
        if value_min is not None:
            if isinstance( value_min, str):
                self.__value_min = None
            else:
                self.__value_min = self._type_( value_min)

        self.__value_max = None
        if value_max is not None:
            if isinstance( value_max, str):
                self.__value_max = None
            else:
                self.__value_max = self._type_( value_max)
        
        self._tau4p_on_modified = PublisherChannel.Synch( self)

        self._tau4p_on_limit_violated = PublisherChannel.Synch( self)
        self._tau4p_on_limit_unviolated = PublisherChannel.Synch( self)

        self.__is_limit_violated = False
        return
    
    def app2value( self, value):
        """Wert schreiben.
        """
        self._tau4p_on_modified()

        is_limit_violated = False
        if self.__value_min is not None:
            is_limit_violated = not self.__value_min <= value
            
        if self.__value_max is not None:
            is_limit_violated = not value <= self.__value_max
            
        if is_limit_violated:
            if not self.__is_limit_violated:
                self._tau4p_on_limit_violated()
                self.__is_limit_violated = True
                
        else:
            if self.__is_limit_violated:
                self._tau4p_on_limit_unviolated()
                self.__is_limit_violated = False
                
        return value
    
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
    
    def value2app( self):
        """Wert lesen.
        """
        return self._value_()
    
    def value_max( self, arg=None):
        """Zugriff auf Grenzwert.
        
        Manche Apps müssen die Grenzwerte nachstellen können.
        """
        if arg is None:
            return self.__value_max
        
        self.__value_max = arg
        return self
            
    def value_min( self, arg=None):
        """Zugriff auf Grenzwert.
        
        Manche Apps müssen die Grenzwerte nachstellen können.
        """
        if arg is None:
            return self.__value_min
        
        self.__value_min = arg
        return self


class _VariableMixinPersistor(_VariableMixin):

    """Mixin-Klasse, die wichtige Daten persistieren kann.
    
    Was persistiert wird, bestimmt die :py:class:`Variable` durch die Methode .varbl2dict().
    Siehe auch :py:class:`_VariableMixinClipper::varbl2dict`.
    
    Der Name des Files, in dem die Daten gespeichert werden, wird gebildet aus 
    ``dirname`` der Id der Variable und der Endung ``.tau4varbl``.
    """
    
    def __init__( self, dirname="./"):
        self.__dirname = dirname
        
        self.__pathname = os.path.join( self.__dirname, str( self.id())) + ".tau4varbl"
        return
    
    def restore( self):
        try:
            with open( self.__pathname, "rt") as f:
                d = eval( f.read().strip())
                self.dict2varbl( d)
                
        except FileNotFoundError:
            self.store()

        return
    
    def store( self):
        with open( self.__pathname, "wt") as f:
            d = self.varbl2dict()
            print( str( d), file=f)

        return


class _VariableMixinPersistor2(_VariableMixin):

    """Mixin-Klasse, die wichtige Daten persistieren kann.
    
    Was persistiert wird, bestimmt die :py:class:`Variable` durch die Methode .varbl2dict().
    Siehe auch :py:class:`_VariableMixinClipper::varbl2dict`.
    
    Im Unterschied zu _VariableMixinPersistor wird kein File Name angegeben sondern 
    eine ConfigParser-Instanz.
    """
    
    def __init__( self, config_parser):
        self.__cp = config_parser
        
        self.__section_name= "tau4data.flex"
        return
    
    def restore( self):
        try:
            data = self.__cp.get( self.__section_name, self.id())
            d = eval( data)
            self.dict2varbl( d)
                
        except configparser.NoSectionError:
            self.__cp.add_section( self.__section_name)
            self.store()

        except configparser.NoOptionError:
            self.store()

        return
    
    def store( self):
        d = self.varbl2dict()
        self.__cp.set( "tau4data.flex", self.id(), str( d))
        self.__cp.write()
        return


class _VariableMixinTimeTracker(_VariableMixin):
    
    """Mixin-Klasse, die die Creation Time und die Modification Time einer :py:class:`Variable` erfasst.
    """
    
    def __init__( self):
        self.__ctime = time.time()
        self.__mtime = self.__ctime
        return
    
    def ctime( self):
        return self.__ctime
    
    def app2value( self, value):
        """Wert schreiben.
        """
        self.__mtime = time.time()
        return value
    
    def mtime( self):
        return self.__mtime
    
    def value2app( self, value):
        """Wert lesen.
        """
        return value

    
class VariableCl(_VariableMixinClipper, _VariableMixinMonitor, Variable, _VariableMixinDecorator):
    
    """Variable, die clippt.
    
    Die Variable clippt NUR. Sollen Bereichsüberschreitungen publiziert werden, 
    muss das Monitor-Mixin "bemüht" werden.
    """
    
    def __init__( self, *, id=-1, value, value_min=-sys.float_info.max, value_max=sys.float_info.max):
        _VariableMixinClipper.__init__( self, value_min=value_min, value_max=value_max)
        Variable.__init__( self, id=id, value=value)
        
        self.value( value)
                                        # Clipping sicherstellen
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        value = self.app2value( value)
                                        # Publisht bei Bereichsverletzungen NICHT.
                                        #   Ändert den Wert der Variable nicht.
        self._value_( value)
                                        # Wert der :py:class:`Variable` ändern.
        return self


class VariableClMo(_VariableMixinClipper, _VariableMixinMonitor, Variable):
    
    """Variable, die Änderungen publisht und clippt.
    """
    
    def __init__( self, *, id=-1, value, label, dim, value_min=-sys.float_info.max, value_max=sys.float_info.max):
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinClipper.__init__( self, value_min=value_min, value_max=value_max)
        Variable.__init__( self, id=id, value=value)
        return
    
    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        value = _VariableMixinClipper.app2value( self, value)
                                        # Publisht bei Bereichsverletzungen.
                                        #   Ändert den Wert der Variable nicht.
        self._value_( value)
                                        # Ändert den Wert der Variable.
        value = _VariableMixinMonitor.app2value( self, value)
                                        # Publisht die Änderung (Bereichsüberschreitungen
                                        #   gibt's wegen des Clippers keine).
        return self


class VariableDe(_VariableMixinDecorator, Variable):
    
    """Variable, die dekoriert ist.
    """
    
    def __init__( self, *, id=-1, value, label, dim="", format="%.3f"):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim, format)
        return
    
    def app2value( self, value):
        return value

    def value2app( self, value):
        return value


class VariableDeClMo(_VariableMixinClipper, _VariableMixinMonitor, Variable, _VariableMixinDecorator):
    
    """Variable, die dekoriert ist, Änderungen publisht und clippt.
    """
    
    def __init__( self, *, id=-1, value, label, dim, value_min=-sys.float_info.max, value_max=sys.float_info.max):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinClipper.__init__( self, value_min=value_min, value_max=value_max)
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        value = _VariableMixinClipper.app2value( self, value)
                                        # Publisht bei Bereichsverletzungen.
                                        #   Ändert den Wert der Variable nicht.
        self._value_( value)
                                        # Ändert den Wert der Variable.
        value = _VariableMixinMonitor.app2value( self, value)
                                        # Publisht die Änderung (Bereichsüberschreitungen
                                        #   gibt's wegen des Clippers keine).
        return self


class VariableDeClMoPe(_VariableMixinClipper, _VariableMixinMonitor, Variable, _VariableMixinDecorator, _VariableMixinPersistor):
    
    """Variable, die dekoriert ist, Änderungen publisht und clippt.
    """
    
    def __init__( self, *, id=-1, value, label, dim, value_min=-sys.float_info.max, value_max=sys.float_info.max):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinClipper.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinPersistor.__init__( self)
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        value = _VariableMixinClipper.app2value( self, value)
                                        # Publisht bei Bereichsverletzungen.
                                        #   Ändert den Wert der Variable nicht.
        self._value_( value)
                                        # Ändert den Wert der Variable.
        value = _VariableMixinMonitor.app2value( self, value)
                                        # Publisht die Änderung (Bereichsüberschreitungen
                                        #   gibt's wegen des Clippers keine).
        return self


class VariableDeMo(_VariableMixinDecorator, _VariableMixinMonitor, Variable):
    
    """Variable, die dekoriert ist und Änderungen publisht.
    """
    
    def __init__( self, *, id=-1, value, label, dim="", value_min=None, value_max=None, format="%.3f"):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim, format)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        return

    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
        dont_care = _VariableMixinMonitor.app2value( self, value)
        return self


class VariableDeMoTi(_VariableMixinDecorator, _VariableMixinMonitor, _VariableMixinTimeTracker, Variable):
    
    """Variable, die dekoriert ist und Änderungen publisht und die Änderungszeit erfasst.
    """
    
    def __init__( self, *, id=-1, value, label, dim, value_min, value_max, format="%.3f"):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim, format)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinTimeTracker.__init__( self)
        return

    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
        dont_care = _VariableMixinTimeTracker.app2value( self, value)
        dont_care = _VariableMixinMonitor.app2value( self, value)
        return self


class VariableDeMoPe(_VariableMixinMonitor, Variable, _VariableMixinDecorator, _VariableMixinPersistor):
    
    """Variable, die dekoriert ist, Änderungen publisht und persitent ist.
    """
    
    def __init__( self, *, id=-1, value, dirname, label, dim, value_min=-sys.float_info.max, value_max=sys.float_info.max):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinPersistor.__init__( self, dirname)
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
                                        # Ändert den Wert der Variable.
        value = _VariableMixinMonitor.app2value( self, self._value_())
                                        # Publisht die Änderung und eventuelle
                                        #   Bereichsüberschreitungen.
        return self


class VariableDePe2(Variable, _VariableMixinDecorator, _VariableMixinPersistor2):
    
    """Variable, die dekoriert ist und persistent ist.
    """
    
    def __init__( self, *, id=-1, value, config_parser, label, dim, value_min=None, value_max=None):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim)
        _VariableMixinPersistor2.__init__( self, config_parser)
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def app2value( self, value):
        """Wert schreiben.
        """
        return value

    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
                                        # Ändert den Wert der Variable.
        return self

    def value2app( self):
        """Wert lesen.
        """
        return self._value_()



class VariableDeMoPe2(_VariableMixinMonitor, Variable, _VariableMixinDecorator, _VariableMixinPersistor2):
    
    """Variable, die dekoriert ist, Änderungen publisht und persistent ist.
    """
    
    def __init__( self, *, id=-1, value, config_parser, label, dim, value_min=None, value_max=None):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinDecorator.__init__( self, label, dim)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        _VariableMixinPersistor2.__init__( self, config_parser)
        return
    
    def __str__( self):
        return "%s: %s %s" % (self.label(), self.value(), self.dim())
    
    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
                                        # Ändert den Wert der Variable.
        value = _VariableMixinMonitor.app2value( self, value)
                                        # Publisht die Änderung und eventuelle
                                        #   Bereichsüberschreitungen.
        return self


class VariableDeTi(_VariableMixinDecorator, _VariableMixinTimeTracker, Variable):
    
    """Variable, die dekoriert ist und Ädie Änderungszeit erfasst.
    """
    
    def __init__( self, *, id=-1, value, label, dim, value_min, value_max, format="%.3f"):
        _VariableMixinDecorator.__init__( self, label, dim, format)
        _VariableMixinTimeTracker.__init__( self)
        Variable.__init__( self, id=id, value=value)
        return

    def value( self, value=None):
        """Wert R/W.
        
        .. note::
            Wenn Bereichsüberschreitungen publiziert werden, ist der Wert der Variablen 
            noch nicht verändert worden!
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        dont_care = _VariableMixinTimeTracker.app2value( self, value)
        self._value_( value)
        return self


class VariableMo(_VariableMixinMonitor, Variable):
    
    """Variable, die Änderungen publisht.
    """
    
    def __init__( self, *, id=-1, value, value_min=None, value_max=None):
        Variable.__init__( self, id=id, value=value)
        _VariableMixinMonitor.__init__( self, value_min=value_min, value_max=value_max)
        return

    def value( self, value=None):
        """Wert R/W.
        """
        ##  Lesen
        #
        if value is None:
            return self._value_()
        
        ##  Schreiben
        #
        self._value_( value)
                                        # Ändert den Wert.
        value = _VariableMixinMonitor.app2value( self, value)
                                        # Publisht die Änderung.
        return self
    

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

