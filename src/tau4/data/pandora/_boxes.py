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

from collections import OrderedDict
import configparser as cp
import sys
import uuid

from tau4 import Object
from tau4.sweng import Singleton

from tau4.data.pandora.plugins import _Plugins, Clipper, Clipper4Numbers, Guard, Guard4Numbers, Monitor, Plugin


class Box(Object):

    """Standard Box, holds a value and that's it.

    \param  value   Initial value. \b Caution: Determines the type of the box's value!
                    There's no further chance to change its type.

    \param  id      The Box's identification. May be None. If it is not None, then
                    the Box is \b automatically stored in the \c Shelf.

    \param  label   The Box's label.

    \param  dim     The value's dimension.

    \param  infos   Additional information.

    Usage:
        \code{.py}
            from tau4.data import pandora

            p = pandora.Box( value=0.0, id="speed", label="The body's speed", dim="m/s")
            print( "%s: %.3f %s" % (p.label(), p.value(), p.dim()))

            ##  Access this Box in an other part of the program
            #
            p = pandora.Shelf().box( "speed")
            p.value( p.value() * 42)
            print( "%s: %.3f %s" % (p.label(), p.value(), p.dim()))
        \endcode

    This box is the fastest, because it only reads and writes values.
    However, a box may be customised in infinite many ways by adding plugins.
    Other boxes, which are derived from this box, are convenience classes, that
    add a monitoring plugin, a clipping plugin, or both etc.

    However, you may configure this box by adding plugins as described below.

    \par Add a clipper and use its results
    2DO

    \_2DO   Add a clipper and use its results

    \par Add a monitor and use its results:
    2DO

    \_2DO   Add a monitor and use its results

    \par Add a clipper and monitor and use their results:
    2DO

    \_2DO   Add a clipper and monitor and use their results

    \par    The Plugin Concept
    The basic design provides, that the user is responsible for his plugins.
    For instance, if he adds a plugin, that publishes (like the Monitor does),
    then he's responsible for registering with that very plugin. This means,
    the Box doesn't do anything with or for its plugins and the user cannot
    register with the Box to be notified of an event generated by a plugin.

    \par
    As for a publishing plugin like Clipper, Guard, or Monitor: If the user
    registers with the plugin, the user is called by the plugin and must not
    access the Box itself! This because the Box does not have its final value
    as long as the plugins are executed!

    """

    def __init__( self, *, value, id=None, label="", dim="", infos="", plugins=None):
        super().__init__( id=id)
        self.__value = value
        self.__type = type( value)
        self.__label = label
        self.__dim = dim
        self.__infos = infos

        if id is not None:
            Shelf().box_add( self)

        self.__plugins = _Plugins()
        if plugins:
            for plugin in plugins:
                self.__plugins.append( plugin)

        return

    def __iter__( self):
        """as_tuple() - Usage: id, value = p_my_box
        """
        for item in (self.id(), self.__value):
            yield item

    def __repr__( self):
        return "%s( id=%s, value=%s)" % (self.__class__.__name__, self.id(), self.value())

    def clipper( self) -> Clipper:
        raise NotImplementedError( "'%s' does not support this protocol, try 'BoxClipping' etc.!" % self.__class__.__name__)

    def data2dict( self):
        return {"data": self.value(), "infos": self.infos()}

    def dict2data( self, d):
        """Used by the Shelf to store a Box in an INI file.
        """
        return self.value( d[ "data"])

    def dim( self, arg=None):
        """The dimension of the value, that is 'm', 'm/s' etc.
        """
        if arg is None:
            return self.__dim

        self.__dim = arg
        return self

    def guard( self) -> Guard:
        """The guard if any; a Guard is a non-clipping Clipper and serves as an informer about out-of-bounds events.
        """
        raise NotImplementedError( "'%s' does not support this protocol, try 'BoxGuarded' etc.!" % self.__class__.__name__)

    def infos( self):
        """Infos abaout the Box for the reader of an INI file.
        """
        return self.__infos

    def is_clipping( self):
        """Does this ox clip?
        """
        for plugin in self.__plugins:
            if plugin.is_clipping():
                return True

        return False

    def label( self, arg=None):
        """A label used if the Box is displayed.
        """
        if arg is None:
            return self.__label

        self.__label = arg
        return self

    def monitor( self) -> Monitor:
        """The Monitor if any; the Monitor publishes changes of the Box's value.
        """
        raise NotImplementedError( "'%s' does not support this protocol, try 'BoxMonitored' etc.!" % self.__class__.__name__)

    def plugin_append( self, plugin : Plugin):
        """Append a new plugin.

        \note   The order the plugns are appended defines the order the plugins are executed.
        """
        self.__plugins.append( plugin)
        return self

    def _typecast_( self, arg):
        return self.__type( arg)

    def _type_is_valid_( self, arg):
        return type( arg) is self.__type

