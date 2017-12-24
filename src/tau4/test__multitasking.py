#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
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


import abc
import logging
import random
import time
import unittest

from tau4 import DictWithUniqueKeys
from tau4.automation import controlunits as cu
from tau4 import ipc
from tau4.data import pandora
from tau4 import ios2
from tau4.ios2 import arduino, noios
from tau4.multitasking import processes
from tau4.multitasking.processes import Process
from tau4.oop import overrides
from tau4.time import Timer2


class JobAppMessageReader(processes.Job):

    def __init__( self):
        super().__init__( cycltime=0.010)
        return

    def execute( self):
        ipm  = "2DO"
        self.process()._message_to_app_( ipm)


class DataReporterProcess(processes.Process):

    def __init__( self, id=self.__class__.__name__, cycletime=cycletime):
        super().__init__( cycletime=cycletime)
        return

    def _run_( self, ipm2me):
        value = random.randint( -100, 100)
        ipm2app = IpmNewEncoderValue( value)
        self._message_to_app_( ipm2app)
        return


class IpmNewEncoderValue(ipc.InterProcessMessage):

    def __init__( self, value):
        super().__init__()

        self.__value = value
        self.__time_created = time.time()
        return

    def value( self):
        return self.__value

    def time( self):
        return self.__time_created


class IncValueRequest(ipc.InterProcessMessage):

    def __init__( self, value):
        super().__init__( self.__class__.__name__)

        self.__value = value
        return

    def value( self, value=None):
        if value is None:
            return self.__value

        self.__value = value
        return self


class PlainProcess(Process):

    def _run_( self, ipm: ipc.InterProcessMessage):
        if ipm and ipm.is_instance_of( IncValueRequest):
            ipm.value( ipm.value() + 1)
            self._message_to_app_( ipm)

        if ipm and ipm.is_instance_of( ipc.StandardInterProcessMessages.BoxesDict):
            boxesdict = ipc.DictToBoxesDict( ipm.dict())
            print( "Got Box-dict: '%s'. " % boxesdict)

        return


class _TESTCASE__0(unittest.TestCase):

    def test__simple( self):
        """
        """
        print()
        return


_Testsuite = unittest.makeSuite( _TESTCASE__0)


class _TESTCASE__Process(unittest.TestCase):

    def test__start_and_shutdown( self):
        """
        """
        print()

        n = 8
        processes = []
        with Timer2( "Creating and starting '%d' processes. " % n) as timer:
            for _ in range( n):
                processes.append( PlainProcess( 0.010))

            for process in processes:
                process.start()

        print( timer.results())

        with Timer2( "Stopping '%d' processes. " % n) as timer:
            for _ in range( n):
                p = processes.pop()
                p.shutdown()
                p.join()

        print( timer.results())
        return

    def test__com( self):
        """
        """
        print()

        p = PlainProcess( 0.010)
        p.start()

        p.message( IncValueRequest( 41))
        ipm = p.message()
        self.assertAlmostEqual( 42, ipm.value())

        p.shutdown( syncly=True)
        return

    def test__cycletime_10_ms( self):
        """
        """
        print()

        p = PlainProcess( 0.010)
        p.start()

        time.sleep( 0.100)

        p.message( ipc.StandardInterProcessMessages.EffectiveCycletimeRequest())
        ipm = p.message()
        print( "Effective Cycletime of process = '%.3f'." % ipm.value())
        self.assertAlmostEqual( 0.010, ipm.value(), places=3)

        p.shutdown( syncly=True)
        return

    def test__cycletime_5_ms( self):
        """
        """
        print()

        cycletime = 0.005

        p = PlainProcess( cycletime)
        p.start()

        print( "Sleep 1 sec to let the process do its job. ")
        time.sleep( 1.0)

        p.message( ipc.StandardInterProcessMessages.EffectiveCycletimeRequest())
        ipm = p.message()
        print( "Effective Cycletime of process = '%.3f'." % ipm.value())
        self.assertAlmostEqual( cycletime, ipm.value(), places=3)

        p.shutdown( syncly=True)
        return

    def test__shutdown_syncly( self):
        """
        """
        print()

        p = PlainProcess( 0.010)
        p.start()

        p.shutdown( syncly=True)
        return

    def test__boxtransfer( self):
        """
        """
        print()

        p = PlainProcess( 0.010)
        p.start()

        d = ipc.BoxesListToDict( [ pandora.Box( id="box %d" % i, value=i) for i in range( 1000)])
        p.message( ipc.StandardInterProcessMessages.BoxesDict( d))

        p.shutdown( syncly=True)
        return

    def test__reading_sensor_values( self):
        """
        """
        print()

        p = DataReporterProcess( 0.010)
        p.start()

        t0 = time.time()
        while time.time() - t0 < 3:
            ipm: ipc.InterProcessMessage = p.message()
            if ipm.is_instance_of( IpmNewEncoderValue):
                dt = time.time() - ipm.time()
                print( "Got new sensor reading: '%.3f'. Time elapsed since creation of that value: '%.3f ms'. " % (ipm.value(), dt * 1000))

        p.shutdown( syncly=True)
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__Process))


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


