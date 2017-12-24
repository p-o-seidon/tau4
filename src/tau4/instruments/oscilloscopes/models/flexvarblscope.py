#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
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

import logging

from collections import deque
import copy
import datetime as dt
from math import *
from threading import RLock
import time

from tau4.data import flex
from tau4.datalogging import UsrEventLog
from tau4.instruments.oscilloscopes.models import LogFileControllerModel
from tau4.mathe.linalg import T3D, V3D
from tau4.sweng import PublisherChannel


class DataBuffer:

    """Databuffer, holding the values to be displayed.

    :param  len:
        Number of datapoints the buffer can fold.

    :param  x_limits:
        Width of window to be displayed. There's no clipping by these values!

    :param  y_limits:
        Height of window to be displayed. There's no clipping by these values!

    :param  colour_rgb:
        RGB tuple, defining the colour when displayed.
    """
    def __init__( self, len, x_limits, y_limits, colour_rgb):
        self.__datapoints = deque( maxlen=len)
        self.__colour_rgb = colour_rgb

        self.__x_limits = Range( *x_limits)
                                        # Limits when displayed: x-axis
        self.__y_limits = Range( *y_limits)
                                        # Limits when displayed: y-axis
        self.__x_range = Range( 0, 0)
                                        # Range of values in the buffer: x-axis
        self.__y_range = Range( 0, 0)
                                        # Range of values in the buffer: y-axis
        self.__time_ref = 0
                                        # 2DO: Really needed?
        self.__tau4p_on_changes = PublisherChannel.Synch( self)
                                        # Called, weh the databuffer has changed,
                                        #   i.e. a data point has been added.
        self.__fv = None

        self.__grid = _Grid4Channel( self)
        self.__lock = RLock()
        return

    def __len__( self):
        return len( self.__datapoints)

    def colour_rgb( self):
        """Colour code as an RGB tuple.

        Used when displayed.
        """
        return self.__colour_rgb

    def connect_flex_varbl( self, fv):
        """Connect data buffer to a flex varbl.

        Each time the flex varbl changes its value, a datapoint is recorded.
        """
        self.__fv = fv
        self.__fv.reg_tau4s_on_modified( self._tau4s_on_input_changed_)
        return self

    def datapoint_add( self, p):
        with self.__lock:
            self.__datapoints.append( Point() << p)

        self.__tau4p_on_changes()
                                        # Causes the view to be partially refreshed.
                                        #   OsciView.OnPaint() is NOT called,
                                        #   OsciView.OnPaint() is called by a
                                        #   timer of OsciView.
        return self

    def datapoints( self):
        with self.__lock: # 2DO: Das Lock nutzt hier gar nichts...
            return [dp.clipped( self.y_limits()) for dp in self.__datapoints]

    def grid( self):
        return self.__grid

    def len( self):
        return len( self)

    def lock( self):
        return self.__lock

    def maxlen( self, arg=None):
        if arg is None:
            return self.__datapoints.maxlen

        self.__datapoints = deque( self.__datapoints, arg)
        return self

    def reg_tau4s_on_changes( self, tau4s):
        self.__tau4p_on_changes += tau4s
        return

    def _tau4s_on_input_changed_( self, tau4pc):
        """Subscriber for changes of the connected flex varbl.
        """
        if not self.__time_ref:
            self.__time_ref = time.time()

        x = time.time() - self.__time_ref
        y = self.__fv.value()
        self.datapoint_add( (x, y))
        return

    def x_limits( self):
        return self.__x_limits

    def y_limits( self):
        return self.__y_limits

#    def y_range( self):
#        return self.__y_range




class Databuffer4XY:

    def __init__( self, DX, dx):
        self.__Ts = Ts
        self.__buffer = deque( len)
        return

    def addXY( self, point):
        assert isinstance( point, Point)
        i = point.x() // self.Ts()
        self.__buffer[ i] = point.y()
        return


    def Ts( self):
        return self.__Ts

    def __len__( self):
        return len( self.__buffer)


