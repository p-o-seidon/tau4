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

from tau4 import ThisName
from tau4.data import flex
from tau4.data import pandora
from tau4.datalogging import _EventLog, UsrEventLog

import wx
from wx.lib import calendar


_PADDING = 5


class BoxView4UpdatingNumber(wx.Panel):

    def __init__( self, parent, id, box: pandora.BoxMonitored, formatter:pandora.formatters.Formatter):
        super().__init__( parent, id)

        self.__box = box
        self.__formatter = formatter
        self.__is_clipping_box = False

        self.__tc_value = None
        self.__tc_value_bgcolour = None
        self.__tc_value_fgcolour = None

        self._build_()

        try:
            self.__box.guard().callable_on_out_of_bounds_append( self._tau4s_on_out_of_bounds_)
            self.__box.guard().callable_on_within_bounds_append( self._tau4s_on_within_bounds_)

        except NotImplementedError:
            pass

        self.__box.monitor().callable_append( self._tau4s_on_modified_box_data_)

        self.__value = 0
        self.__timer_for_updating_the_display = wx.Timer( self)
        self.Bind( wx.EVT_TIMER, self._wxEH_on_EVT_TIMER_, self.__timer_for_updating_the_display)
        self.__timer_for_updating_the_display.Start( 500)

        return

    def _build_( self):
        s0 = wx.BoxSizer( wx.HORIZONTAL)

        s0.Add( wx.StaticText( self, -1, self.__box.label()), 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT|wx.RIGHT, 1)

        self.__tc_value = wx.TextCtrl( self, -1, self.__formatter.as_str( self.__box.data()), style=wx.TE_RIGHT|wx.TE_READONLY)
        s0.Add( self.__tc_value, 1, wx.ALIGN_CENTRE_VERTICAL)

        s0.Add( wx.StaticText( self, -1, self.__box.dim()), 0, wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, 1)

        self.SetSizerAndFit( s0)
        return

    def _tau4s_on_modified_box_data_( self, tau4pc):
        """

        _2DO:
            Bringt das wirklich was, den Update nur zu machen, wenn das Control
            angezeigt wird?
        """
        self.__value = tau4pc.client().value()
        return

    def _tau4s_on_out_of_bounds_( self, tau4pc):
        #self.__tc_value_bgcolour = "yellow"
        self.__tc_value_bgcolour = wx.Colour( 255, 255, 0)
        self.__tc_value_fgcolour = "red"
        return

    def _tau4s_on_within_bounds_( self, tau4pc):
        self.__tc_value_bgcolour = None
        self.__tc_value_fgcolour = None
        return

    def _value_display_( self):
        self.__tc_value.SetBackgroundColour( self.__tc_value_bgcolour)
                                        # Funzt nicht -> ?!
        self.__tc_value.SetForegroundColour( self.__tc_value_fgcolour)
        self.__tc_value.Refresh()
        self.__tc_value.SetValue( self.__formatter.as_str( self.__value))
        return

    def _wxEH_on_EVT_TIMER_( self, wxE):
        if self.__tc_value.IsShownOnScreen():
            wx.CallAfter( self._value_display_)

        return


class BoxView4UpdatingText(wx.Panel):

    def __init__( self, parent, id, box: pandora.BoxMonitored, formatter:pandora.formatters.Formatter=pandora.formatters.StrFormatter):
        super().__init__( parent, id)

        self.__box = box
        self.__formatter = formatter

        self._build_()

        self.__box.monitor().callable_append( self._tau4s_on_modified_box_data_)
        return

    def _build_( self):
        s0 = wx.BoxSizer( wx.HORIZONTAL)

        s0.Add( wx.StaticText( self, -1, self.__box.label()), 1, wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT|wx.RIGHT, 1)

        style = wx.TE_READONLY
        if self.__formatter.alignH_centre(): style |= wx.TE_CENTRE
        elif self.__formatter.alignH_left(): pass
        elif self.__formatter.alignH_right(): style |= wx.TE_RIGHT
        self.__tc_value = wx.TextCtrl( self, -1, self.__formatter.as_str( self.__box.value()), style=style)
        s0.Add( self.__tc_value, 1, wx.ALIGN_CENTRE_VERTICAL)

        s0.Add( wx.StaticText( self, -1, self.__box.dim()), 1, wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, 1)

        self.SetSizerAndFit( s0)
        return

    def _tau4s_on_modified_box_data_( self, tau4pc):
        """

        2DO:
            bringt das wirklich was, den Update nur zu machen, wenn das Control
            angezeigt wird?
        """
        if self.__tc_value.IsShownOnScreen():
            wx.CallAfter( self.__tc_value.SetValue, self.__formatter.as_str( tau4pc.client().value()))

        return


