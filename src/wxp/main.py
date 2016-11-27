#   -*- coding: utf8 -*-
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2016
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

from __future__ import division

import logging; from logging import handlers

from math import sqrt
import os
import string

from tau4.data import flex
from tau4.time import SchedulerThread

import traceback
import time
import wx
from wx import adv


_PADDING = 5


#
### File    data.py
#
import configparser as cp
import os
import sys
from tau4.data import flex
from tau4.sweng import Singleton
import time


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
    

class Varbls(metaclass = Singleton):
    
    class IDs:
        
        _GPS_DATA_ERROR_MARGIN = "_GPS_DATA_ERROR_MARGIN"

        _GPS_DATA_HSPEED = "_GPS_DATA_HSPEED"

        _GPS_DATA_MAP_URL = "_GPS_DATA_MAP_URL"

        _GPS_DATA_POSITION_PRECISION_X = "_GPS_DATA_POSITION_PRECISION_X"
        _GPS_DATA_POSITION_PRECISION_Y = "_GPS_DATA_POSITION_PRECISION_Y"

        _GPS_DATA_ORG_X = "_GPS_DATA_ORG_X"
        _GPS_DATA_ORG_Y = "_GPS_DATA_ORG_Y"
        
        _GPS_DATA_SAT_COUNT = "_GPS_DATA_SAT_COUNT"
        
        _GPS_DATA_X_RAW = "_GPS_DATA_X_RAW"
        _GPS_DATA_Y_RAW = "_GPS_DATA_Y_RAW"

        _GPS_DATA_DISTANCE_TO_ORG = "_GPS_DATA_DISTANCE_TO_ORG"
        
    def __init__( self):
        self.__config_parser = _ConfigParser( self._pathname_ini_())
        self.__config_parser.read()
        fv = flex.Variable( id="varbls.app.name", value="tau4 Sample App")
        flex.Variable.InstanceStore( fv.id(), fv)

        fv = flex.VariableDeMoPe2( id="varbls.app.date_of_last_start", value="2016-08-08", config_parser=self.__config_parser, label="Last Started", dim=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        fv.restore()
        
        fv = flex.VariableDeMo( id="varbls.gps.data.string", value="", label="GPS", dim=None, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_MAP_URL, value="-", label="Map URL", dim="", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_POSITION_PRECISION_X, value=0.0, label="Pos. Prec. X", dim="", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_POSITION_PRECISION_Y, value=0.0, label="Pos. Prec. Y", dim="", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_ERROR_MARGIN, value="-", label="Error Margin", dim="", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_HSPEED, value=0.0, label="Horz. Speed", dim="m/s", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_SAT_COUNT, value=0, label="# Sats", dim="", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_DISTANCE_TO_ORG, value=0.0, label="Travel Distance", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_X_RAW, value=0.0, label="X Raw", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_Y_RAW, value=0.0, label="Y Raw", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_ORG_X, value=0.0, label="X Org", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=self.IDs._GPS_DATA_ORG_Y, value=0.0, label="Y Org", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.gps.data.x", value=0.0, label="X", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.gps.data.y", value=0.0, label="Y", dim="m", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.logging.errors", value="", label="Errors", dim=None, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.logging.infos", value="", label="Infos", dim=None, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.debug.time_running", value=0, label="Time Up And Running", dim="s", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.debug.time_started", value=time.time(), label="Time Started", dim="s", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.debug.heartbeat", value=0, label="Heartbeat", dim=None, value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id="varbls.debug.heartbeats_per_sec", value=0, label="Heartbeat Rate", dim="1/s", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        return
    
    def fv( self, id):
        return flex.Variable.Instance( id)
    
    def fv_app_name( self):
        return self.fv( "varbls.app.name")
    
    def fv_app_date_of_last_start( self):
        return self.fv( "varbls.app.date_of_last_start")
    
    def fv_dbg_heartbeat( self):
        return self.fv( "varbls.debug.heartbeat")
    
    def fv_dbg_heartbeats_per_sec( self):
        return self.fv( "varbls.debug.heartbeats_per_sec")
    
    def fv_dbg_time_running( self):
        return self.fv( "varbls.debug.time_running")
    
    def fv_dbg_time_started( self):
        return self.fv( "varbls.debug.time_started")
    
    def fv_gps_data_string( self):
        return self.fv( "varbls.gps.data.string")
    
    def fv_gps_data_x( self):
        return self.fv( "varbls.gps.data.x")
    
    def fv_gps_data_y( self):
        return self.fv( "varbls.gps.data.y")
    
    def fv_logging_errors( self):
        return self.fv( "varbls.logging.errors")
    
    def fv_logging_infos( self):
        return self.fv( "varbls.logging.infos")
    
    def _pathname_ini_( self):
        return os.path.join( os.path.dirname( sys.argv[0]), "tau4app.ini")
    
    

#
### File    gps.py
#
import gpsd
from math import cos, radians
from tau4 import threads as tau4threading


class GPSReader(tau4threading.Thread):
    
    def __init__( self):
        super().__init__( looptime=1.0)
        return
    
    def run( self):
        while True:
            self.loopmonitor().reset()
            
            try:
                response = gpsd.get_current()
                Messages.GPS.Data( response).publish()
                
            except (KeyError, gpsd.NoFixError) as e:
                Messages.GPS.Error( e).publish()
            
            time.sleep( self.loopmonitor().looptime_remainder())
            
        return
    
    def start( self):
        try:
            gpsd.connect()
            super().start()
            
            return True
        
        except ConnectionRefusedError:
            return False
    
    def stop( self):
        return super().stop()
    
#
### File    mbus.py
#
from tau4.com import mbus


class Messages:
    
    class GPS:
        
        class Error(mbus.Message):
            
            def __init__( self, error):
                super().__init__()
                
                self.__error = error
                return
            
            def __str__( self):
                return "GPS Error: %s.\n" % self.__error

            
        class Data(mbus.Message):
            
            def __init__( self, gps_response):
                super().__init__()
                
                self.__gps_response = gps_response
                return
            
            def count_sats( self):
                return self.__gps_response.sats
            
            def error_margin( self):
                return self.__gps_response.error
            
            def hspeed( self):
                return self.__gps_response.speed()
            
            def ll2xy( self, lat, lon):
                y = lat * 111.111 * 1000
                x = cos( radians( lat)) * 111.111 * 1000
                return (x, y)
            
            def map_url( self):
                return self.__gps_response.map_url()
            
            def pos_precision( self):
                return self.__gps_response.position_precision()
            
            def posLL( self):
                return self.__gps_response.position()
            
            def posXY( self):
                return self.ll2xy( *self.posLL())

#
### File    __wx_main__.py
#
def _AppName_():
    return Varbls().fv_app_name().value()

def _AppVersion_():
    return "%d.%d.%d" % (0, 0, 0)

def _AppCaption_():
    return "%s Ver. %s" % (_AppName_(), _AppVersion_())



_USE_CUSTOM_EXCEPT_HOOK = 0
                                # Be aware, that using your own excpet hook is
                                #   not convenient during development. Activate
                                #   in releases only.

_LOGGING_LEVEL = (\
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
    )[0]



if _USE_CUSTOM_EXCEPT_HOOK:
    import traceback

    def Excepthook( typ, val, tbk):
        tbk_formatted = ""
        for file, line, module, info in traceback.extract_tb( tbk):
            tbk_formatted += "\tFile:\t%s\n\tLine:\t%d\n\tModule:\t%s\n\tInfo:\t%s\n\n" % (file, line, module, info)

        if tbk_formatted:
            tbk_formatted = tbk_formatted[:-1]

        additional_infos = "\tCurrent working directory = %s\n\tsys.argv = %s" % (os.getcwd(), sys.argv)
        logging.critical( "An uncaught exception has occurred:\ntype = '%s'\nvalue = '%s'\ntraceback:\n%s\nadditional infos:\n%s" \
                          % (typ, val, tbk_formatted, additional_infos)
                        )
        sys.__excepthook__( typ, val, tbk)
        return

    sys.excepthook = Excepthook



def _InitLogging_():
    logger = logging.getLogger()
    hdlr = handlers.RotatingFileHandler( "./%s.log" % _AppName_(), "a", 10000000, 10)
    formatter = logging.Formatter( "%(asctime)s %(process)d %(thread)d %(levelname)10s %(message)s")
    hdlr.setFormatter( formatter)
    logger.addHandler( hdlr)
    logger.setLevel( _LOGGING_LEVEL)
    return

_Logger = logging.getLogger()


class App(wx.App):

    def OnInit( self):
        main_frame = MainFrame( None, -1, _AppCaption_())
        splash = _SplashScreen( main_frame)
        splash.Show()
        self.SetTopWindow( main_frame)

        gpsr = GPSReader()
        if not gpsr.start():
            wx.MessageBox( "Cannot connect to GPS device!", "ERROR", wx.ICON_EXCLAMATION)
            
        return True
    

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

        s1.Add( _VarblViewBuilder( Varbls().fv_dbg_time_running()).view_actualFV( self, -1))
        s1.Add( _VarblViewBuilder( Varbls().fv_dbg_heartbeat()).view_actualFV( self, -1))
        s1.Add( _VarblViewBuilder( Varbls().fv_dbg_heartbeats_per_sec()).view_actualFV( self, -1))
        
        s2 = wx.StaticBoxSizer( wx.StaticBox( self, -1, "GPS"), wx.VERTICAL)
        s0.Add( s2, flag=wx.LEFT|wx.TOP, border=_PADDING)
        
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_SAT_COUNT)).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv_gps_data_x()).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv_gps_data_y()).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_DISTANCE_TO_ORG)).view_actualFV( self, -1))
        b = wx.Button( self, -1, "Current World Pos. As Org.")
        b.Bind( wx.EVT_BUTTON, self._wxEH_on_EVT_BUTTON_teach_org_)
        s2.Add( b, 0, wx.ALIGN_CENTER_HORIZONTAL)
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_HSPEED)).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_ERROR_MARGIN)).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_X)).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_POSITION_PRECISION_Y)).view_actualFV( self, -1))
        s2.Add( _VarblViewBuilder( Varbls().fv( Varbls.IDs._GPS_DATA_MAP_URL)).view_actualFV( self, -1))
        
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


