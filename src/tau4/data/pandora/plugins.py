#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
#
#   This file is part of pandora.
#
#   pandora is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   pandora is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with pandora. If not, see <http://www.gnu.org/licenses/>.


import abc
from collections import OrderedDict
import inspect
import sys

from tau4.oop import PublisherChannel, Singleton


class _Plugins(OrderedDict):

    def __setitem__( self, id, plugin):
        if id in self:
            raise KeyError( "A plugin '%s' has been appended already!" % id)

        OrderedDict.__setitem__( self, id, plugin)
        return self

    def append( self, plugin):
        self[ plugin.id()] = plugin
        return self

    def remove( self, plugin_id):
        del self[ id]
        return self


class Plugin(metaclass=abc.ABCMeta):

    def __init__( self, id):
        self.__id = id
        self.__value = None
        return

    def id( self):
        return self.__id

    @abc.abstractmethod
    def is_clipping( self):
        pass

    @abc.abstractmethod
    def process_value( self, value):
        """Process data in plugin and - IMPORTANT - return the result.

        .. note::
            **IMPORTANT: This method MUST return the result!**
        """
        pass

    def value( self, value=None):
        if value is None:
            return self.__value

        self.__value = value
        return self.__value


class Mapper4Numbers(Plugin):

    class _Point2D:

        def __init__( self, x, y):
            self._x = x
            self._y = y
            return


    class _Line2D:

        def __init__( self, P, Q):
            self._P = P
            self._Q = Q

            self._k = (self._Q._y - self._P._y)/(self._Q._x - self._P._x)
            return

        def y( self, x):
            y = self._k * (x - self._P._x) + self._P._y
            return y


    def __init__( self, *, id, x1, y1, x2, y2):
        super().__init__( id)

        self.__line = self._Line2D( self._Point2D( x1, y1), self._Point2D( x2, y2))
        return

    def is_clipping( self):
        return False

    def process_value( self, value):
        value = self.__line.y( value)
        self.value( value)
        return value


class Monitor(Plugin):

    def __init__( self, *, id, callable=None):
        super().__init__( id)
        self.__on_data_changed = PublisherChannel.Synch( self)
        if callable:
            self.callable_append( callable)

        return

    def callable_append( self, callable):
        assert len( inspect.getargspec( callable).args) == 2, "Your callable must accept one arg besides 'self'!"
        self.__on_data_changed += callable
        return self

    def callable_remove( self, callable):
        self.__on_data_changed -= callable
        return self

    def is_clipping( self):
        return False

    def process_value( self, value):
        """
        NOTE:
            It is essentially important that the subscriber calls the monitor to
            ask for its value and not the box!

            So, don't do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    assert isinstance( self.__model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                    return

                Here, the model would be the box, which leads to wrong
                results: The box yet hasn't updated its value by the plugin's value!


            Instead, do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    model = tau4pc.client()
                    assert isinstance( model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                    return

                Here, the model would be the current plugin, which returns the
                valid value!

        """
        self.value( value)
        self.__on_data_changed()
        return value


class Clipper(Monitor):

    """Nimmt einen Wert und beschneidet ihn, wenn nötig.

    Clients können sich beim Clipper registrieren, um den geclippten Wert zu bekommen.

    \note
        Diese Klasse selbst kann gar nicht clippen, sondern muss abgeleitet
        werden. Siehe bspw. Clipper4Numbers.
    """

    def __init__( self, *, id):
        super().__init__( id=id, callable=None)

        self._is_out_of_bounds = False

        self._value_unclipped = None

        self._on_data_clipped = PublisherChannel.Synch( self)
        self._on_data_not_clipped = PublisherChannel.Synch( self)
        return

    def callable_on_out_of_bounds_append( self, callable_on_out_of_bounds):
        """Callable wird ausgeführt, wenn Daten geclippt worden sind, vorher aber within bounds waren (Flankensteuerung).
        """
        assert len( inspect.getargspec( callable_on_out_of_bounds).args) == 2, "Your callable_on_out_of_bounds must accept one arg besides 'self'!"
        self._on_data_clipped += callable_on_out_of_bounds
        return self

    def callable_on_out_of_bounds_remove( self, callable_on_out_of_bounds):
        self._on_data_clipped -= callable_on_out_of_bounds
        return self

    def callable_on_within_bounds_append( self, callable_on_within_bounds):
        """Callable wird ausgeführt, wenn Daten nicht geclippt worden sind, vorher aber out of bounds waren (Flankensteuerung).
        """
        assert len( inspect.getargspec( callable_on_within_bounds).args) == 2, "Your callable_on_within_bounds must accept one arg besides 'self'!"
        self._on_data_not_clipped += callable_on_within_bounds
        return self

    def callable_on_within_bounds_remove( self, callable_on_within_bounds):
        self._on_data_not_clipped -= callable_on_within_bounds
        return self

    def is_clipping( self):
        """True.
        """
        return True

    def value_unclipped( self):
        """Daten, bevor sie geclippt worden sind.
        """
        return self._value_unclipped