#    def _value_( self, value=None):
#        """Zugriff auf den Value ohne Ausführung der Plugins.
#        """
#        if value is None:
#            return self.__value
#
#        self.__value = value
#        return self
# ##### 2017-09-07: Wird nicht benötigt.

    def value( self, value=None):
        if value is None:
            return self.__value

        value = self._typecast_( value)

        for plugin in self.__plugins.values():
            value = plugin.process_value( value)

        #assert self._type_is_valid_( value)
        self.__value = value
        return value
    data = value


class BoxGuarded(Box):

    """Box enthält einen Guard und einen Monitor.

    Im Unterschied zu einem Clipper publisht der Guard eine Bereichsüberschreitung
    nur, der Wert wird nicht geändert.

    Klassischer Anwendungsfall:
        Abhängig von Bereichsüberschreitungen sollen am Display die Farbe der
        angezeigten Werte verändert werden. Die Werte selbst dürfen sdabei natürlich
        nicht verändert werden, damit der User das Ausmaß der Bereichsüberschreitung
        beurteilen kann.
    """

    def __init__( self, *, value, bounds=(-sys.float_info.max, sys.float_info.max), id=None, label="", dim="", infos=""):
        super().__init__( value=value, id=id, label=label, dim=dim, infos=infos, plugins=None)

        id = id if id is not None else str( uuid.uuid4())

        self.__guard_id = id + "." + Guard4Numbers.__name__
        guard = Guard4Numbers( id=self.__guard_id, bounds=bounds)
        Shelf().plugin_add( guard)

        self.plugin_append( guard)

        self.__monitor_id = id + "." + Monitor.__name__
        monitor = Monitor( id=self.__monitor_id)
        Shelf().plugin_add( monitor)

        self.plugin_append( monitor)
        return

    def bounds( self, bounds: tuple):
        """Grenzen des Plugins \c Guard ändern.
        """
        assert isinstance( bounds, tuple)
        self.guard().bounds( bounds)
        return self

    def guard( self) -> Clipper:
        """Zugriff auf den \c Guard.
        """
        return Shelf().plugin( self.__guard_id)

    def is_clipping( self):
        """False.
        """
        return False

    def monitor( self) -> Monitor:
        """Zugriff auf den Monitor.
        """
        return Shelf().plugin( self.__monitor_id)

    def reg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.

        Note:
            It is essentially important that the subscriber calls the sender to
            ask for its value and not the box!

            So, don't do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    assert isinstance( self.__model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                    return

                Here, the model would be the box, which leads to wrong
                results: The box hasn't updated its value by the plugin's value!


            Instead, do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    model = tau4pc.client()
                    assert isinstance( model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                    return

                Here, the model would be the current plugin, which returns the
                valid value!

        """
        return self.guard().callable_on_out_of_bounds_append( tau4s)

    def ureg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.
        """
        return self.guard().callable_on_out_of_bounds_remove( tau4s)

    def reg_tau4s_on_limit_not_violated( self, tau4s):
        """

        NOTE:
            It is essentially important that the subscriber calls the sender to
            ask for its value and not the box!

            So, don't do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    assert isinstance( self.__model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                    return

                Here, the model would be the box, which leads to wrong
                results: The box hasn't updated its value by the plugin's value!


            Instead, do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    model = tau4pc.client()
                    assert isinstance( model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                    return

                Here, the model would be the current plugin, which returns the
                valid value!

        """
        return self.guard().callable_on_within_bounds_append( tau4s)

    def ureg_tau4s_on_limit_not_violated( self, tau4s):
        return self.guard().callable_on_within_bounds_remove( tau4s)

    def reg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.
        """
        return self.monitor().callable_append( tau4s)

    def ureg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.
        """
        return self.monitor().callable_remove( tau4s)


class BoxClipping(Box):

    def __init__( self, *, value, bounds=(-sys.float_info.max, sys.float_info.max), id=None, label="", dim="", infos=""):
        super().__init__( value=value, id=id, label=label, dim=dim, infos=infos, plugins=None)

        id = id if id is not None else str( uuid.uuid4())

        self.__clipper_id = id + "." + Clipper4Numbers.__name__
        clipper = Clipper4Numbers( id=self.__clipper_id, bounds=bounds)
        Shelf().plugin_add( clipper)

        self.plugin_append( clipper)

        self.__clipper = clipper
        return

    def bounds( self, bounds: tuple):
        assert isinstance( bounds, tuple)
        self.__clipper.bounds( bounds)
        return self

    def clipper( self) -> Clipper:
        return Shelf().plugin( self.__clipper_id)

    def is_clipping( self):
        """True.
        """
        return True

    def reg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.
        """
        return self.clipper().callable_on_out_of_bounds_append( tau4s)

    def ureg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.
        """
        return self.clipper().callable_on_out_of_bounds_remove( tau4s)

    def reg_tau4s_on_limit_not_violated( self, tau4s):
        return self.clipper().callable_on_within_bounds_append( tau4s)

    def ureg_tau4s_on_limit_not_violated( self, tau4s):
        return self.clipper().callable_on_within_bounds_remove( tau4s)


class BoxClippingMonitored(Box):

    def __init__( self, *, value, bounds=(-sys.float_info.max, sys.float_info.max), id=None, label="", dim="", infos=""):
        super().__init__( value=value, id=id, label=label, dim=dim, infos=infos, plugins=None)

        id = id if id is not None else str( uuid.uuid4())

        self.__clipper_id = id + "." + Clipper4Numbers.__name__
        clipper = Clipper4Numbers( id=self.__clipper_id, bounds=bounds)
        Shelf().plugin_add( clipper)

        self.plugin_append( clipper)

        self.__monitor_id = id + "." + Monitor.__name__
        monitor = Monitor( id=self.__monitor_id)
        Shelf().plugin_add( monitor)

        self.plugin_append( monitor)
        return

    def bounds( self, bounds: tuple):
        assert isinstance( bounds, tuple)
        self.clipper().bounds( bounds)
        return self

    def clipper( self) -> Clipper:
        return Shelf().plugin( self.__clipper_id)

    def is_clipping( self): return True

    def monitor( self) -> Monitor:
        return Shelf().plugin( self.__monitor_id)

    def reg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.

        NOTE:
            It is essentially important that the subscriber calls the sender to
            ask for its value and not the box!

            So, don't do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    assert isinstance( self.__model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                    return

                Here, the model would be the box, which leads to wrong
                results: The box hasn't updated its value by the plugin's value!


            Instead, do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    model = tau4pc.client()
                    assert isinstance( model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                    return

                Here, the model would be the current plugin, which returns the
                valid value!

        """
        return self.clipper().callable_on_out_of_bounds_append( tau4s)

    def ureg_tau4s_on_limit_violated( self, tau4s):
        """For compatibility w/ clipped flex varbls.
        """
        return self.clipper().callable_on_out_of_bounds_remove( tau4s)

    def reg_tau4s_on_limit_not_violated( self, tau4s):
        """

        NOTE:
            It is essentially important that the subscriber calls the sender to
            ask for its value and not the box!

            So, don't do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    assert isinstance( self.__model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                    return

                Here, the model would be the box, which leads to wrong
                results: The box hasn't updated its value by the plugin's value!


            Instead, do this:

                def _tau4s_on_model_changed_( self, tau4pc):
                    model = tau4pc.client()
                    assert isinstance( model.value(), int)
                    wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                    return

                Here, the model would be the current plugin, which returns the
                valid value!

        """
        return self.clipper().callable_on_within_bounds_append( tau4s)

    def ureg_tau4s_on_limit_not_violated( self, tau4s):
        return self.clipper().callable_on_within_bounds_remove( tau4s)

    def reg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.
        """
        return self.monitor().callable_append( tau4s)

    def ureg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.
        """
        return self.monitor().callable_remove( tau4s)


class BoxMonitored(Box):

    def __init__( self, *, value, id=None, label="", dim="", infos=""):

        super().__init__( value=value, id=id, label=label, dim=dim, infos=infos, plugins=None)

        id = id if id is not None else str( uuid.uuid4())

        self.__monitor_id = id + "." + Monitor.__name__
        monitor = Monitor( id=self.__monitor_id)
        Shelf().plugin_add( monitor)

        self.plugin_append( monitor)
        return

    def monitor( self) -> Monitor:
        return Shelf().plugin( self.__monitor_id)

    def reg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.

        NOTE:
            It is essentially important that the subscriber calls the sender to
            ask for its value and not the box!

            So, don't do this:

                \code{.py}
                    def _tau4s_on_model_changed_( self, tau4pc):
                        assert isinstance( self.__model.value(), int)
                        wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if self.__model.value() else None)
                        return
                \endcode

            Here, the model would be the box, which leads to wrong
            results: The box hasn't updated its value by the plugin's value!


            Instead, do this:

                \code{.py}
                    def _tau4s_on_model_changed_( self, tau4pc):
                        model = tau4pc.client()
                        assert isinstance( model.value(), int)
                        wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
                        return
                \endcode

            Here, the model would be the current plugin, which returns the
            valid value!

        """
        return self.monitor().callable_append( tau4s)

    def ureg_tau4s_on_modified( self, tau4s):
        """For compatibility w/ monitored flex varbls.
        """
        return self.monitor().callable_remove( tau4s)


class Shelf(metaclass=Singleton):

    def __init__( self):
        self.__boxes = {}
        self.__plugins = {}
        self.__pathname = "./pandoras_shelf.ini"

        self.__sectionname_boxes = "pandora.boxes"
        self.__sectionname_plugins = "pandora.plugins"
        self.__cp = None
        return

    def box( self, id):
        return self.__boxes[ id]

    def box_add( self, p):
        if p.id() in self.__boxes:
            raise KeyError( "Box '%s' already set!" % p.id())

        self.__boxes[ p.id()] = p
        return

    def box_exists( self, id):
        return id in self.__boxes

    def box_remove( self, p):
        del self.__boxes[ p.id()]
        return

    def box_restore( self, p):
        if self.__cp is None:
            self.__cp = _ConfigParser( self.pathname_ini())
            self.__cp.read()

        try:
            data = self.__cp.get( self.__sectionname_boxes, p.id())
            d = eval( data)
            p.dict2data( d)

        except cp.NoSectionError:
            self.__cp.add_section( self.__sectionname_boxes)
            self.box_store( p)

        except cp.NoOptionError:
            self.box_store( p)

        return self
    restore_box = box_restore # DEPRECATED

    def box_store( self, p):
        if self.__cp is None:
            self.__cp = _ConfigParser( self.pathname_ini())
            self.__cp.read()

        try:
            self.__cp.set( self.__sectionname_boxes, p.id(), str( p.data2dict()))

        except cp.NoSectionError:
            self.__cp.add_section( self.__sectionname_boxes)
            self.__cp.set( self.__sectionname_boxes, p.id(), str( p.data2dict()))

        self.__cp.write()
        return self
    store_box = box_store # DEPRECATED

    def pathname_ini( self, pathname=None):
        if pathname is None:
            return str( self.__pathname)

        self.__pathname = pathname
        self.__cp = None
        return self

    def plugin_add( self, p):
        if p.id() in self.__plugins:
            raise KeyError( "Plugin '%s' already in Plugins!" % p.id())

        self.__plugins[ p.id()] = p
        return

    def plugin( self, id):
        return self.__plugins[ id]


class _ConfigParser(cp.ConfigParser):

    def __init__( self, pathname):
        super().__init__()

        self.__pathname = pathname
        return

    def pathname( self):
        return self.__pathname

    def read( self):
        return super().read( self.pathname())

    def write( self):
        with open( self.pathname(), "wt") as f:
            return super().write( f)