class MainFrame(wx.Frame):

    def __init__( self, parent, id, caption):

        this_name = u"MainFrame.__init__"
                                        # The name of this method, just in case 
                                        #   we needed it for logging.
        ### Init the base class
        #
        wx.Frame.__init__( self, parent, id, caption, wx.DefaultPosition
                           , size=(700, 500)
                           #, style=wx.MAXIMIZE
                          )

        ### Build this MainFrame
        #
        self._build_()
                                        # Build the MainFrame
        self.Maximize()
                                        # Let the MainFrame fill the whole screen
        self.Layout()
                                        # 2DO: Is this still needed?

        ### Activate all events we will need
        #
        wx.EVT_IDLE( self, self._on_idle_)
        #  ^         ^     ^
        #  |         |     |
        #  |         |     Event target's event handler
        #  |         Event target
        #  Event
                                        # Activate IDLE events. These are called, 
                                        #   if the GUI is - well - IDLE. You may
                                        #   then do things you wouldn't want to do 
                                        #   if the GUI is processing.
        wx.EVT_CLOSE( self, self._on_close_window_)
                                        # Activate CLOSE event. You may want to 
                                        #   do some cleanup in case we are 
                                        #   closing down.

        ### Activate the IDLE-timer
        #
        self._idle_timer = wx.Timer( self)
        self.Bind( wx.EVT_TIMER, self._on_idle_timer_)
        self._idle_timer.Start( 100)

        ### Some attributes
        #
        self.__time_hbs = time.time()
        self._is_closing = False
        
        ### Schedulter für Heartbeat usw.
        #
        self.__schedulerthread = SchedulerThread( id=-1, looptime=0.010)
        self.__schedulerthread.start()

        def _handle_heartbeat_():
            FVs = Varbls()
            FVs.fv_dbg_heartbeat()
            FVs.fv_dbg_heartbeat().value( FVs.fv_dbg_heartbeat().value() + 1)

            FVs.fv_dbg_time_running().value( time.time() - FVs.fv_dbg_time_started().value())
            return
        
        self.__schedulerthread.scheduler().job_add( _handle_heartbeat_, 100)
        
        class _HeartbeatsPerSecHandler:
            
            def __init__( self, interval_ms):
                self.__interval_ms = interval_ms
                
                self.__heartbeats_at_last_call = 0
                return
                
            def __call__( self):
                FVs = Varbls()
                FVs.fv_dbg_heartbeats_per_sec().value( (FVs.fv_dbg_heartbeat().value() - self.__heartbeats_at_last_call)/self.__interval_ms*1000)
                self.__heartbeats_at_last_call = FVs.fv_dbg_heartbeat().value()
                return
                
        self.__schedulerthread.scheduler().job_add( _HeartbeatsPerSecHandler( 1000), 1000)

        def _handle_alive_message_( interval_ms=60000):
            Varbls().fv_logging_infos().value( "We are running for %.3f h now.\n" % (Varbls().fv_dbg_time_running().value()/3600))
         
        self.__schedulerthread.scheduler().job_add( _handle_alive_message_, 60000)

        return

    def _build_( self):
        """Builds the MainFrame, i.e. creates all widgets and puts them into sizers."""

        ### Put the App's icon in the MainFrame
        #
        if os.path.exists( "icon.ico"):
            icon = wx.EmptyIcon()
            bmp = wx.Image( "icon.ico").ConvertToBitmap()
            icon.CopyFromBitmap( bmp)
            self.SetIcon( icon)

        ### Create all the other widgets
        #
        s0 = wx.BoxSizer( wx.HORIZONTAL)
        
        s0.Add( _Dashboard( self, -1), 1, wx.EXPAND)

        s1 = wx.BoxSizer( wx.VERTICAL)
        s0.Add( s1, 2, wx.EXPAND|wx.ALL, 1)
        
        s1.Add( _VarblViewBuilder( Varbls().fv_gps_data_string()).view_loggingFV( self, -1), 3, wx.EXPAND)
        s1.Add( _VarblViewBuilder( Varbls().fv_logging_infos()).view_loggingFV( self, -1), 2, wx.EXPAND)
        s1.Add( _VarblViewBuilder( Varbls().fv_logging_errors()).view_loggingFV( self, -1), 1, wx.EXPAND)

        self.SetSizer( s0)
        s0.Fit( self)

        return

    def _on_close_window_( self, event):

        self._is_closing = True
        busy = wx.BusyInfo( "Just a moment, please...")
        wx.SafeYield( None, True)
        time.sleep( 1.0)

        self.Destroy()

    def _on_idle_( self, event):
        this_name = "MainFrame::_on_idle_"

        event.Skip()
        return

    def _on_idle_timer_( self, event):
        """Ensures that idle events get handled. 

        .. note::
            To do it this way is more efficient than a call to event.RequestMore() in each and every idle 
            event handler.

            Every idle event handler should call event.Skip() now.
        """
        if not self._is_closing:
            wx.WakeUpIdle()

        return

    def _on_timer_( self, event):
        if self._is_closing:
            return

        return



