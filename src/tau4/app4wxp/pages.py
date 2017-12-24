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

import logging
import wx

from tau4.instruments.oscilloscopes.models.flexvarblscope import OsciChannel, OsciModel, OsciModelMPL
from tau4.instruments.oscilloscopes.views.wxp import OsciView, OsciViewMPL
from tau4.wxp import VarblViewBuilder

from tau4.app4wxp.data import Varbls 
from tau4.app4wxp.mbus import Messages

_PADDING = 5


class _Dashboard(wx.Panel):
    
    def __init__( self, parent, id, *args, **kwargs):
        super().__init__( parent, id, *args, **kwargs)
        
        self._build_()
        
        Messages.GPS.Error.RegisterSubscriber( self._mbus_on_gps_error_)
        Messages.GPS.Data.RegisterSubscriber( self._mbus_on_gps_new_data_)
        return
    
    def _build_( self):
        s0 = wx.BoxSizer( wx.VERTICAL)
        
        s1 = wx.StaticBoxSizer( wx.StaticBox( self, -1, "DEBUG"), wx.VERTICAL)
        s0.Add( s1, flag=wx.LEFT|wx.TOP, border=_PADDING)

        s1.Add( VarblViewBuilder( Varbls().fv_dbg_time_running()).view_actualFV( self, -1))
        s1.Add( VarblViewBuilder( Varbls().fv_dbg_heartbeat()).view_actualFV( self, -1))
        s1.Add( VarblViewBuilder( Varbls().fv_dbg_heartbeats_per_sec()).view_actualFV( self, -1))
        
        s2 = wx.StaticBoxSizer( wx.StaticBox( self, -1, "GPS"), wx.VERTICAL)
        s0.Add( s2, flag=wx.LEFT|wx.TOP, border=_PADDING)
        
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_SAT_COUNT)).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv_gps_data_x()).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv_gps_data_y()).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_DISTANCE_TO_ORG)).view_actualFV( self, -1))
        b = wx.Button( self, -1, "Current World Pos. As Org.")
        b.Bind( wx.EVT_BUTTON, self._wxEH_on_EVT_BUTTON_teach_org_)
        s2.Add( b, 0, wx.ALIGN_CENTER_HORIZONTAL)
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_HSPEED)).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_ERROR_MARGIN)).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_X)).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_Y)).view_actualFV( self, -1))
        s2.Add( VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_MAP_URL)).view_actualFV( self, -1))
        
        self.SetSizer( s0)
        s0.Fit( self)
        return
    
    def _mbus_on_gps_error_( self, tau4pc, message):
        Varbls().fv_logging_errors().value( str( message))
        return
    
    def _mbus_on_gps_new_data_( self, tau4pc, message):
        FVs = Varbls()
        
        ### GPS-Daten als String
        #
        s = "# sats: %d; posLL: %s; posXY: %s.\n" % (message.count_sats(), message.posLL(), message.posXY())
        FVs.fv_gps_data_string().value( s)

        ### GPS-Pos roh, also bwz. WORLD
        #
        sat_count = message.count_sats()
        FVs.fv( Varbls.IDs._GPS_DATA_SAT_COUNT).value( sat_count)

        x, y = message.posXY()        
        FVs.fv( Varbls.IDs._GPS_DATA_X_RAW).value( x)
        FVs.fv( Varbls.IDs._GPS_DATA_Y_RAW).value( y)
        
        ### GPS-Pos bez. AREA
        #
        x -= FVs.fv( Varbls.IDs._GPS_DATA_ORG_X).value()
        y -= FVs.fv( Varbls.IDs._GPS_DATA_ORG_Y).value()
        FVs.fv_gps_data_x().value( x)
        FVs.fv_gps_data_y().value( y)
        
        ### GPS-Distanz bez. AREA
        #
        FVs.fv( Varbls.IDs._GPS_DATA_DISTANCE_TO_ORG).value( sqrt( x*x + y*y))

        ### Error Margin
        #
        #FVs.fv( Varbls.IDs._GPS_DATA_ERROR_MARGIN).value( message.error_margin())
        
        ### HSpeed
        #
        FVs.fv( Varbls.IDs._GPS_DATA_HSPEED).value( message.hspeed())
        
        ### Pos. Prec.
        #
        x, y = message.pos_precision()
        FVs.fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_X).value( x)
        FVs.fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_Y).value( y)
        
        ### Map URL
        #
        FVs.fv( Varbls.IDs._GPS_DATA_MAP_URL).value( message.map_url())
        
        return
    
    def _wxEH_on_EVT_BUTTON_teach_org_( self, wxE):
        FVs = Varbls()

        ### Org setzen
        #
        Varbls().fv( Varbls.IDs._GPS_DATA_ORG_X).value( Varbls().fv( Varbls.IDs._GPS_DATA_X_RAW).value())
        Varbls().fv( Varbls.IDs._GPS_DATA_ORG_Y).value( Varbls().fv( Varbls.IDs._GPS_DATA_Y_RAW).value())
        
        ### GPS-Pos bez. AREA
        #
        x = FVs.fv( Varbls.IDs._GPS_DATA_X_RAW).value() - FVs.fv( Varbls.IDs._GPS_DATA_ORG_X).value()
        y = FVs.fv( Varbls.IDs._GPS_DATA_Y_RAW).value() - FVs.fv( Varbls.IDs._GPS_DATA_ORG_Y).value()
        FVs.fv_gps_data_x().value( x)
        FVs.fv_gps_data_y().value( y)
        
        ### GPS-Distanz bez. AREA
        #
        FVs.fv( Varbls.IDs._GPS_DATA_DISTANCE_TO_ORG).value( sqrt( x*x + y*y))

        return