class CalenDlg(wx.Dialog):
    """A dialog with a calendar control."""
    def __init__(self, parent, month=None, day=None, year=None):
        """
        Default class constructor.

        :param wx.Window `parent`: parent window. Must not be ``None``;
        :param integer `month`: the month, if None the current day will be used
        :param integer `day`: the day
        :param integer `year`: the year

        """
        wx.Dialog.__init__( self, parent, -1, "Event Calendar", wx.DefaultPosition, (280+40, 360))
        self.result = None

        # set the calendar and attributes
        self._calendar_ctrl = calendar.Calendar( self, -1, (20, 60), (240+40, 200))

        if month is None:
            self._calendar_ctrl.SetCurrentDay()
            start_month = self._calendar_ctrl.GetMonth()
            start_year = self._calendar_ctrl.GetYear()
        else:
            self._calendar_ctrl.month = start_month = month
            self._calendar_ctrl.year = start_year = year
            self._calendar_ctrl.SetDayValue( day)

        self._calendar_ctrl.HideTitle()
        self.ResetDisplay()

        # get month list from DateTime
        monthlist = calendar.GetMonthList()

        # select the month
        self.date = wx.ComboBox( self, -1, calendar.Month[start_month], (20, 20), (90, -1),
                                 monthlist, wx.CB_DROPDOWN
                                 )
        self.Bind( wx.EVT_COMBOBOX, self.EvtComboBox, self.date)

        # alternate spin button to control the month
        h = self.date.GetSize().height
        self.m_spin = wx.SpinButton( self, -1, (115, 20), (h * 1.5, h), wx.SP_VERTICAL)
        self.m_spin.SetRange(1, 12)
        self.m_spin.SetValue(start_month)
        self.Bind( wx.EVT_SPIN, self.OnMonthSpin, self.m_spin)

        # spin button to control the year
        self.dtext = wx.TextCtrl( self, -1, str(start_year), (160, 20), (60, -1))
        w = self.dtext.GetSize().width
        h = self.dtext.GetSize().height

#        self.y_spin = wx.SpinButton( self, -1, (225, 20), (h * 1.5, h), wx.SP_VERTICAL)
        self.y_spin = wx.SpinButton( self, -1, (225, 20), (w * 1.25, h), wx.SP_VERTICAL)
        self.y_spin.SetRange( 1980, 9999)
        self.y_spin.SetValue( start_year)

        self.Bind( wx.EVT_SPIN, self.OnYrSpin, self.y_spin)
        self.Bind( calendar.EVT_CALENDAR, self.MouseClick, self._calendar_ctrl)

        x_pos = 50
        y_pos = 280
        but_size = (60, 25)

        btn = wx.Button( self, wx.ID_OK, ' Ok ', (x_pos, y_pos), but_size)
        self.Bind( wx.EVT_BUTTON, self.OnOk, btn)

        btn = wx.Button(self, wx.ID_CANCEL, ' Close ', (x_pos + 120, y_pos), but_size)
        self.Bind( wx.EVT_BUTTON, self.OnCancel, btn)

    def OnOk(self, evt):
        """The OK event handler."""
        self.result = ['None', str(self._calendar_ctrl.day), calendar.Month[self._calendar_ctrl.month], str(self._calendar_ctrl.year)]
        self.EndModal( wx.ID_OK)

    def OnCancel(self, event):
        """The Cancel event handler."""
        self.EndModal( wx.ID_CANCEL)

    def MouseClick(self, evt):
        """The mouse click event handler."""
        self.month = evt.month
        # result click type and date
        self.result = [ evt.click, str( evt.day), calendar.Month[ evt.month], str( evt.year)]

        if evt.click == 'DLEFT':
            self.EndModal(wx.ID_OK)

    def OnMonthSpin(self, event):
        """The month spin control event handler."""
        month = event.GetPosition()
        self.date.SetValue( calendar.Month[ month])
        self._calendar_ctrl.SetMonth( month)
        self._calendar_ctrl.Refresh()

    def OnYrSpin(self, event):
        """The year spin control event handler."""
        year = event.GetPosition()
        self.dtext.SetValue( str(year))
        self._calendar_ctrl.SetYear( year)
        self._calendar_ctrl.Refresh()

    def EvtComboBox(self, event):
        """The month combobox event handler."""
        name = event.GetString()
        monthval = self.date.FindString(name)
        self.m_spin.SetValue(monthval + 1)

        self._calendar_ctrl.SetMonth(monthval + 1)
        self.ResetDisplay()

    def ResetDisplay(self):
        """Reset the display."""
        month = self._calendar_ctrl.GetMonth()
        self._calendar_ctrl.Refresh()