class OsciModel:

    def __init__( self, len, x_limits, y_limits, colour_rgb):
        self.__databuffer = DataBuffer( len, x_limits, y_limits, colour_rgb)

        self.__screenbuffer = ScreenBuffer( 100, 100, self.__databuffer)
                                        # The initial values are just that: Inital
                                        #   values. They are changed by the OsciView
                                        #   as soon as the size of the window the
                                        #   data are displayed in changes.
                                        #   See OsciView.OnSize().
        self.__logfile_controller_model = LogFileControllerModel()
        self.__screenbuffer.databuffer().reg_tau4s_on_changes( self._tau4s_on_databuffer_modified_)

        return

    def connect_flex_varbl( self, fv):
        self.__databuffer.connect_flex_varbl( fv)

    def logfile_controller( self):
        return self.__logfile_controller_model

    def screenbuffer( self):
        """Accessed by OsciView.
        """
        return self.__screenbuffer

    def _tau4s_on_databuffer_modified_( self, tau4pc):
        databuffer = tau4pc.client()
        x, y = databuffer.datapoints()[ -1]
        if not self.__logfile_controller_model.logfile_is_open():
            self.__logfile_controller_model.logfile_open()

        self.__logfile_controller_model.logfile_write( x, y)
        return


class ScreenBuffer:

    """Buffer, that does all the calculations needed for display by wxp etc.

    This means that wxp just needs to take the figures and display them directly
    w/o any calculations.

    :param  databuffer:
        Buffer, that contains all the real values, that should be displayed.

    :param  dx:
        Time span, that should be displayed.

        BS: 100 if the time span displayed should be 100 s.

    :param  dy:
        Range of values, that should be displayed.

        BS: (-100, 100) if all values in between -100 and 100 should be displayed.
    """

    class _ScreenData: pass


    def __init__( self, dx, dy, databuffer):
        self.__databuffer = databuffer; assert isinstance( self.__databuffer, DataBuffer)
        self.__x_limits = Range( 0, dx)
        self.__y_limits = Range( 0, dy)

        self.__sTc = None

        self.__grid = _Grid4Screen( self)

        self.__zoomF_x = 1
        self.__zoomF_y = 1
        return

    def _clippedY_( self, y):
        return min( self.dy(), max( 0, y))

    def databuffer( self):
        return self.__databuffer

    def dx( self, arg=None):
        """Pixel values relative to the upper left corner.
        """
        if arg is None:
            return self.__x_limits.size()

        assert isinstance( arg, (int, float))
        self.__x_limits << (0, arg)
        self.__sTc = None
        self.grid().x_limits( Range( 0, arg))
        return self

    def dy( self, arg=None):
        """Pixel values relative to the upper left corner.
        """
        if arg is None:
            return self.__y_limits.size()

        assert isinstance( arg, (int, float))
        self.__y_limits << (0, arg)
        self.__sTc = None
        self.grid().y_limits( Range( 0, arg))
        return self

    def grid( self):
        return self.__grid

    def datapoints( self):
        with self.databuffer().lock():
            ### Cal. values for the scaling
            #
            grid4screen = self.grid()
            grid4channel = self.databuffer().grid()
            sDX = grid4screen.x_limits().size()
            sDY = grid4screen.y_limits().size()
            cDX = grid4channel.x_limits().size()
            cDY = grid4channel.y_limits().size()
            scale_x = sDX / cDX
            scale_y = sDY / cDY

            ### The x-values shift by by time. We need to shift them towards the
            #   origin: The first x-value must euqal to zero. Otherwise it would be
            #   drawn on the false screen position!
            #
            if not self.__databuffer.datapoints():
                return

            datapoints = copy.copy( self.__databuffer.datapoints())

            cXMAX = datapoints[ -1][ 0]

            datapoints.reverse()

            ### Now deliver
            #
            cXLIMITMAX = grid4channel.x_limits().max()
            for cX, cY in datapoints:
                cX = cX - cXMAX + cXLIMITMAX
                                                # No x-value greater than cXMAX
                if cX < 0:
                                                # DataBuffer greater than needed:
                                                # There are more values in the
                                                #   buffer than have to be
                                                #   displayed, i.e. the
                                                #   data buffer is too large.
                    break
                                                    # We don't do a
                                                    #   self.__databuffer.maxlen( ceil( self.__databuffer.len()))
                                                    #   because just ignoring the
                                                    #   values not displayed is
                                                    #   enough optimisation

                sX, sY = self.sXYc( cX * scale_x, cY * scale_y)
                sY = self._clippedY_( sY)

                yield sX, sY