class _PLC(cu.ProgrammableLogicControl):

    def __init__( self, cycletime):
        super().__init__( cycletime)

        self.__led13time = 0
        self.__led13duration = 0.5
        self.__led13value = 0
        return

    @overrides( cu.ProgrammableLogicControl)
    def _hwinps_read_( self):
        ios2.IOSystem().execute_inps()
        return

    @overrides( cu.ProgrammableLogicControl)
    def _hwouts_write_( self):
        ios2.IOSystem().execute_outs()
        return

    @overrides( cu.ProgrammableLogicControl)
    def on_cycleend( self):
        """DEBUG.
        """
        super().on_cycleend()
        return

    @overrides( cu.ProgrammableLogicControl)
    def _run_( self, ipm: ipc.InterProcessMessage):
        if self.dinp_value( iochannelid="rc -> plc", iousrid="enabled") == 0:
            self.dout_value( iochannelid="plc -> rc", iousrid="enable", value=1)

        if self.dinp_value( iochannelid="rc -> plc", iousrid="enabled") == 1:
            self.dout_value( iochannelid="plc -> usr", iousrid="rop.is_enabled", value=1)

            if self.dinp_value( iochannelid="rc -> plc", iousrid="started") == 0:
                self.dout_value( iochannelid="plc -> rc", iousrid="start", value=1)

        if self.dinp_value( iochannelid="rc -> plc", iousrid="started") == 1:
            self.dout_value( iochannelid="plc -> usr", iousrid="rop.is_started", value=1)

        if time.time() - self.__led13time  > self.__led13duration:
            ios2.IOSystem().douts( "started").value( self.__led13value)
            self.__led13value = 1 - self.__led13value
            if self.__led13value:
                self.__led13duration = max( 0.1, self.__led13duration - 0.05)

            self.__led13time = time.time()

        return

    @overrides( cu.ProgrammableLogicControl)
    def setup( self):
        """Setup von ios2.IOSystem und ios2.IOBoards, was nur hier erfolgen darf: Die PLC ist der einzige Prozess, der auf die physischen IOs zugreifen darf!
        """
        ios2.IOBoards().board_add( board=arduino.BoardPyMata(), usrid_board="arduino")

        ios2.IOSystem().dout_add( arduino.DOutNano( board=ios2.IOBoards().board( "arduino"), id_sys=13, is_hi_active=True, label=""), id_usr="started")
        return


class _RC(cu.RobotControl):

    def __init__( self, cycletime):
        super().__init__( cycletime)
        return

    def _inpchannel_plc_( self) -> cu.SwIoChannel:
        return self._inpchannels_by_channelid[ "plc -> rc"]

    def _outchannel_plc_( self) -> cu.SwIoChannel:
        return self._outchannels_by_channelid[ "rc -> plc"]

    @overrides( cu.RobotControl)
    def _run_( self, ipm: ipc.InterProcessMessage):
        if self.dinp_value( iochannelid="plc -> rc", iousrid="enable") == 1:
            self.dout_value( iochannelid="rc -> plc", iousrid="enabled", value=1)

        if self.dout_value( iochannelid="rc -> plc", iousrid="enabled") == 1:
            if self.dinp_value( iochannelid="plc -> rc", iousrid="start") == 1:
                self.dout_value( iochannelid="rc -> plc", iousrid="started", value=1)

        return

    @overrides( cu.ProgrammableLogicControl)
    def setup( self):
        return