class EventLogView(wx.ListCtrl):

    def __init__( self, parent, id, eventlog):
        super().__init__( parent, id, style=wx.LC_REPORT|wx.LC_VIRTUAL)

        self.__eventlog = eventlog
        assert isinstance( self.__eventlog, _EventLog)

        self.InsertColumn( 0, "Event Type")
        self.InsertColumn( 1, "Time")
        self.InsertColumn( 2, "Description")
        self.InsertColumn( 3, "Source")
        self.SetColumnWidth( 0, 25)
        self.SetColumnWidth( 1, 200)
        self.SetColumnWidth( 2, 500)
        self.SetColumnWidth( 3, 500)

        self._attr4infos = wx.ListItemAttr()
        self._attr4infos.SetBackgroundColour( "white")

        self._attr4warnings = wx.ListItemAttr()
        self._attr4warnings.SetBackgroundColour( "white")

        self._attr4errors = wx.ListItemAttr()
        self._attr4errors.SetBackgroundColour( "white")

        self.__images = wx.ImageList( 16, 16)
        self.__iconindex4infos = self.__images.Add( wx.ArtProvider().GetBitmap( wx.ART_INFORMATION, size=(16,16)))
        self.__iconindex4warnings = self.__images.Add( wx.ArtProvider().GetBitmap( wx.ART_WARNING, size=(16,16)))
        self.__iconindex4errors = self.__images.Add( wx.ArtProvider().GetBitmap( wx.ART_ERROR, size=(16,16)))
        self.SetImageList( self.__images, wx.IMAGE_LIST_SMALL)

        UsrEventLog().register_tau4s_on_changes( self._tau4s_on_eventlog_changed_)
        return

    def OnGetItemAttr( self, i):
        event = self.__eventlog.event( i)

        if event.severity_is_info():
            return self._attr4infos

        if event.severity_is_warning():
            return self._attr4warnings

        if event.severity_is_error():
            return self._attr4errors

        return None

    def OnGetItemImage( self, i):
        event = self.__eventlog.event( i)

        if event.severity_is_info():
            return self.__iconindex4infos

        if event.severity_is_warning():
            return self.__iconindex4warnings

        if event.severity_is_error():
            return self.__iconindex4errors

        return -1

    def OnGetItemText( self, i, j):
        event = self.__eventlog.event( i)

        if j == 0:
            text = ""
                                            # In 1. Spalte wird ein Image angezeigt.
        elif j == 1:
            text = str( event.time_formatted())

        elif j == 2:
            text = str( event.reason_text())

        elif j == 3:
            text = str( event.source_text())

        else:
            text = "??? (UNKNOWN COL NBR)"

        return text

    def _tau4s_on_eventlog_changed_( self, tau4p):
        wx.CallAfter( self.SetItemCount, UsrEventLog().num_events())
        return