#            if cX > cXMAX * 0.1:
#                                            # DataBuffer is too short,
#                                            #   not all cX got displayed.
#                maxlen_new = ceil( self.__databuffer.len() * 1.10)
#                UsrEventLog().log_warning( "Buffer is too short, resize it from '%d' to '%d. " % (self.__databuffer.maxlen(), maxlen_new))
#                self.__databuffer.maxlen( maxlen_new)
# ##### This branch is always executed as long as the databuffer is not fully filled :-(

        return None

    def sXYc( self, x, y):
        """Screen to View by the transform sP = sTc*cP.
        """
        x, y, z = (self.sTc() * V3D( x, y, 0)).xyz()
        return x, y

    def sTc( self):
        if self.__sTc is None:
            #self.__sTr = T3D.FromEuler( 0, self.dy()/2, 0, 0, 0, pi)
            cDY = self.__databuffer.y_limits().size()
            cYMAX = self.__databuffer.y_limits().max()
            sY = self.dy() * cYMAX / cDY
            self.__sTc = T3D.FromEuler( 0, sY, 0, 0, 0, pi)

        return self.__sTc

    def x_limits( self):
        return self.__x_limits

    def y_limits( self):
        return self.__y_limits

    def zoomF_x( self, arg=None):
        if arg is None:
            return self.__zoomF_x

        self.__zoomF_x = arg
        return self

    def zoomF_y( self, arg=None):
        if arg is None:
            return self.__zoomF_y

        self.__zoomF_y = arg
        return self


class _Grid4Channel:

    def __init__( self, databuffer):
        self._databuffer = databuffer

        self._lines = []
        self._texts = []

        self._build_()
        return

    def _build_( self):

        n = 10
                        # Number of divisions
        x_min = self._databuffer.x_limits().min()
        x_max = self._databuffer.x_limits().max()
        dx = (x_max - x_min)/n
                        # Width of a division
        y_min = self._databuffer.y_limits().min()
        y_max = self._databuffer.y_limits().max()
#        dy = (y_max - y_min)/n
#                        # Height of a division
#        ### HORZ gridlines
#        #
#        for i in range( -n//2, n//2 + 1):
#            y = i*dy
#            self._lines.append( _Line( _Point( x_min, y), _Point( x_max, y)))
#            self._texts.append( _Text( str="%.3f" % y, point=_Point( x_max * 1.01, y)))
#
#        ### VERT gridlines
#        #
#        for i in range( n + 1):
#            x = i*dx
#            self._lines.append( _Line( _Point( x, y_min), _Point( x, y_max)))
#            self._texts.append( _Text( "%d" % int( x), _Point( x, y_min * 1.10)))

        dy = y_max / n

        ### HORZ gridlines - pos. half
        #
        y = 0
        i = 0
        while y < y_max:
            self._lines.append( _Line( Point( x_min, y), Point( x_max, y)))
            self._texts.append( Text( str="%.3f" % y, point=Point( x_max * 1.01, y)))
            i += 1
            y = i*dy

        y = y_max
        self._lines.append( _Line( Point( x_min, y), Point( x_max, y)))
        self._texts.append( Text( str="%.3f" % y, point=Point( x_max * 1.01, y)))

        ### HORZ gridlines - neg. half
        #
        y = 0
        i = 0
        while y > y_min:
            self._lines.append( _Line( Point( x_min, y), Point( x_max, y)))
            self._texts.append( Text( str="%.3f" % y, point=Point( x_max * 1.01, y)))
            i += 1
            y = -i*dy

        y = y_min
        self._lines.append( _Line( Point( x_min, y), Point( x_max, y)))
        self._texts.append( Text( str="%.3f" % y, point=Point( x_max * 1.01, y)))

        ### VERT gridlines
        #
        for i in range( n + 1):
            x = i*dx
            self._lines.append( _Line( Point( x, y_min), Point( x, y_max)))
            self._texts.append( Text( "%d" % int( x), Point( x, y_min * 1.10)))

        return

    def lines( self):
        return self._lines

    def texts( self):
        return self._texts

    def x_limits( self):
        return self._databuffer.x_limits()

    def y_limits( self):
        return self._databuffer.y_limits()


