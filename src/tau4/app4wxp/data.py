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

import logging; from logging import handlers

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
        
        
        class Oscilloscope:
            
            _CHANNEL_1 = "oscilloscope.channel.1"
            _CHANNEL_2 = "oscilloscope.channel.2"
        
        
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
        
        ### Oscilloscope
        #
        fv = flex.VariableDeMo( id=Varbls.IDs.Oscilloscope._CHANNEL_1, value=0.0, label="Channel 1", dim="V", value_min=None, value_max=None)
        flex.Variable.InstanceStore( fv.id(), fv)
        
        fv = flex.VariableDeMo( id=Varbls.IDs.Oscilloscope._CHANNEL_2, value=0.0, label="Channel 2", dim="V", value_min=None, value_max=None)
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
    
    