class _SplashScreen(adv.SplashScreen):

    def __init__( self, main_frame):
        if os.path.exists( "splash.png"):
            bmp = wx.Image( "splash.png").ConvertToBitmap()
        else:
            bmp = wx.EmptyBitmap( 500, 350)

        bmp = wx.Image( "splash.png").ConvertToBitmap()
        adv.SplashScreen.__init__( self, bmp
                                , adv.SPLASH_CENTRE_ON_SCREEN | adv.SPLASH_TIMEOUT
                                , 5000 
                                , None, -1
                                , size=(800,-1) 
                                )
        self._main_frame = main_frame
        self.Bind( wx.EVT_CLOSE, self.OnClose)
        self._fc = wx.FutureCall( 2000, self._show_main_)
        return

    def OnClose(self, evt):

        ### Make sure the default handler runs too so this window gets destroyed
        #
        evt.Skip()
        self.Hide()

        ### If the timer is still running then go ahead and show the MainFrame now
        #
        if self._fc.IsRunning():
            self._fc.Stop()
            self._show_main_()

        return

    def _show_main_(self):
        self._main_frame.Centre( wx.BOTH)
        self.Show( False)
        self._main_frame.Show( True)
        #if self._fc.IsRunning():
        #    self.Raise()
        # ### Guess, this isn't needed, is it?

        return