class _Grid4Screen:

    """Screen and data as drawn directly to the screen.
    """

    def __init__( self, screenbuffer):
        self._screenbuffer = screenbuffer

        self.__databuffer = self._screenbuffer.databuffer()
        self.__lines = []
        self.__texts = []
        self.__limits = [ Range(), Range()]

        return

    def _build_( self):
        """Take all the lines from the Grid4Channel and transform them.
        """
        ### Shortcuts
        #
        grid4channel = self.__databuffer.grid()
        grid4screen = self

        sDX = grid4screen.x_limits().size()
        sDY = grid4screen.y_limits().size()
        cDX = grid4channel.x_limits().size()
        cDY = grid4channel.y_limits().size()
        scale_x = sDX / cDX
        scale_y = sDY / cDY

        ### Grid lines
        #
        for line_org in grid4channel.lines():
            line_transformed_and_scaled = _Line.FromOther( line_org, self.sTc(), scale_x=scale_x, scale_y=scale_y)
            self.__lines.append( line_transformed_and_scaled)

        ### Grid texts
        #
        for text_org in grid4channel.texts():
            text_transformed_and_scaled = Text.FromOther( text_org, self.sTc(), scale_x=scale_x, scale_y=scale_y)
            self.__texts.append( text_transformed_and_scaled)

        return

    def _clear_( self):
        self.__lines[ :] = []
        self.__texts[ :] = []

    def x_limits( self, range=None):
        """Pixel values relative to the uppe rleft corner.
        """
        if range is None:
            return self.__limits[ 0]

        assert isinstance( range, (Range, tuple))
        self.__limits[ 0] << range
        self._clear_()
        return self

    def y_limits( self, range=None):
        """Pixel values relative to the uppe rleft corner.
        """
        if range is None:
            return self.__limits[ 1]

        assert isinstance( range, (Range, tuple))
        self.__limits[ 1] << range
        self._clear_()
        return self

    def lines( self):
        """Transform into screen and stretch.
        """
        if not self.__lines:
            self._build_()

        return self.__lines

    def rebuild( self):
        self._clear_()
        self._build_()

    def sTc( self):
        return self._screenbuffer.sTc()

    def texts( self):
        """Transform into screen and stretch.
        """
        if not self.__texts:
            self._build_()

        return self.__texts


class _Line:

    @staticmethod
    def FromOther( line, T3=T3D.FromEuler(), scale_x=1, scale_y=1):
        this = _Line( Point.FromOther( line.beg(), T3, scale_x, scale_y), Point.FromOther( line.end(), T3, scale_x, scale_y))
        return this


    def __init__( self, beg, end):
        self.__points = (beg, end)
        return

    def __getitem__( self, i):
        return self.__points[ i]

    def __repr__( self):
        return "Line( %s, %s)" % tuple( self.__points)

    def __setitem__( self, i, point):
        self.__points[ i] << point
        return self

    def beg( self):
        return self.__points[ 0]

    def end( self):
        return self.__points[ 1]


class Point:

    """2DO: Derive from V3D!
    """

    @staticmethod
    def FromOther( other, T3=T3D.FromEuler(), scale_x=1, scale_y=1):
        x, y = other
        x *= scale_x
        y *= scale_y
        x, y = (T3 * V3D( x, y)).xy()
        this = Point( x, y)
        return this


    def __init__( self, x=0, y=0):
        self.__coords = [ x, y]
        return

    def __eq__( self, other):
        """Compare the Point with a tuple.
        """
        if isinstance( other, (tuple, list)):
            return tuple( self.__coords) == tuple( other)

        return self.__coords == other.__coords

    def __getitem__( self, i):
        return self.__coords[ i]

    def __repr__( self):
        return "Point( %f, %f)" % tuple( self.__coords)

    def __setitem__( self, i, v):
        self.__coords[ i] = v
        return

    def __lshift__( self, other):
        if isinstance( other, (tuple, list)):
            self.__coords[ :] = other
            return self

        self.__coords[ :] = other.__coords
        return self

    def clipped( self, y_limits):
        x, y = self
        return self.__class__( x, y_limits.clipped( y))

    def x( self):
        return self.__coords[ 0]

    def y( self):
        return self.__coords[ 1]


class Range:

    def __init__( self, min=0, max=0):
        self.__bounds = [ min, max]
        return

    def __lshift__( self, other):
        if isinstance( other, (tuple, list)):
            self.__bounds[ :] = other
            return

        self.__bounds[ :] = other.__bounds
        return

    def __mul__( self, other):
        min, max = self
        return self.__class__( min*other, max*other)

    def __getitem__( self, i):
        return self.__bounds[ i]

    def __repr__( self):
        return "Range(%f, %f)" % tuple(self.__bounds)

    def __setitem__( self, i, v):
        assert isinstance( v, (int, float))
        self.__bounds[ i] = v
        return self

    def augment( self, value):
        """Push the limits if value doesn't fit into this range.
        """
        i = min( self.__bounds[ 0], value)
        x = max( self.__bounds[ 1], value)
        self.__bounds[ :] = i, x
        return self

    def clipped( self, value):
        return min( self.max(), max( self.min(), value))

    def min( self):
        return self.__bounds[ 0]

    def max( self):
        return self.__bounds[ 1]

    def size( self):
        min, max = self.__bounds
        return max - min