class FontModder:

    """Changes fonts of controls recursively.
    """

    def __init__( self, win):
        self._win = win

        self._font_org = win.GetFont()
        return

    def face_name_set( self, face_name, recurseively=True):
        self._change_style_if_needed_()

        f = self._win.GetFont()
        g = wx.Font( f.GetPointSize(), f.GetFamily(), f.GetStyle(), f.GetWeight(), faceName=face_name)
        self._win.SetFont( g)

        if recurseively:
            for win in self._win.GetChildren():
                self.__class__( win).face_name_set( face_name, recurseively)

        return self

    def family_set( self, family, recurseively=True):
        win = self._win

        self._change_style_if_needed_()

        f = win.GetFont()
        g = wx.Font( f.GetPointSize(), family, f.GetStyle(), f.GetWeight(), faceName=f.GetFaceName())
        win.SetFont( g)

        if recurseively:
            for win in self._win.GetChildren():
                self.__class__( win).family_set( family, recurseively)

        return self

    def family_set_MODERN( self, recurseively=True):
        return self.family_set( wx.FONTFAMILY_MODERN, recurseively)

    def family_set_TELETYPE( self, recurseively=True):
        return self.family_set( wx.TELETYPE, recurseively)

    def magnify( self, factor=1.5, only_instances_of_these_classes=(wx.Window,), recurseively=True):
        self._change_style_if_needed_()

        if isinstance( self._win, only_instances_of_these_classes):
            self._size_change_( self._win, factor)

        if recurseively:
            for win in self._win.GetChildren():
                self.__class__( win).magnify( factor, only_instances_of_these_classes, recurseively)

        return self

    def magnify_button_texts_only( self, factor=1.5, recurseively=True):
        #return self
        win = self._win

        if isinstance( win, wx.Button):
            self._size_change_( win, factor)

        if recurseively:
            for win in win.GetChildren():
                self.__class__( win).magnify_button_texts_only( factor, recurseively)

        return self

    def shrink( self, factor=1.5, only_instances_of_these_classes=(wx.Window,), recurseively=True):
        self._change_style_if_needed_()

        if isinstance( self._win, only_instances_of_these_classes):
            self._size_change_( self._win, 1./factor)

        if recurseively:
            for win in self._win.GetChildren():
                self.__class__( win).shrink( factor, only_instances_of_these_classes, recurseively)

        return self

    def weight_set_BOLD( self, only_instances_of_these_classes=(wx.Window,), recursively=True):
        if isinstance( self._win, only_instances_of_these_classes):
            self._change_style_if_needed_()
            f = self._win.GetFont()
            g = wx.Font( f.GetPointSize(), f.GetFamily(), f.GetStyle(), wx.FONTWEIGHT_BOLD, faceName=f.GetFaceName())
            self._win.SetFont( g)

        if recursively:
            for win in self._win.GetChildren():
                self.__class__( win).weight_set_BOLD( only_instances_of_these_classes, recursively)

        return self


    def weight_set_NORMAL( self, only_instances_of_these_classes=(wx.Window,), recursively=True):
        if isinstance( self._win, only_instances_of_these_classes):
            self._change_style_if_needed_()
            f = self._win.GetFont()
            g = wx.Font( f.GetPointSize(), f.GetFamily(), f.GetStyle(), wx.FONTWEIGHT_NORMAL, faceName=f.GetFaceName())
            self._win.SetFont( g)

        if recursively:
            for win in self._win.GetChildren():
                self.__class__( win).weight_set_BOLD( only_instances_of_these_classes, recursively)

        return self

    def _change_style_if_needed_( self):
        win = self._win

        if isinstance( win, wx.TextCtrl):
            if wx.Platform == "__WXMSW__":
                style = win.GetDefaultStyle()
                style_flags = style.GetFlags()
                style_flags |= wx.TE_RICH2
                style.SetFlags( style_flags)
                win.SetDefaultStyle( style)

        return

    def _size_change_( self, win, factor):
        f = win.GetFont()
        g = wx.Font( int( f.GetPointSize() * factor), f.GetFamily(), f.GetStyle(), f.GetWeight(), faceName=f.GetFaceName())
        win.SetFont( g)
        return win


