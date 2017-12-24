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
import matplotlib
matplotlib.use( 'WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import numpy as np
import os
import random
import time
import wx

from tau4 import ThisName
from tau4.data import flex
from tau4.datalogging import SysEventLog, UsrEventLog
from tau4.instruments.oscilloscopes.models.flexvarblscope import OsciModel
from tau4.instruments.oscilloscopes.models import LogFileControllerModel
from tau4.wxp import VarblViewBuilder


_PADDING = 5


class _LogFileControllerView(wx.Panel):

    """Control for selecting a pathname and enabling/disabling the logging.
    """

    def __init__( self, parent, id, model: LogFileControllerModel):
        super().__init__( parent, id)

        self.__model = model

        self.__model.reg_tau4s_on_modified( self._tau4s_on_model_is_modified_)

        self._build_()
        return

    def _build_( self):
        s0 = wx.StaticBoxSizer( wx.StaticBox( self, -1, "Log file"), wx.VERTICAL)

        b = wx.ToggleButton( self, -1, "Enable")
        b.Bind( wx.EVT_TOGGLEBUTTON, self._wxEH_on_EVT_TOGGLEBUTTON_)
        s0.Add( b, 0, wx.EXPAND|wx.ALL, _PADDING)

        self.__tc_pathname = wx.TextCtrl( self, -1, self._model_().logfile_pathname().value())
        s0.Add( self.__tc_pathname, 0, wx.EXPAND|wx.ALL, _PADDING)

        self.__st_exception = wx.StaticText( self, -1, "")
        s0.Add( self.__st_exception, 0, wx.EXPAND|wx.ALL, _PADDING)

        b = wx.ToggleButton( self, -1, "Browse")
        b.Bind( wx.EVT_TOGGLEBUTTON, self._wxEH_on_EVT_BUTTON_)
        s0.Add( b, 0, wx.EXPAND|wx.ALL, _PADDING)

        self.SetSizerAndFit( s0)
        return

    def _model_( self):
        return self.__model

    def _tau4s_on_model_is_modified_( self, tau4pc):
        """Model has changed.

        :param  tau4pc: Publisher channel.
        """
        self.__tc_pathname.SetValue( tau4pc.client().logfile_pathname().value())
        if tau4pc.client().logfile_is_enabled():
            self.__st_exception.SetLabel( str( tau4pc.client().logfile_exception()))

        else:
            self.__st_exception.SetLabel( "")

        return

    def _wxEH_on_EVT_BUTTON_( self, wxE):
        wildcard = "Log files (*.log)|*.log|All files (*.*)|*.*"
        d = wx.FileDialog( \
            self,
            message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
#            style=wx.OPEN|wx.CHANGE_DIR
        )
        if d.ShowModal() == wx.ID_OK:
            pathname = d.GetPath()
            if pathname:
                self._model_().logfile_pathname( pathname)

        d.Destroy()
        return

    def _wxEH_on_EVT_TOGGLEBUTTON_( self, wxE):
        """View has changed.
        """
        value = wxE.GetInt()
        self._model_().logfile_enable() if value != 0 else self._model_().logfile_disable()
        return


class _DashboardView(wx.Panel):

    """

    2DO:
        If there's a view, there should be a model...
    """

    def __init__( self, parent, id):
        super().__init__( parent, id)

        ### Attributes
        #
        self.__fv_x = flex.VariableDeMo( value=0.0, label="X")
        self.__fv_y = flex.VariableDeMo( value=0.0, label="Y")
        self.__fv_databuffer_len = flex.VariableDeMo( value=0.0, label="#")
        self.__fv_databuffer_maxlen = flex.VariableDeMo( value=0.0, label="##")

        ### Build it
        #
        s0 = wx.StaticBoxSizer( wx.StaticBox( self, -1, ""), wx.VERTICAL)
        s0.Add( VarblViewBuilder( self.__fv_databuffer_maxlen).view_actualFV( self, -1))
        s0.Add( VarblViewBuilder( self.__fv_databuffer_len).view_actualFV( self, -1))
        s0.Add( VarblViewBuilder( self.__fv_x).view_actualFV( self, -1))
        s0.Add( VarblViewBuilder( self.__fv_y).view_actualFV( self, -1))

        self.SetSizerAndFit( s0)
        return

    def fv_x( self):
        return self.__fv_x

    def fv_y( self):
        return self.__fv_y

    def fv_databuffer_len( self):
        return self.__fv_databuffer_len

    def fv_databuffer_maxlen( self):
        return self.__fv_databuffer_maxlen


class OsciView(wx.Panel):

    def __init__( self, parent, id, oscimodel: OsciModel):
        super().__init__( parent, id)

        self.__oscimodel = oscimodel

        self.__screen = wx.Panel( self, -1)

        self.__dashboard = _DashboardView( self, -1)
        self.__logfile_controlller_view = _LogFileControllerView( self, -1, model=self.__oscimodel.logfile_controller())

        self.__screenbuffer = self.__oscimodel.screenbuffer()
                                        # Realises the transform
        self.__screenbuffer.databuffer().reg_tau4s_on_changes( self._tau4s_on_databuffer_changed_)

        self.__vX_max = 0
        self.__vY_max = 0

        self._build_()

        self.__screen.Bind( wx.EVT_PAINT, self.OnPaint)
        self.__screen.Bind( wx.EVT_SIZE, self.OnSize)

        self.__timer = wx.Timer( self)
        self.Bind( wx.EVT_TIMER, self._wxEH_EVT_TIMER_, self.__timer)
        self.__timer.Start( 500)
                                        # 2DO: Wert muss aus den Settings kommen.
        return

    def _build_( self):
        s0 = wx.StaticBoxSizer( wx.StaticBox( self, -1, "Oscilloscope"), wx.HORIZONTAL)

        self.__screen.SetBackgroundColour( "black")
        s0.Add( self.__screen, 4, wx.EXPAND)

        s_controls = wx.BoxSizer( wx.VERTICAL)
        s0.Add( s_controls, 1, wx.EXPAND)

        s_controls.Add( self.__dashboard, 1, wx.EXPAND)
        s_controls.Add( self.__logfile_controlller_view, 1, wx.EXPAND)

        self.SetSizerAndFit( s0)
        return

    def _draw_grid_( self, dc):
        dc.SetTextForeground( wx.Colour( (255, 128, 0)))
        dc.SetPen( wx.Pen( wx.Colour( (255, 128, 0)), 1, wx.PENSTYLE_SHORT_DASH))

        for text in self.screenbuffer().grid().texts():
            dc.DrawText( text.str(), *text.point())

        for ((x1, y1), (x2, y2)) in self.screenbuffer().grid().lines():
            dc.DrawLine( x1, y1, x2, y2)

        return

    def _draw_datapoints_( self, dc):
        dc.SetPen( wx.Pen( wx.Colour( self.databuffer().colour_rgb()), 2))

        datapoints = self.screenbuffer().datapoints()
        try:
            x1, y1 = next( datapoints)

        except StopIteration:
            return

        for x2, y2 in datapoints:
            dc.DrawLine( x1, y1, x2, y2)
            x1, y1 = x2, y2

        return

    def OnPaint( self, wxE):
        dc = wx.PaintDC( self.__screen)

        self._draw_grid_( dc)
        self._draw_datapoints_( dc)

        return

    def OnSize( self, wxE):
        """Festlegen des Koordinatensystems fürs Zeichnen.

        Die meisten Grafikpakete haben den Org links oben, wir möchten ihn aber
        links unten haben. Hierzu ist ein Frame zu berechnen, der dann bei den
        grafischen Ausgaben berücsichtigt wird. Dieser Frame wird hier berechnet.

        Ebenfalls hier berechnet wird auch der Maßstabsfaktor.
        """
        self.__vX_max, self.__vY_max = wxE.GetSize()
        self.__vTs = None
                                        # # Force recal. of transform

        dx, dy = wxE.GetSize()
        dx *= 0.9; dy *= 0.9
        self.__screenbuffer.dx( dx).dy( dy)
        return

    def databuffer( self):
        return self.screenbuffer().databuffer()

    def screenbuffer( self):
        return self.__screenbuffer

    def _tau4s_on_databuffer_changed_( self, tau4pc):
        """Display the values of the latest datapoint (and of some other values).
        """
        databuffer = tau4pc.client()
        x, y = databuffer.datapoints()[ -1]
        self.__dashboard.fv_x().value( x)
        self.__dashboard.fv_y().value( y)
        self.__dashboard.fv_databuffer_maxlen().value( databuffer.maxlen())
        self.__dashboard.fv_databuffer_len().value( databuffer.len())
        return

    def _wxEH_EVT_TIMER_( self, wxE):
        if self.IsShownOnScreen():
            self.Refresh( eraseBackground=False)

        return

class OsciViewMPL(wx.Panel):

    """Oscilloscope view, matplotlib-based.
    """

    def __init__( self, parent, id, oscimodel, freq_update=0.5):
        super().__init__( parent, id)

        ### Connect to the model
        #
        self.__oscimodel = oscimodel
        self.__oscimodel.reg_tau4s_on_modified_accessories( self._tau4s_on_modified_accessories_)
        #self.__oscimodel.reg_tau4s_on_modified_data( self._tau4s_on_modified_data_)
        # ##### Not needed, as display is executed timer driven

        ### Attrs needed for drawing
        #

        ### Build
        #
        s0 = wx.BoxSizer( wx.HORIZONTAL)

            ### Screen
            #
        self.__figure = Figure()

        self.__subplot = self.__figure.add_subplot( 111)
        self.__subplot.set_title( self.__oscimodel.title())
        self.__subplot.set_xlabel( self.__oscimodel.title_x())
        self.__subplot.set_ylabel( self.__oscimodel.title_y())

        self.__canvas = FigureCanvas( self, -1, self.__figure)
        s0.Add( self.__canvas, 4, wx.LEFT | wx.TOP | wx.GROW)

#        self.__line2D = None
#        self.__line2D, = self.__subplot.plot( [ 0], [ 0])

            ### Controls
            #
        s_controls = wx.BoxSizer( wx.VERTICAL)
        s0.Add( s_controls, 1, wx.EXPAND)

                ### Sliders for scaling
                #
        self.__span_x = self.model().span_x()
        s = wx.StaticBoxSizer( wx.StaticBox( self, -1, "X (Abscissa)"), wx.HORIZONTAL)
        s_controls.Add( s, 0, wx.EXPAND)
        self.__slider_x = wx.Slider( self, -1, 100, 1, 200, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.__slider_x.SetTickFreq( 10)
        self.__slider_x.Bind( wx.EVT_SLIDER, self._wxEH_on_EVT_SLIDER_x_)
        s.Add( self.__slider_x, 1)

        self.__range_y = self.model().range_y()
        s = wx.StaticBoxSizer( wx.StaticBox( self, -1, "Y (Ordinata)"), wx.HORIZONTAL)
        s_controls.Add( s, 0, wx.EXPAND)
        self.__slider_y = wx.Slider( self, -1, 100, 1, 200, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.__slider_y.SetTickFreq( 10)
        self.__slider_y.Bind( wx.EVT_SLIDER, self._wxEH_on_EVT_SLIDER_y_)
        s.Add( self.__slider_y, 1)

                ### Slider-reset button
                #
        b = wx.Button( self, -1, "Reset scaling")
        self.Bind( wx.EVT_BUTTON, self._wxEH_on_EVT_BUTTON_reset_scaling_)
        s_controls.Add( b, 0, wx.EXPAND)

        ### Timer to enable realtime plotting
        #
        self.__timer = wx.Timer( self)
        self.Bind( wx.EVT_TIMER, self._wxEH_on_EVT_TIMER_)
        self.__timer.Start( freq_update * 1000)

        ### Layout
        #
        self.SetSizerAndFit( s0)

        return

    def draw( self):
        wx.CallAfter( self._draw_)

    def _draw_( self):
        this_name = ThisName( self)

        is_data_present = False
        osci = self.__oscimodel
        for channel in osci.channels():
            datapoints_x = channel.datapoints_x()
            if channel.datapoints_x():
                r, g, b = channel.colour_rgb()
                colour_rgb = ( r/255, g/255, b/255)

                channel.datapoints_lock()

                try:

#                    self.__line2D.set_xdata( channel.datapoints_x())
#                    self.__line2D.set_ydata( channel.datapoints_y())
#                    self.__line2D.set_color( color=colour_rgb)
                    self.__subplot.plot( channel.datapoints_x(), channel.datapoints_y(), color=colour_rgb)

                except ValueError as e:
                    UsrEventLog().log_error( e, this_name)

                channel.datapoints_unlock()

                x_max = channel.datapoints_x()[ -1]
                x_min = x_max - float( osci.span_x())

                is_data_present = True

        if is_data_present:
            y_min, y_max = osci.range_y()
            self.__subplot.axis( ( x_min, x_max, y_min, y_max))
            self.__subplot.grid( True, "both")
            self.__canvas.draw()

        return

    def model( self):
        return self.__oscimodel

    def _tau4s_on_modified_accessories_( self, tau4pc):
        self.__subplot.set_title( self.__oscimodel.title())
        self.__subplot.set_xlabel( self.__oscimodel.title_x())
        self.__subplot.set_ylabel( self.__oscimodel.title_y())

        self.__subplot.set_yticks( \
            np.arange( *self.model().range_y(), step=self.model().range_y().size() / 20),
            minor=True
        )
        return

    def _tau4s_on_modified_data_( self, tau4pc):
        pass

    def _wxEH_on_EVT_BUTTON_reset_scaling_( self, wxE):
        self.model().span_x( self.__span_x)
        self.__slider_x.SetValue( 100)

        self.model().range_y( self.__range_y)
        self.__slider_y.SetValue( 100)
        return

    def _wxEH_on_EVT_SLIDER_x_( self, wxE):
        value = wxE.GetInt()
        self.model().span_x( self.__span_x * (value / 100))
        return

    def _wxEH_on_EVT_SLIDER_y_( self, wxE):
        value = wxE.GetInt()
        self.model().range_y( self.__range_y * (value / 100))
        return

    def _wxEH_on_EVT_TIMER_( self, wxE):
        if self.IsShownOnScreen():
            self._draw_()

        return