class Text:

    @staticmethod
    def FromOther( other, T3=T3D.FromEuler(), scale_x=1, scale_y=1):
        this = Text( other.str(), Point.FromOther( other.point(), T3, scale_x, scale_y))
        return this


    def __init__( self, str, point):
        self.__str = str
        self.__point = point
        return

    def point( self):
        return self.__point

    def str( self):
        return self.__str


class OsciChannel:

    def __init__( self, *, title, len, colour_rgb: tuple):
        self.__title = title
        self.__len = len
        self.__colour_rgb = colour_rgb

        self.__datapoints_x = deque( maxlen=len)
        self.__datapoints_y = deque( maxlen=len)
        self.__datapoint_x_1st = None

        self.__fv_y = None

        self.__lock = RLock()

        self.__tau4p_on_modified_data = PublisherChannel.Synch( self)
        return

    def colour_rgb( self):
        return self.__colour_rgb

    def connect_fv_y( self, fv_y):
        self.__fv_y = fv_y
        self.__fv_y.reg_tau4s_on_modified( self._tau4s_on_modified_fv_)
        return

    def datapoint_add( self, point, use_1st_x_as_base=False):
        x, y = point
        if use_1st_x_as_base:
            if self.__datapoint_x_1st is None:
                self.__datapoint_x_1st = x

            x -= self.__datapoint_x_1st

        self.__datapoints_x.append( x)
        self.__datapoints_y.append( y)

        self.__tau4p_on_modified_data()
        return

    def datapoints_lock( self):
        self.__lock.acquire()

    def datapoints_unlock( self):
        self.__lock.release()

    def datapoints_x( self):
        return self.__datapoints_x

    def datapoints_y( self):
        return self.__datapoints_y

    def fv( self):
        return

    def reg_tau4s_on_modified_data( self, tau4s):
        self.__tau4p_on_modified_data += tau4s

    def _tau4s_on_modified_fv_( self, tau4pc):
        self.datapoints_lock()
        self.datapoint_add( OsciModelMPL.Point( OsciModelMPL.Time.Now().milliseconds(), self.__fv_y.value()), use_1st_x_as_base=True)
        self.datapoints_unlock()
        return


class OsciModelMPL:

    """Oscilloscope model for use in matplotlib-based oscilloscope view.
    """

    Point = Point


    Range = Range


    class SpanMS:

        def __init__( self, value):
            self.__value = float( value)

        def __float__( self):
            return self.__value

        def __mul__( self, other):
            return self.__class__( self.__value * other)


    class Time:

        @staticmethod
        def Now():
            return OsciModelMPL.Time( dt.datetime.now().time())


        def __init__( self, datetime_time):
            self.__time = datetime_time
            return

        def milliseconds( self):
            return 1000 * (60 * (self.__time.hour * 60 + self.__time.minute) + self.__time.second) + self.__time.microsecond / 1000

        def seconds( self):
            return 60 * (self.__time.hour * 60 + self.__time.minute) + self.__time.second


    def __init__( self, *, title, span_x: SpanMS, range_y: Range, channels):
        self.__span_x = span_x
        self.__range_y = range_y

        self.__title = title
        self.__title_x = ""
        self.__title_y = ""

        self.__tau4p_on_modified_accessories = PublisherChannel.Synch( self)

        self.__channels = channels
        return

    def channel( self, i):
        return self.__channels[ i]

    def channels( self):
        return self.__channels

    def range_y( self, arg=None):
        if arg is None:
            return self.__range_y

        assert isinstance( arg, OsciModelMPL.Range)
        self.__range_y = arg

        self.__tau4p_on_modified_accessories()
        return self

    def reg_tau4s_on_modified_accessories( self, tau4s):
        self.__tau4p_on_modified_accessories += tau4s

    def span_x( self, arg=None):
        if arg is None:
            return self.__span_x

        assert isinstance( arg, OsciModelMPL.SpanMS)
        self.__span_x = arg

        self.__tau4p_on_modified_accessories()
        return self

    def title( self, arg=None):
        if arg is None:
            return self.__title

        self.__title = str( arg)

        self.__tau4p_on_modified_accessories()
        return self

    def title_x( self, arg=None):
        if arg is None:
            return self.__title_x

        self.__title_x = str( arg)

        self.__tau4p_on_modified_accessories()
        return self

    def title_y( self, arg=None):
        if arg is None:
            return self.__title_y

        self.__title_y = str( arg)

        self.__tau4p_on_modified_accessories()
        return self


def _lab_mmap_():
    import mmap

    return


if __name__ == "__main__":
    _lab_mmap_()
    input( "Press any key to exit...")