class IpAddrEditWidget(wx.Panel):

    @staticmethod
    def ModelFromFlexVarbl( fv):
        return IpAddrEditWidget.Model( fv)


    class Model:

        def __init__( self, fv):
            self.__fv = fv
            return

        def label( self):
            return self.__fv.label()

        def is_valid( self):
            items = self.value().split( ".")
            if not len( items) == 4:
                return False

            if not all( [item.isdigit() for item in items]):
                return False

            return True

        def store( self):
            return self.__fv.store()

        def value( self, arg=None):
            if arg is None:
                return self.__fv.value( arg)

            return self.__fv.value( arg)


    def __init__( self, parent, id, model):
        super().__init__( parent, id)

        self.__model = model
        self.__view = None

        ### Build
        #
        s0 = wx.BoxSizer( wx.HORIZONTAL)

        s0.Add( \
            wx.StaticText( self, -1, self.model().label(), style=wx.ALIGN_RIGHT),
            1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, _PADDING
        )

        tc = wx.TextCtrl( self, -1, self.model().value(), style=wx.TE_CENTER)
        tc.Bind( wx.EVT_TEXT, self._wxE_on_EVT_TEXT_)
        s0.Add( tc, 1, wx.ALIGN_CENTER_VERTICAL)
        self.__view = tc

        self.SetSizerAndFit( s0)
        return

    def model( self):
        return self.__model

    def view( self):
        return self.__view

    def _wxE_on_EVT_TEXT_( self, wxE):
        s = wxE.GetString()
        self.model().value( s)
        if not self.model().is_valid():
            #self.view().SetBackgroundColour( "orange")
            # ##### Funzt nicht (Phoenix unter Arch)
            self.view().SetForegroundColour( "red")
            return

        self.view().SetBackgroundColour( None)
        self.view().SetForegroundColour( None)
        self.model().store()
        return