class Clipper4Numbers(Clipper):

    """Clipper nur für numerische Wrete.
    """

    def __init__( self, *, id, bounds=(-sys.float_info.max, sys.float_info.max)):
        super().__init__( id=id)
        self.__min, self.__max = bounds

        return

    def bounds( self, bounds):
        self.__min, self.__max = bounds
        return self

    def min( self):
        return self.__min

    def max( self):
        return self.__max

    def process_value( self, value):
        _type = type( value)
        self._value_unclipped = value

        is_clipped = False
        if not self.__min <= value:
            value = _type( self.__min)
            is_clipped = True

        if not value <= self.__max:
            value = _type( self.__max)
            is_clipped = True

        self.value( value)

        if is_clipped:
            if not self._is_out_of_bounds:
                if self._on_data_clipped:
                    self._on_data_clipped()

                self._is_out_of_bounds = True

        else:
            if self._is_out_of_bounds:
                if self._on_data_not_clipped:
                    self._on_data_not_clipped()

                self._is_out_of_bounds = False

        return value


class Guard(Plugin):

    """Bereichsgrenzenüberwachung - eine Art Clipper, der nicht clippt.
    """

    def __init__( self, *, id):
        super().__init__( id=id)

        self._is_out_of_bounds = False

        self._on_data_out_of_bounds = PublisherChannel.Synch( self)
        self._on_data_within_bounds = PublisherChannel.Synch( self)
        return

    def callable_on_out_of_bounds_append( self, callable_on_out_of_bounds):
        """Callable wird ausgeführt, wenn Daten Grenzen überschreiten, vorher aber within bounds waren (Flankensteuerung).
        """
        assert len( inspect.getargspec( callable_on_out_of_bounds).args) == 2, "Your callable_on_out_of_bounds must accept one arg besides 'self'!"
        self._on_data_out_of_bounds += callable_on_out_of_bounds
        self._is_out_of_bounds = False
        return self

    def callable_on_out_of_bounds_remove( self, callable_on_out_of_bounds):
        self._on_data_out_of_bounds -= callable_on_out_of_bounds
        return self

    def callable_on_within_bounds_append( self, callable_on_within_bounds):
        """Callable wird ausgeführt, wenn Daten innerhalb der Grenzen sind, vorher aber out of bounds waren (Flankensteuerung).
        """
        assert len( inspect.getargspec( callable_on_within_bounds).args) == 2, "Your callable_on_within_bounds must accept one arg besides 'self'!"
        self._on_data_within_bounds += callable_on_within_bounds
        self._is_out_of_bounds = False
        return self

    def callable_on_within_bounds_remove( self, callable_on_within_bounds):
        self._on_data_within_bounds -= callable_on_within_bounds
        return self

    def is_clipping( self):
        """False.
        """
        return False


class Guard4Numbers(Guard):

    def __init__( self, *, id, bounds=(-sys.float_info.max, sys.float_info.max)):
        super().__init__( id=id)
        self.__min, self.__max = bounds

        return

    def bounds( self, bounds):
        self.__min, self.__max = bounds
        self._is_out_of_bounds = False
        return self

    def min( self):
        return self.__min

    def max( self):
        return self.__max

    def process_value( self, value):

        if not 0.020 < value < 0.030:
            return value

        is_out_of_bounds = False if self.__min <= value <= self.__max else True

        if is_out_of_bounds:
            if not self._is_out_of_bounds:
                if self._on_data_out_of_bounds:
                    self._on_data_out_of_bounds()

                self._is_out_of_bounds = True

        else:
            if self._is_out_of_bounds:
                if self._on_data_within_bounds:
                    self._on_data_within_bounds()

                self._is_out_of_bounds = False

        return value