class _VarblViewBuilder:
    
    """Baut zusammengesetzte Controls, die auf flex.Variable arbeiten.
    """
    
    class _DefaultValueFormatter:
        
        def __call__( self, value):
            try:
                return "%.3f" % value
            
            except TypeError:
                return str( value)
        
        
    def __init__( self, fv):
        self.__fv = fv
        
        self.__valueformatter = self._DefaultValueFormatter()
        return
    
    def _fv_value_change_and_restore_( self, value):
        self.__fv.value( value)
        if isinstance( self.__fv, (flex._VariableMixinPersistor, flex._VariableMixinPersistor2)):
            self.__fv.store()
            
        return

    def valueformatter( self, formatter=None):
        if formatter is None:
            return self.__valueformatter

        self.__valueformatter = formatter
        return self
        
    
    def view_actualFV( self, parent, id):
        s = wx.BoxSizer( wx.HORIZONTAL)

        s.Add( self._view_label_( parent, -1), 2, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.LEFT, 5)
        
        tc = wx.TextCtrl( parent, -1, str( self.__fv.value()), style=wx.TE_READONLY|wx.TE_RIGHT)
        self.__fv.reg_tau4s_on_modified( lambda pc, w=tc: wx.CallAfter( tc.SetValue, self.__valueformatter( pc.client().value())))
        s.Add( tc, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, 5)

        v = self._view_dim_( parent, -1)        
        if v:
            s.Add( v, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            
        else:
            s.AddStretchSpacer( 1)
            
        return s
    
    def _view_dim_( self, parent, id):
        return wx.StaticText( parent, id, self.__fv.dim()) if self.__fv.dim() else None
    
    def _view_label_( self, parent, id):
        return wx.StaticText( parent, id, self.__fv.label())
    
    def view_loggingFV( self, parent, id):
        s = wx.BoxSizer( wx.VERTICAL)

        st = wx.StaticText( parent, -1, self.__fv.label())
        s.Add( st, 0, wx.TOP|wx.LEFT, 5)

        tc = wx.TextCtrl( parent, -1, str( self.__fv.value()), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.__fv.reg_tau4s_on_modified( lambda pc, w=tc: wx.CallAfter( tc.AppendText, pc.client().value()))
        s.Add( tc, 1, wx.EXPAND|wx.ALL, 5)

        return s
    
    def view_ratedFV( self, parent, id):
        """Sollwert-Widget für den Wert der flex.Variable.
     
     Der Typ wird von der flex.Variable bestimmt.
     
     Wenn die flex.Variable geändert wird, publisht sie das und dieses Widget 
     hat sich dafür angemeldet. Also wird, was gerade eingegeben worden ist, 
     durch dieses Publsihing angezeigt und zwar formatiert.
     """
        s = wx.BoxSizer( wx.HORIZONTAL)
        s.Add( self._view_label_( parent, -1), 1, wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.LEFT, 5)

        tc = wx.TextCtrl( parent, -1, str( self.__fv.value()), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT)
        tc.Bind( wx.EVT_TEXT_ENTER, self._wxEH_on_EVT_ENTER_)
        self.__fv.reg_tau4s_on_modified( lambda pc, w=tc: tc.SetValue( self.__valueformatter( pc.client().value())))
        s.Add( tc, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.TOP|wx.LEFT, 5)

        v = self._view_dim_( parent, -1)        
        if v:
            s.Add( v, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            
        else:
            s.AddStretchSpacer( 1)
            
        return s
    
    def _wxEH_on_EVT_ENTER_( self, wxE):
        wx.CallAfter( self._fv_value_change_and_restore_, wxE.GetEventObject().GetValue())
        return
    

def main():

    ### First we change the path to where the executable resides
    #
    if sys.platform.startswith( "win"):
        try:
            dirname = os.path.split(sys.argv[0])[0]
            os.chdir( dirname)
            
        except ValueError:
            pass

    ### Now we start logging
    #
    _InitLogging_()
    _Logger.critical( u"******** %s has started. ********" % _AppName_())
    _Logger.info( "Program has started with these args: '%s'. " % sys.argv)

    ### And finally we start the app
    #
    redirect_stderr_and_stdout = 0
    app = App( redirect_stderr_and_stdout)
    app.MainLoop()


if __name__ == '__main__':
    main()