class VarblViewBuilder:

    """Baut zusammengesetzte Controls, die auf flex.Variable arbeiten.
    """

    _ProportionLabel = 2
    _ProportionValue = 2
    _ProportionDim = 1

    class _DefaultValueFormatter:

        def __call__( self, value):
            try:
                return "%.3f" % value

            except TypeError:
                return str( value)


    class _FloatValueFormatter:

        def __call__( self, value):
            return "%.3f" % value


    class _IntValueFormatter:

        def __call__( self, value):
            return "%d" % value


    class _StrValueFormatter:

        def __call__( self, value):
            return str( value)


    class _BoolValueFormatter:

        def __call__( self, value):
            return "True" if value in (True, "TRUE", "True", "true", 1, "YES", "Yes", "yes") else "False"


    def __init__( self, p_value):
        self.__p_value = p_value
        self.__st_value = None
        self.__tc_value = None

        if type( self.__p_value.value()) == bool:
            self.__valueformatter = self._BoolValueFormatter()

        elif isinstance( self.__p_value.value(), int):
            self.__valueformatter = self._IntValueFormatter()

        elif isinstance( self.__p_value.value(), float):
            self.__valueformatter = self._FloatValueFormatter()

        elif isinstance( self.__p_value.value(), str):
            self.__valueformatter = self._StrValueFormatter()

        else:
            self.__valueformatter = self._DefaultValueFormatter()

        return

    def _fv_value_change_and_restore_( self, value):
        try:
            self.__p_value.value( value)
            if isinstance( self.__p_value, (flex._VariableMixinPersistor, flex._VariableMixinPersistor2)):
                self.__p_value.store()

        except ValueError as e:
            wx.MessageBox( str( e), "ERROR", wx.ICON_ERROR)

        return

    def _tau4s_on_modified_model_update_static_text_( self, tau4pc):
        wx.CallAfter( self.__st_value.SetLabel, self.__valueformatter( tau4pc.client().value()))
        return

    def _tau4s_on_modified_model_update_text_ctrl_( self, tau4pc):
        wx.CallAfter( self.__tc_value.SetValue, self.__valueformatter( tau4pc.client().value()))
        return

    def valueformatter( self, formatter=None):
        if formatter is None:
            return self.__valueformatter

        self.__valueformatter = formatter
        return self


    def view_actualFV( self, parent, id, padding=5):
        """

        .. note::
            Fehler in wx.StaticText: Kann wx.ALIGN_RIGHT nicht.
        """
        use_StaticText = True
        use_TextCtrl = not use_StaticText

        panel = wx.Panel( parent, -1)
        parent = panel

        s = wx.BoxSizer( wx.HORIZONTAL)

        ### Label
        #
        st = wx.StaticText( parent, -1, self.__p_value.label(), style=wx.ST_ELLIPSIZE_MIDDLE)
        s.Add( st, self._ProportionLabel, wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, padding)

        ### Value
        #
        if use_TextCtrl:
            tc = wx.TextCtrl( parent, -1, str( self.__p_value.value()), style=wx.TE_READONLY|wx.TE_RIGHT)
            self.__tc_value = tc
            tc.SetForegroundColour( "DARK GREY")
            self.__p_value.reg_tau4s_on_modified( self._tau4s_on_modified_model_update_text_ctrl_)
            tc.Bind( wx.EVT_WINDOW_DESTROY, self._wxEH_on_EVT_WINDOW_DESTROY_text_ctrl_)
            s.Add( tc, self._ProportionValue, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, padding)

        else:
            st = wx.StaticText( parent, -1, str( self.__p_value.value()), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.__st_value = st
            f = st.GetFont()
            f.SetWeight( wx.FONTWEIGHT_BOLD)
            st.SetFont( f)
            self.__p_value.reg_tau4s_on_modified( self._tau4s_on_modified_model_update_static_text_)
            st.Bind( wx.EVT_WINDOW_DESTROY, self._wxEH_on_EVT_WINDOW_DESTROY_static_text_)
            s.Add( st, self._ProportionValue, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, padding)

        ### Dim
        #
        v = self._view_dim_( parent, -1)
        if v:
            s.Add( v, self._ProportionDim, wx.ALIGN_CENTER_VERTICAL|wx.ALL, padding)

        else:
            s.AddStretchSpacer( self._ProportionDim)

        ### Sizer
        #
        panel.SetSizerAndFit( s)

        return panel

    def _view_dim_( self, parent, id):
        return wx.StaticText( parent, id, self.__p_value.dim()) if self.__p_value.dim() else None

    def view_loggingFV( self, parent, id):
        s = wx.BoxSizer( wx.VERTICAL)

        st = wx.StaticText( parent, -1, self.__p_value.label())
        s.Add( st, 0, wx.TOP|wx.LEFT, 5)

        tc = wx.TextCtrl( parent, -1, str( self.__p_value.value()), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.__p_value.reg_tau4s_on_modified( lambda pc, w=tc: wx.CallAfter( tc.AppendText, pc.client().value()))
        s.Add( tc, 1, wx.EXPAND|wx.ALL, 5)

        return s

    def view_ratedFV( self, parent, id, is_restart_needed=True):
        """Sollwert-Widget für den Wert der flex.Variable.

        Der Typ wird von der flex.Variable bestimmt.

        Wenn die flex.Variable geändert wird, publisht sie das und dieses Widget
        hat sich dafür angemeldet. Also wird, was gerade eingegeben worden ist,
        durch dieses Publsihing angezeigt und zwar formatiert.
        """
        p = wx.Panel( parent, id)
        parent = p

        s = wx.BoxSizer( wx.HORIZONTAL)

        ### Label
        #
        label = self.__p_value.label()
        if is_restart_needed:
            label += " (Restart Needed)"

        st = wx.StaticText( parent, -1, label)
        #st.SetBackgroundColour( "YELLOW")
        ### Funzt nicht.
        s.Add( st, self._ProportionLabel, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, 5)

        ### Value
        #
        style = 0
        style = wx.TE_PROCESS_ENTER
        if self.__p_value.is_numeric():
            style |= wx.TE_RIGHT

        tc = wx.TextCtrl( parent, -1, str( self.__p_value.value()), style=style)
        tc.Bind( wx.EVT_TEXT_ENTER, self._wxEH_on_EVT_ENTER_)
        tc.Bind( wx.EVT_KILL_FOCUS, self._wxEH_on_EVT_ENTER_)
        self.__p_value.reg_tau4s_on_modified( lambda pc, w=tc: tc.SetValue( self.__valueformatter( pc.client().value())))
        s.Add( tc, self._ProportionValue, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, 5)

        ### Dim
        #
        v = self._view_dim_( parent, -1)
        if v:
            s.Add( v, self._ProportionDim, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            #v.SetBackgroundColour( "YELLOW")
            ### Funzt nicht.

        else:
            s.AddStretchSpacer( self._ProportionDim)

        ### Sizer
        #
        p.SetSizerAndFit( s)

        return p

    def _wxEH_on_EVT_ENTER_( self, wxE):
        #if wxE.GetEventObject().GetValue().strip():
        #    wx.CallAfter( self._fv_value_change_and_restore_, wxE.GetEventObject().GetValue().strip())
        # ##### So kann man keine Variablen löschen!
        wx.CallAfter( self._fv_value_change_and_restore_, wxE.GetEventObject().GetValue().strip())

        return

    def _wxEH_on_EVT_WINDOW_DESTROY_static_text_( self, wxE):
        self.__p_value.ureg_tau4s_on_modified( self._tau4s_on_modified_model_update_static_text_)
        return

    def _wxEH_on_EVT_WINDOW_DESTROY_text_ctrl_( self, wxE):
        self.__p_value.ureg_tau4s_on_modified( self._tau4s_on_modified_model_update_text_ctrl_)
        return


class VarblEnabledButtonBuilder:

    def __init__( self, fv, button):
        self.__button = button

        fv.reg_tau4s_on_modified( lambda tau4pc, fv=fv, b=button: wx.CallAfter( b.Enable, fv.value()))
        return

    def button( self):
        return self.__button


class IOConnectedButtonBuilder:

    """Builder baut einen Button, der einen internen DOUT (iDOUT) "treibt" (Flanke!).

    Die Connection mit z.B. einer internen PLC (siehe auch automation.PLC) muss
    extern erfolgen.
    """
    def __init__( self, dout, button):
        self.__button = button; assert isinstance( self.__button, wx.Button)
        self.__idout = idout

        self._build_()
        return

    def _build_( self):
        self.__button.Bind( wx.EVT_BUTTON, self._wxEH_on_EVT_BUTTON_)
        return

    def button( self):
        return self.__button

    def _wxEH_on_EVT_BUTTON_( self, wxE):
        self.__idout.value( 1)
        threading.Timer( 0.5, self.__idout.value, (0,))
        return


class IOEnabledButtonBuilder:

    """Builder baut einen Button, der von einem internen DINP (iDOUT) enablet wird (Flanke!).

    Die Connection mit z.B. einer internen PLC (siehe auch automation.PLC) muss
    extern erfolgen.
    """
    def __init__( self, idinp, button):
        self.__button = button; assert isinstance( self.__button, wx.Button)
        self.__idinp = idinp

        #idinp.fv_pin().reg_tau4s_on_modified( lambda tau4pc, fv=idinp, b=button: wx.CallAfter( b.Enable, fv.value()))
        # ##### Okay, lässt sich aber schlecht debuggen
        idinp.fv_pin().reg_tau4s_on_modified( self._tau4s_on_modified_)
        return

    def button( self):
        return self.__button

    def _tau4s_on_modified_( self, tau4pc):
        wx.CallAfter( self.__button.Enable, tau4pc.client().value())
        return


class VarblDrivenStatusBuilder:

    """Baut Status-Control, das an einer boolschen FV hängt.
    """

    _ProportionLabel = 2
    _ProportionValue = 2
    _ProportionDim = 1

    class _DefaultValueFormatter:

        def __init__( self, value4NOK, value4OK):
            self.__value4NOK = value4NOK
            self.__value4OK = value4OK
            return

        def __call__( self, value):
            if value:
                return self.__value4OK

            else:
                return self.__value4NOK


    def __init__( self, fv, value4NOK, value4OK):
        self.__fv = fv
        self.__valueformatter = self._DefaultValueFormatter( value4NOK, value4OK)
        return

    def valueformatter( self, formatter=None):
        if formatter is None:
            return self.__valueformatter

        self.__valueformatter = formatter
        return self


    def view_actualFV( self, parent, id):
        """

        .. note::
            Fehler in wx.StaticText: Kann wx.ALIGN_RIGHT nicht.
        """
        use_StaticText = True
        use_TextCtrl = not use_StaticText

        panel = wx.Panel( parent, -1)
        parent = panel

        s = wx.BoxSizer( wx.HORIZONTAL)

        ### Label
        #
        st = wx.StaticText( parent, -1, self.__fv.label(), style=wx.ST_ELLIPSIZE_MIDDLE)
        s.Add( st, self._ProportionLabel, wx.ST_NO_AUTORESIZE|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, 5)

        ### Value
        #
        if use_TextCtrl:
            tc = wx.TextCtrl( parent, -1, str( self.__fv.value()), style=wx.TE_READONLY|wx.TE_RIGHT)
            tc.SetForegroundColour( "DARK GREY")
            self.__fv.reg_tau4s_on_modified( lambda pc, w=tc: wx.CallAfter( tc.SetValue, self.__valueformatter( pc.client().value())))
            s.Add( tc, self._ProportionValue, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        else:
            st = wx.StaticText( parent, -1, str( self.__fv.value()), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            f = st.GetFont()
            f.SetWeight( wx.FONTWEIGHT_BOLD)
            st.SetFont( f)
            self.__fv.reg_tau4s_on_modified( lambda pc, w=st: wx.CallAfter( w.SetLabel, self.__valueformatter( pc.client().value())))
            self.__fv.reg_tau4s_on_modified( lambda pc, w=st: wx.CallAfter( w.SetLabel, self.__valueformatter( pc.client().value())))
            s.Add( st, self._ProportionValue, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        ### Dim
        #
        v = self._view_dim_( parent, -1)
        if v:
            s.Add( v, self._ProportionDim, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        else:
            s.AddStretchSpacer( self._ProportionDim)

        ### Sizer
        #
        panel.SetSizerAndFit( s)

        return panel

    def _view_dim_( self, parent, id):
        return wx.StaticText( parent, id, self.__fv.dim()) if self.__fv.dim() else None


class LEDView4Box(wx.Panel):

    """LED of fixed size, that displays the status of a flex.Variable.

    NOTE:
        We could use sizers instead of a fixed size panel.

    """
    def __init__( self, parent, id, model: pandora.Box, size=(10, 10), colourname="red"):
        super().__init__( parent, id)

        self.__colourname = colourname

        self.__model = model

        self.__outer_panel = wx.Panel( self, -1, size=size)
        self.__outer_panel.SetBackgroundColour( "black")

        self.__inner_panel = wx.Panel( self.__outer_panel, -1, size=( size[ 0]-2, size[ 1]-2))
        self.__inner_panel.SetBackgroundColour( self.__colourname if self.__model.value() else None)
        self.__inner_panel.SetPosition( (1, 1))

        s0 = wx.BoxSizer( wx.HORIZONTAL)

        s0.Add( self.__outer_panel, 0, wx.ALIGN_CENTRE_VERTICAL)
        s0.Add( \
            wx.StaticText( self, -1, self.__model.label()),
            0,
            wx.ALIGN_CENTRE_VERTICAL|wx.LEFT,
            5
            )

        self.SetSizerAndFit( s0)

        self.__model.reg_tau4s_on_modified( self._tau4s_on_model_changed_)
        return

    def _tau4s_on_model_changed_( self, tau4pc):
        model = tau4pc.client()
        assert isinstance( model.value(), int)
        wx.CallAfter( self.__inner_panel.SetBackgroundColour, self.__colourname if model.value() else None)
        return

