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

from math import sin, sqrt
import os
import string
import sys

from tau4.data import flex
from tau4.datalogging import UsrEventLog
from tau4.time import SchedulerThread

import traceback
import time
import wx
from wx import adv

from tau4.app4wxp import pages
from tau4.app4wxp.data import Varbls

_PADDING = 5


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
        show_splashscreen = False
        main_frame = MainFrame( None, -1, _AppCaption_())
        if show_splashscreen:
            splash = _SplashScreen( main_frame)
            splash.Show()
            
        else:
            main_frame.Show()

        self.SetTopWindow( main_frame)

        gpsr = GPSReader()
#        if and not gpsr.start():
#            wx.MessageBox( "Cannot connect to GPS device!", "ERROR", wx.ICON_EXCLAMATION)
            
        return True
    

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
        if os.path.exists( "./wxp/icon.ico"):
            icon = wx.EmptyIcon()
            bmp = wx.Image( "./wxp/icon.ico").ConvertToBitmap()
            icon.CopyFromBitmap( bmp)
            self.SetIcon( icon)
            
        else:
            UsrEventLog().log_error( "File './wxp/icon.ico' not found!")

        ### Create all the other widgets
        #
        s0 = wx.BoxSizer( wx.HORIZONTAL)
        
        nb = wx.Notebook( self, -1)
        s0.Add( nb, 1, wx.EXPAND)
#        pages.NotebookPageOscilloscope( nb, -1)
        pages.NotebookPageOscilloscopeMPL( nb, -1)
        pages.NotebookPageGPS( nb, -1)
        
        self.SetSizerAndFit( s0)
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
            
        Varbls().fv( Varbls.IDs.Oscilloscope._CHANNEL_1).value( 50*sin( time.time()))
        Varbls().fv( Varbls.IDs.Oscilloscope._CHANNEL_2).value( 50*sin( 2*time.time()))

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