class _NotebookPage(wx.Panel):
    
    def __init__( self, parent, id, caption):
        super().__init__( parent, id)
                
        self._build_()
        
        parent.InsertPage( parent.GetPageCount(), self, caption)
        return
    
    def _build_( self):
        raise NotImplementedError()

    
class NotebookPageGPS(_NotebookPage):
    
    def __init__( self, parent, id):
        super().__init__( parent, id, "GPS")
        
        return
    
    def _build_( self):
        s0 = wx.BoxSizer( wx.HORIZONTAL)
    
        s0.Add( _Dashboard( self, -1), 1, wx.EXPAND)
    
        s1 = wx.BoxSizer( wx.VERTICAL)
        s0.Add( s1, 2, wx.EXPAND|wx.ALL, 1)
    
        s1.Add( VarblViewBuilder( Varbls().fv_gps_data_string()).view_loggingFV( self, -1), 3, wx.EXPAND)
        s1.Add( VarblViewBuilder( Varbls().fv_logging_infos()).view_loggingFV( self, -1), 2, wx.EXPAND)
        s1.Add( VarblViewBuilder( Varbls().fv_logging_errors()).view_loggingFV( self, -1), 1, wx.EXPAND)
    
        self.SetSizerAndFit( s0)
        return
    

class NotebookPageOscilloscope(_NotebookPage):
    
    def __init__( self, parent, id):
        super().__init__( parent, id, "Oscilloscope")
        
        return
    
    def _build_( self):
        s0 = wx.BoxSizer( wx.VERTICAL)

        om = OsciModel( 5000, (0, 300), (-45, 55), (0, 153, 76))
        om.connect_flex_varbl( Varbls().fv( Varbls.IDs.Oscilloscope._CHANNEL_1))
        ov = OsciView( self, -1, om)
        s0.Add( ov, 1, wx.EXPAND)

        self.SetSizerAndFit( s0)
        return
    

class NotebookPageOscilloscopeMPL(_NotebookPage):
    
    def __init__( self, parent, id):
        super().__init__( parent, id, "Oscilloscope (matplotlib Version)")
        
        return
    
    def _build_( self):
        s0 = wx.BoxSizer( wx.VERTICAL)

        oc1 = OsciChannel( title="Stdev X", len=10000, colour_rgb=( 255, 0, 0))
        oc2 = OsciChannel( title="Stdev Y", len=10000, colour_rgb=( 0, 255, 0))
        om = OsciModelMPL( title="Stdev X", span_x=OsciModelMPL.SpanMS( 1 * 60 * 1000), range_y=OsciModelMPL.Range( -45, 55), channels=( oc1, oc2))
        ov = OsciViewMPL( self, -1, om)
        om.title_x( "time / s")
        om.channel( 0).connect_fv_y( Varbls().fv( Varbls.IDs.Oscilloscope._CHANNEL_1))
        om.channel( 1).connect_fv_y( Varbls().fv( Varbls.IDs.Oscilloscope._CHANNEL_2))
        s0.Add( ov, 1, wx.EXPAND)

        self.SetSizerAndFit( s0)
        return