class Usr:

    def __init__( self):
        self._inpchannels_by_channelid = {}
        return


################################################################################
### Lab
#
def _lab__ioimages_for_plcs_():

    time.sleep( 0.5)


    ### IOs definieren
    #
    iodefs = (
        ### rc -> plc
        #
        cu.SwIoDef( usrid="enabled",        channelid="rc -> plc",      value=0.0,  iotype="d"),
        cu.SwIoDef( usrid="started",        channelid="rc -> plc",      value=0.0,  iotype="d"),

        ### plc -> rc
        #
        cu.SwIoDef( usrid="enable",         channelid="plc -> rc",      value=0.0,  iotype="d"),
        cu.SwIoDef( usrid="start",          channelid="plc -> rc",      value=0.0,  iotype="d"),
        cu.SwIoDef( usrid="bA",             channelid="plc -> rc",      value=0.0,  iotype="a"),
        cu.SwIoDef( usrid="bX",             channelid="plc -> rc",      value=0.0,  iotype="a"),
        cu.SwIoDef( usrid="bY",             channelid="plc -> rc",      value=0.0,  iotype="a"),

        ### plc -> usr
        #
        cu.SwIoDefs.DO( usrid="rop.is_enabled", channelid="plc -> usr",     value=0,  iotype="d"),
        cu.SwIoDefs.DO( usrid="rop.is_started", channelid="plc -> usr",     value=0,  iotype="d"),
    )

    ### Channels bauen, die obige Images enthalten
    #
    iochannelbuilder = cu.IoChannelBuilder( iodefs)
    iochanneldict = iochannelbuilder.iochannels()
                                    # Liefert alle IO-Channels
    assert len( iochanneldict) == 3

    ### Controls erzeugen
    #
    plc = _PLC( 0.010)
    rc = _RC( 0.010)

    usr = Usr()

    ### Channels in die Controls eintragen
    #
    iochannelid = "rc -> plc"
    iochannel = iochannelbuilder.iochannel( iochannelid)
    rc.channel_add( iochannelid, iochannel)
    rc.iochannel_connect( iochannelid, plc)

    iochannelid = "plc -> rc"
    iochannel = iochannelbuilder.iochannel( iochannelid)
    plc.channel_add( iochannelid, iochannel)
    plc.iochannel_connect( iochannelid, rc)

    iochannelid = "plc -> usr"
    iochannel = iochannelbuilder.iochannel( iochannelid)
    plc.channel_add( iochannelid, iochannel)
    plc.iochannel_connect( iochannelid, usr)

    ### Controls starten
    #
    plc.start( syncly=True)
    rc.start( syncly=True)

    swioreader = cu.SwIoImagereader( usr._inpchannels_by_channelid)
    t0 = time.time()
    while time.time() - t0 <= 5:
        swioreader.execute( "plc -> usr")
        time.sleep( 0.010)

    print( "_ l a b _ _ i o i m a g e s _ f o r _ p l c s _ ( ):", usr._inpchannels_by_channelid)
    print( "=" * 80)

    rc.shutdown( True)
    plc.shutdown( True)

    assert usr._inpchannels_by_channelid[ "plc -> usr"].rcvimage().dinp_value( "rop.is_enabled") == 1
    assert usr._inpchannels_by_channelid[ "plc -> usr"].rcvimage().dinp_value( "rop.is_started") == 1
    return


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


if __name__ == '__main__':
    import multiprocessing as mp
    #mp.set_start_method( "spawn")
#    _Test_()
    logging.getLogger().setLevel( 10)
    _lab__ioimages_for_plcs_()
    input( u"Press any key to exit...")



