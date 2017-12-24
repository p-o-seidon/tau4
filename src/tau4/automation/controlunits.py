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
import copy
import ctypes
import logging; _Logger = logging.getLogger()
import multiprocessing as mp
from multiprocessing import queues as mpqueue
import _pickle as pickle
import queue

from tau4 import DictWithUniqueKeys
from tau4.data import pandora
from tau4 import ios2
from tau4 import ipc
from tau4.multitasking import processes as mtp
from tau4.multitasking import threads as mtt
from tau4.oop import overrides, Singleton
from tau4.time import Timer2


################################################################################
### M e s s a g e s
#
class InternalInterProcessMessages:

    class RequestAInpsImage(ipc.InterProcessMessage):

        pass


    class RequestUpdateAOutsImage(ipc.InterProcessMessage):

        pass


    class RequestDInpsImage(ipc.InterProcessMessage):

        pass


    class RequestUpdateDOutsImage(ipc.InterProcessMessage):

        pass


#    class RequestImageProcessing(ipc.InterProcessMessage):
#
#        pass


################################################################################
### I O s   etc.
#
class IoDef(abc.ABC):

    """

    \param  channelid   ...
                Ist channelid None, dann handelt es sich um eine Definition
                eines HwIoImage -s, das HwIoControl vorbehalten ist.
    """

    def __init__( self, *, channelid, usrid, value, iotype):
        self._usrid = usrid
        self._channelid = channelid
        self._iotype = iotype
        self._typecaster = { "a": float, "d": int}[ iotype]
        self._value = self._typecaster( value)
        return

    def __iter__( self):
        for attr in (self._usrid, self._value, self._iotype):
            yield attr

    def __lshift__( self, other):
        self._usrid = other._usrid
        self._value = other._value
        self._iotype = other._iotype
        self._typecaster = other._typecaster
        return self

    def __ne__( self, other):
        return not self == other

    def __repr__( self):
        return "%s( '%s', '%s', '%s', '%s')" % (self.__class__.__name__, self._channelid, self._usrid, self._value, self._iotype)


    @abc.abstractmethod
    def ioimageclass( self):
        pass


class HwIoDef(IoDef):

    def __init__( self, usrid, channelid, value, sysid, boardid):
        super().__init__( usrid, channelid, value)
        self._sysid = sysid
        self._boardid = boardid
        return

    @abc.abstractmethod
    def board_configure( self):
        pass

    def ioimage( self):
        return HwIoImage2( ())

    def ioimageclass( self):
        return HwIoImage2


class HwIoDefs:

    class AI(HwIoDef):

        pass


    class AO(HwIoDef):

        pass


    class DI(HwIoDef):

        pass


    class DInpArduino(DI):

        def __init__( self, usrid, value, is_hi_active, sysid, boardid):
            super().__init__( usrid, None, value, sysid, boardid)
            self._is_hi_active = is_hi_active
            return

        def board_configure( self):
            ios2.IOBoards().board( self._boardid).set_pinmode_DINP( self._sysid)
            return


    class DO(HwIoDef):

        pass


    class DOutArduino(DO):

        def __init__( self, usrid, value, is_hi_active, sysid, boardid):
            super().__init__( usrid, None, value, sysid, boardid)
            self._is_hi_active = is_hi_active
            return

        def board_configure( self, board):
            board.set_pinmode_DOUT( self._sysid)
            return


class SwIoDef(IoDef):

    def __init__( self, *, channelid, usrid, value, iotype):
        super().__init__( channelid=channelid, usrid=usrid, value=value, iotype=iotype)
        return

    def ioimage( self):
        return SwIoImage2( ())

    def ioimageclass( self):
        return SwIoImage2


class SwIoDefs:

    class AI(SwIoDef):

        pass


    class AO(SwIoDef):

        pass


    class DI(SwIoDef):

        pass


    class DO(SwIoDef):

        pass


class IoImageBuilder:

    def __init__( self, iodefs):
        self.__iodefs = iodefs

        self.__ioimages = {}
        return

    def ioimages( self):
        if not self.__ioimages:
            for iodef in self.__iodefs:
                if iodef._channelid not in self.__ioimages:
                    self.__ioimages[ iodef._channelid] = iodef.ioimage()

                self.__ioimages[ iodef._channelid]._iodef_add_( iodef)

        return self.__ioimages


class IoPortBuilder:

    def __init__( self, iodefs, boards):
        self.__iodefs = iodefs
        self.__boards = boards
        return

    def ioport( self):
        return HwIoPort( self.__iodefs, self.__boards)


################################################################################
### I m a g e
#
class _IoImageline:

    """Zeile eines IoImage (Hardware oder Software) und damit ein, AInp, AOut, DInp oder DOut.

    \note   Nicht für die direkte Anwendung: _HsIoImageline oder _HwIoImageline verwenden!

    \note   Nicht für den User bestimmt.
    """

    @staticmethod
    def FromList( attrs):
        return _IoImageline( *attrs)


    def __init__( self, usrid, value, iotype):
        super().__init__()
        self._usrid = usrid
        self._iotype = iotype
        self._typecaster = { "a": float, "ai": float, "ao": float, "d": int, "di": int, "do": int, "aiv": float, "div": int}[ iotype]
        self._value = self._typecaster( value)
        return

    def __eq__( self, other):
        if not self.__class__.__name__ == other.__class__.__name__:
            return False

        if self._usrid != other._usrid:
            return False

        if self._iotype != other._iotype:
            return False

        if self._value != other._value:
            return False

        return True

    def __iter__( self):
        for attr in (self._usrid, self._value, self._iotype):
            yield attr

    def __lshift__( self, other):
        self._usrid = other._usrid
        self._value = other._value
        self._iotype = other._iotype
        self._typecaster = other._typecaster
        return self

    def __ne__( self, other):
        return not self == other

    def __repr__( self):
        return "%s( '%s', '%s', '%s')" % (self.__class__.__name__, self._usrid, self._value, self._iotype)


class _SwIoImageline(_IoImageline):

    """IoImageline eines IoSwImage.

    \param  usrid   Id, unter der die Image Line im IoImage gefunden wird.

    \param  value   Wert des IOs.

    \param  iotype  EInes von 'ai', 'ao', 'di', 'do'.

    """

    def __init__( self, usrid, value, iotype):
        assert iotype in ("a", "d"), "Assertion failed: iotype = %s (usrid = %s). " % (iotype, usrid)
        super().__init__( usrid, value, iotype)
        return


class _HwIoImageline(_IoImageline):

    """IoImageline eines IoHwImage.

    \param  usrid   Id, unter der die Image Line im IoImage gefunden wird.

    \param  sysid   Id, die von der Hardware mit der boardid erwartet wird, wenn
                    von ihr gelesen oder auf sie geschrieben wird.

    \param  value   Wert des IOs.

    \param  iotype  Eines von 'ai', 'ao', 'di', 'do'.

    \param  boardid Id des Hardware Boards, also z.B. 'arduino' oder 'raspi'.
    """

    def __init__( self, usrid, sysid, value, iotype, boardid):
        assert iotype in ( "ai", "ao", "di", "do", "aiv", "aov", "div", "dov")
        super().__init__( usrid, value, iotype)

        self._sysid = sysid
        self._boardid = boardid
        return

    def __iter__( self):
        for attr in (self._usrid, self._sysid, self._value, self._iotype, self._boardid):
            yield attr

    def __lshift__( self, other):
        super().__lshift__( other)
        self._sysid = other._sysid
        self._boardid = other._boardid
        return self

class _HwInp(_HwIoImageline):

    """_HwIoImageline "interpretiert" als HW-Eingang.
    """

    def __init__( self, usrid, sysid, value, iotype, boardid):
        super().__init__( usrid, sysid, value, iotype, boardid)


class HwInpA(_HwInp):

    """_HwIoImageline "interpretiert" als HW-Eingang analog.
    """

    def __init__( self, usrid, sysid, value, boardid):
        super().__init__( usrid, sysid, value, "ai", boardid)


class HwInpAV(HwInpA):

    """_HwIoImageline "interpretiert" als HW-Eingang analog und virtuell.
    """

    def __init__( self, usrid, sysid, value, boardid):
        super().__init__( usrid, sysid, value, boardid)


class HwInpD(_HwInp):

    """_HwIoImageline "interpretiert" als HW-Eingang digital.
    """

    def __init__( self, usrid, sysid, value, boardid):
        super().__init__( usrid, sysid, value, "di", boardid)


class HwInpDV(HwInpA):

    """_HwIoImageline "interpretiert" als HW-Eingang digtal und virtuell.
    """

    def __init__( self, usrid, sysid, value, boardid):
        super().__init__( usrid, sysid, value, boardid)


class IoImage2(abc.ABC):

    """Container von IoImageline Instanzen.
    """

    ############################################################################
    def __init__( self):
        self._iodefs_by_usrid = DictWithUniqueKeys()
        return

    def __eq__( self, other):
        if not self.__class__.__name__ == other.__class__.__name__:
            return False

        for usrid in self._iodefs_by_usrid:
            if self._iodefs_by_usrid[ usrid] != other._iodefs_by_usrid[ usrid]:
                return False

        return True

    def __lshift__( self, other):
        for usrid in self._iodefs_by_usrid:
            self._iodefs_by_usrid[ usrid] << other._iodefs_by_usrid[ usrid]

        return self

    def __ne__( self, other):
        return not self == other

    def __repr__( self):
        ss = []
        for il in self._iodefs_by_usrid.values():
            ss.append( str( il))

        s = "\n\t".join( ss)
        return s

    def _iodef_add_( self, iodef):
        self._iodefs_by_usrid[ iodef._usrid] = iodef
        return self

    def __getstate__( self):
        return self.__dict__.copy()

    def __setstate__( self, state):
        self.__dict__.update( state)
        return

    def ainp_value( self, usrid):
        """Eingang aus IoImage lesen.

        Usage
            \code{.py}

                print( "RC errornumber = %s. " % self._inpimages_by_channelid[ "rc -> plc"].ainp_value( "errornumber"))
                                                # Codezeile in einer User PLC.

            \endcode
        """
        il = self._iodefs_by_usrid[ usrid]
        assert il._iotype in ("a", "ai")
        return il._value

    def aout_value( self, usrid, value=None):
        """Ausgang in IoImage schreiben.

        Usage
            \code{.py}

                self._outimages_by_channelid[ "rc -> plc"].aout_value( "errornumber", 42)
                                                # Codezeile in einer Custom Control Unit.

            \endcode
        """
        il = self._iodefs_by_usrid[ usrid]
        assert il._iotype in ("a", "ao")
        if value is None:
            return il._value

        il._value = il._typecaster( value)
        return self

    def clone( self):
        return copy.deepcopy( self)

    def dinp_value( self, usrid):
        """Siehe ainp_value().
        """
        il = self._iodefs_by_usrid[ usrid]
        assert il._iotype in( "d", "di")
        return il._value

    def dout_value( self, usrid, value=None):
        """Siehe aout_value().
        """
        il = self._iodefs_by_usrid[ usrid]
        assert il._iotype in( "d", "do")
        if value is None:
            return il._value

        il._value = il._typecaster( value)
        return self



class HwIoImage2(IoImage2):

    """IoImage für den Transfer von und zur Hardware.

    \note   Dieses Image darf nur die Instanz HwIoControl (von der es nur eine geben darf) verwenden.
    """

    def __init__( self, iodefs):
        super().__init__()

        for iodef in iodefs:
            self._iodef_add_( iodef)

        return


class SwIoImage2(IoImage2):

    """IoImage für den Transfer zwischen Control Instanzen, es ist also keine Hardware beteiligt.
    """

    def __init__( self, iodefs):
        super().__init__()

        channelids = set()
        for iodef in iodefs:
            self._iodef_add_( iodef)
            channelids.add( iodef._channelid)

        self.__iochannelid = None
        return

#    def iochannel( self):
#        return SwIoChannel( self, MailboxBasedOnMpPipe( self.iochannelid()))

#    def iochannelid( self):
#        if not self.__iochannelid:
#            self.__iochannelid = set( [ iodef._channelid for iodef in self._iodefs_by_usrid.values()]).pop()
#
#        return self.__iochannelid


class IoImageTransferrer(abc.ABC):

    """Transferiert IoImage über Mailbox nstanzen.
    """

    def __init__( self, iochannels_by_channelid):
        self._iochannels_by_channelid = iochannels_by_channelid
        return

    @abc.abstractmethod
    def execute( self):
        pass


class HwIoImageTransferrer(IoImageTransferrer):

    """Transfer der IOs von und zur Hardware.

    \note   Die benötigten Boards müssen vom User initialisiert worden sein!

    \param  boards  ios2.IOBoards(), das aber vn HwIoControl initialisiert worden
            sein muss (siehe dort).
    """

    def __init__( self, boards, hwiochannel_from_hw, hwiochannel_to_hw):
        super().__init__( { "from hw": hwiochannel_from_hw, "to hw": hwiochannel_to_hw})

        self.__boards = boards
        return

    @overrides( IoImageTransferrer)
    def execute( self):
        self.inps_from_hardware()
        self.outs_to_hardware()
        return

    def inps_from_hardware( self, rcvimage: HwIoImage2):
        hwoutchannel = self._iochannels_by_channelid[ "to hw"]
        if hwoutchannel.sndimage_is_marked_as_dirty():
            for usrid in rcvimage._imagelines_by_usrid:
                il = rcvimage._imagelines_by_usrid[ usrid]
                board = self.__boards.board( il._boardid)
                if il._iotype == "ai":
                    il._value = board.ainp_value( il._sysid) if board else 42

                elif il._iotype == "di":
                    il._value = board.dinp_value( il._sysid) if board else 42

                elif il._iotype == "aiv":
                    il._value = board.vainp_value( il._sysid) if board else 42

                elif il._iotype == "div":
                    il._value = board.vdinp_value( il._sysid) if board else 42

                else:
                    raise ValueError( "Unknown iotype = %s, expected one of 'ai', 'di'. " % il._iotype)

            hwoutchannel.sndimage_unmark_as_dirty()

        return

    def outs_to_hardware( self, sndimage: HwIoImage2):
        for usrid in sndimage._imagelines_by_usrid:
            il = sndimage._imagelines_by_usrid[ usrid]
            board = self.__boards.board( il._boardid)
            if il._iotype == "ao":
                board.aout_value( il._sysid, il._value) if board else None

            elif il._iotype == "do":
                board.dout_value( il._sysid, il._value) if board else None


            else:
                raise ValueError( "Unknown iotype = %s, expected one of 'ao', 'do'. " % il._iotype)

        return


class SwIoImagereader(IoImageTransferrer):

    def __init__( self, inpchannels_by_channelid):
        super().__init__( inpchannels_by_channelid)
        return

    @overrides( IoImageTransferrer)
    def execute( self, iochannelid):
        """Kopiert das Image aus der Mailbox ins rcvimage.
        """
        iochannel = self._iochannels_by_channelid[ iochannelid]
        iochannel.get_rcvimage()
        return


class SwIoImagewriter(IoImageTransferrer):

    """Schreibt ein SwIoImage in einen IoChannel, der sowohl das SwIoImage als auch die Mailbox des IoChannel enthält.
    """
    def __init__( self, inpchannels_by_channelid):
        super().__init__( inpchannels_by_channelid)
        return

    def execute( self, iochannelid):
        """Kopiert das sndimage in die Mailbox.
        """
        iochannel = self._iochannels_by_channelid[ iochannelid]
        if iochannel.sndimage_is_marked_as_dirty():
            iochannel.put_sndimage()
            iochannel.sndimage_unmark_as_dirty()

        return


class _Mailbox:

    """Mailbox des IoChannel und damit der eigentliche Kanal.

    Die Mailbox unterscheidet sich von einer Queue, Connection (oder was auch immer)
    dadurch, dass der Sender darin befindliche Daten überschreibt, wenn sie durch
    den Empfänger nicht abgeholt worden sind. So ist gesichert, dass der Empfänger
    nur aktuelle Daten erhält.

    \_2DO   Derzeit ist die Mailbox realisiert per mp.Queue. Eine mp.Connection oder
            mp.Pipe wäre zu überlegen.
    """

    def __init__( self, iochannelid):
        self._iochannelid = iochannelid

        self.__flag_ioimage_has_changed = mp.Value( "i", 1)
        self._lock = mp.Lock()
        return

    def __repr__( self):
        return "%s( '%s')" % (self.__class__.__name__, self._iochannelid)

    def _ioimage_unpickled_( self, ioimage_pickled):
        try:
            return pickle.loads( ioimage_pickled)

        except (EOFError, pickle.UnpicklingError) as e:
            return None

    def _ioimage_pickled_( self, ioimage, protocol=0):
        ioimage_picked = pickle.dumps( ioimage, protocol=protocol)
                                        # Wie's scheint, kann man keine binären
                                        #   Daten in ein mp.Array stecken. Also
                                        #   müssen wir "human readable" arbeiten.
        return ioimage_picked

    def ioimage_is_marked_as_dirty( self):
        """_IoImage is (virtually) marked as changed.
        """
        return self.__flag_ioimage_has_changed.value

    def ioimage_mark_as_dirty( self):
        """Mark _IoImage (virtually) as changed.
        """
        self.__flag_ioimage_has_changed.value = 1
        return self

    def ioimage_unmark_as_dirty( self):
        """Unmark _IoImage (virtually) as changed.
        """
        self.__flag_ioimage_has_changed.value = 0
        return self


class MailboxBasedOnMpQueue(_Mailbox):

    """Mailbox des IoChannel und damit der eigentliche Kanal, basierend auf einer mp.Queue.

    Die Mailbox unterscheidet sich von einer Queue, Connection (oder was auch immer)
    dadurch, dass der Sender darin befindliche Daten überschreibt, wenn sie durch
    den Empfänger nicht abgeholt worden sind. So ist gesichert, dass der Empfänger
    nur aktuelle Daten erhält.

    \warning    Nicht zuverlässig!
    """

    def __init__( self, iochannelid):
        super().__init__( iochannelid)

        self.__q = mp.Queue()
        self.__lock = mp.Lock()
        return

    def put_nowait( self, ioimage):
        """Senden, Ausführung durch Sender.
        """
        try:
            self.__q.put( ioimage, block=False)

        except queue.Full:

            with self.__lock:
                try:
                    while 1:
                        ioimage = None
                        ioimage = self.__q.get( block=True, timeout=0.0001)

                except queue.Empty:
                    try:
                        self.__q.put( ioimage, block=False)

                    except queue.Full:
                        _Logger.critical( "Mailbox.clear_and_put_nowait(): Queue   m u s t   n o t   b e   f u l l   here, but is!")
                                                        # Das kann wirklich passieren, ich fasse es nicht!

        return self

    def get_nowait( self):
        """Nichtblockierendes Empfangen, Ausführung durch Empfänger.

        \returns    None    wenn keine Daten zum Empfangen da sind.
        """
        with self.__lock:
            try:
                ioimage = self.__q.get_nowait()

            except queue.Empty:
                ioimage = None

        return ioimage


class MailboxBasedOnMpValue(_Mailbox):

    """Mailbox des IoChannel und damit der eigentliche Kanal, basierend auf mp.Array.

    Die Mailbox unterscheidet sich von einer Queue, Connection (oder was auch immer)
    dadurch, dass der Sender darin befindliche Daten überschreibt, wenn sie durch
    den Empfänger nicht abgeholt worden sind. So ist gesichert, dass der Empfänger
    nur aktuelle Daten erhält.

    Nicht schnell, aber zuverlässig.

    \param  size    Größe des Arrays, das für den Datentransfer verwendet wird.
                    Muss leider so früh festgelegt werden. Schlimmer noch: Man
                    kann auch zuwenig angeben (sehr große Images).
    """

    def __init__( self, iochannelid, size=4096):
        super().__init__( iochannelid)

# ##### Hängt sich beim Unpicklen auf! Siehe dazu _ioimage_unpickled_().
#        self.__ioimage_pickled = mp.Value( ctypes.c_char_p, lock=True)
        self.__ioimage_pickled = mp.Array( "c", size)
# #####
        self.__ioimage_pickled.value = pickle.dumps( "", protocol=0)
                                        # Wie's scheint, kann man keine binären
                                        #   Daten in ein mp.Array stecken. Also
                                        #   müssen wir "human readable" arbeiten: protocol=0
        self.__ioimage_pickled_remembered = ""
        return

    def put_nowait( self, ioimage):
        """Senden, Ausführung durch Sender.
        """
        with self._lock:
            if self._ioimage_is_dirty_():
                                            # ACHTUNG: _ioimage_is_dirty_() setzt
                                            #   die Dirty-Erkennung für den nächsten
                                            #   Durchlauf automatisch zurück!
                self.ioimage_mark_as_dirty()
                self.__ioimage_pickled.value = self._ioimage_pickled_( ioimage)

            return self

    def get_nowait( self):
        """Nichtblockierendes Empfangen, Ausführung durch Empfänger.

        \returns    None    wenn keine Daten zum Empfangen da sind.
        """
        with self._lock:
            ioimage = None
            if self.ioimage_is_marked_as_dirty():
                ioimage = self._ioimage_unpickled_( self.__ioimage_pickled.value)
                if not ioimage:
                    ioimage = None

                self.ioimage_unmark_as_dirty()

            return ioimage

    def _ioimage_is_dirty_( self):
        """_IoImage has changed, so we will mark it (virtually).

        \note   _ioimage_is_dirty_() setzt
                die Dirty-Erkennung für den nächsten
                Durchlauf automatisch zurück!
        """
        is_dirty = self.__ioimage_pickled != self.__ioimage_pickled_remembered
        self.__ioimage_pickled_remembered = self.__ioimage_pickled.value
        return is_dirty


class MailboxBasedOnMpPipe(_Mailbox):

    """Mailbox des IoChannel und damit der eigentliche Kanal, basierend auf mp.Pipe und mp.Connection.

    Die Mailbox unterscheidet sich von einer Queue, Connection (oder was auch immer)
    dadurch, dass der Sender darin befindliche Daten überschreibt, wenn sie durch
    den Empfänger nicht abgeholt worden sind. So ist gesichert, dass der Empfänger
    nur aktuelle Daten erhält.

    Relativ schnell und zuverlässig.
    """

    def __init__( self, iochannelid):
        super().__init__( iochannelid)

        self.__conn_rcv, self.__conn_snd = mp.Pipe( False)
        self.__lock = mp.Lock()
        return

    def put_nowait( self, ioimage):
        """Senden, Ausführung durch Sender.
        """
        with self.__lock:
            try:
                self.__conn_snd.send( ioimage)

            except ValueError as e:
                _Logger.critical( "%s.put_nowait(): %s. ", self.__class__.__name__, e)

        return self

    def get_nowait( self):
        """Nichtblockierendes Empfangen, Ausführung durch Empfänger.

        \returns    None    wenn keine Daten zum Empfangen da sind.
        """
        ioimage = None
        with self.__lock:
            try:
                while self.__conn_rcv.poll():
                    ioimage = self.__conn_rcv.recv()

            except ValueError as e:
                _Logger.critical( "%s.get_nowait(): %s. ", self.__class__.__name__, e)

        return ioimage


class HwIoPort:

    """Erzeugt aus IoDef -s ios2.Port -s und stellt sie HwIoControl zur Verfügung.

    HwIoControl bemüht den HwIoTransferrer, um SwIoImage2 zur Hardware zu
    tranferieren und umgekehrt.

    \_2DO
        Es gibt keinen SwIoPort. Also umbenennen in IoPort?
    """

    def __init__( self, iodefs, boards):
        self.__iodefs = iodefs
        self.__boards = boards

        self.__ainps = {}
        self.__dinps = {}
        self.__aouts = {}
        self.__douts = {}

        for iodef in self.__iodefs:
            if isinstance( iodef, ( HwIoDefs.AI, HwIoDefs.DI)):
                self.__inpimage._iodef_add_( iodef)

            elif isinstance( iodef, ( HwIoDefs.AO, HwIoDefs.DO)):
                self.__outimage._iodef_add_( iodef)

        return

    def boards_configure( self):
        for iodef in self.__inpimage.iodefs() + self.__outimage.iodefs():
            try:
                board = self.__boards[ iodef._boardid]
                iodef.board_configure( board)

            except KeyError:
                _Logger.critical( "%s.%s(): Board '%s' not found. ", self.__class__.__name__, "boards_configure", iodef._boardid)

        return

    def read( self):
        return

    def write( self):
        return


class SwIoChannel:

    """Kommunikationskanal zwischen zwei Control Instanzen.

    Enthält eine Mailbox und zwei Images. Eines davon ist das Source Image, das
    andere das Destination Image. Ersteres wird von Process 1 geschrieben,
    letzteres von Process 2 gelesen. Der Transfer wird vom Process 1 an jedem
    Zyklusende über eine Mailbox erledigt.
    """

    def __init__( self, ioimage: IoImage2, mailbox: _Mailbox):
        self.__mailbox = mailbox

        self._sndimage = ioimage
        self._rcvimage = ioimage.clone()

        self._sndimage_remembered = ioimage.clone()
        self._rcvimage_remembered = ioimage.clone()

        self.__p_boxes = {}
        for usrid, iodef in self._rcvimage._iodefs_by_usrid.items():
            self.__p_boxes[ usrid] = pandora.Box( value=iodef._value)
                                            # 2DO: Bereinigen: Wie kann eine
                                            #   ROM-Definition einen Value haben?!
        return

    def __repr__( self):
        return "%s( \nsndimage=\n\t%s, \nrcvimage=\n\t%s) @%s" % (self.__class__.__name__, self._sndimage, self._rcvimage, id( self))

    def ainp_value( self, iousrid):
        """Lesen eines Wertes vom Receive Image, das in jedem Zyklus von der Mailbox gelesen wird.
        """
        return self.rcvimage().ainp_value( iousrid)

    def aout_value( self, iousrid, value=None):
        """Schreiben eines Wertes ins Send Image, das in jedem Zyklus in die Mailbox geschrieben wird.
        """
        if value is None:
            return self.sndimage().aout_value( iousrid)

        return self.sndimage().aout_value( iousrid, value)

    def dinp_value( self, iousrid):
        """Lesen eines Wertes vom Receive Image, das in jedem Zyklus von der Mailbox gelesen wird.
        """
        return self.rcvimage().dinp_value( iousrid)

    def dout_value( self, iousrid, value=None):
        """Schreiben eines Wertes ins Send Image, das in jedem Zyklus in die Mailbox geschrieben wird.
        """
        if value is None:
            return self.sndimage().dout_value( iousrid)

        return self.sndimage().dout_value( iousrid, value)

    def get_rcvimage( self):
        """IoImage aus Mailbox lesen, damit dann per rcvimage() auf den aktuellen Inhalt zugegriffen werden kann.
        """
        ioimage = self.__mailbox.get_nowait()
        if ioimage:
            self._rcvimage = ioimage
            self._rcvimage_to_boxes_()

        return self

    def mailbox( self) -> _Mailbox:
        return self.__mailbox

    def p_box( self, ioid):
        return self.__p_boxes[ ioid]

    def put_sndimage( self):
        """IoImage in die Mailbox schreiben (Zugriff auf dieses IoImage per sndimage()).
        """
        if self.sndimage_is_marked_as_dirty():
            self.__mailbox.put_nowait( self._sndimage)

            self.sndimage_unmark_as_dirty()

        return self

    def rcvimage( self) -> IoImage2:
        """IoImage, das von get_rcvimage() aus der Mailbox gelesen wird.
        """
        return self._rcvimage

    def _rcvimage_to_boxes_( self):
        for usrid, iodef in self._rcvimage._iodefs_by_usrid.items():
            self.__p_boxes[ usrid].value( iodef._value)

        return self

#    def rcvimage_is_marked_as_dirty( self):
#        """Siehe sndimage_is_marked_as_dirty().
#        """
#        return self._rcvimage != self._rcvimage_remembered
# ##### Sinnlos!

    def sndimage_is_marked_as_dirty( self):
        """Am SwIoImage hat sich etwas geändert.

        Wird vom HwIoImageTransferrer dazu verwendet zu entscheiden, ob das SwIoImage
        versendet werden soll.
        """
        return self._sndimage != self._sndimage_remembered

#    def rcvimage_unmark_as_dirty( self):
#        """Siehe sndimage_is_marked_as_dirty().
#        """
#        self._rcvimage_remembered << self._rcvimage
#        return self
# ##### Sinnlos!

    def sndimage( self) -> IoImage2:
        """IoImage, das von put_sndimage() in die Mailbox geschrieben wird.
        """
        return self._sndimage

    def sndimage_unmark_as_dirty( self):
        """Siehe sndimage_is_marked_as_dirty().
        """
        self._sndimage_remembered << self._sndimage
        return self


class IoChannelBuilder:

    """Erzeugt aus den IoDef -s die SwIoChannel -s.
    """

    def __init__( self, iodefs):
        self.__iodefs = iodefs

        self.__iochannels = {}
        return

    def _build_iochannels_( self):

        ### Wir bauen uns ein Nested Dict
        #
        iodefdicts_by_channelid = {}
        for iodef in self.__iodefs:
            if not iodef._channelid in iodefdicts_by_channelid:
                iodefdicts_by_channelid[ iodef._channelid] = DictWithUniqueKeys()

        for iodef in self.__iodefs:
            iodefdicts_by_channelid[ iodef._channelid][ iodef._usrid] = iodef

        ### Jetzt bauen wir die Channels
        #
        for channelid, iodefs in iodefdicts_by_channelid.items():
            ioimage = SwIoImage2( list( iodefs.values()))
            iochannel = SwIoChannel( ioimage, MailboxBasedOnMpValue( channelid))
            self.__iochannels[ channelid] = iochannel

        return

    def iochannel( self, iochannelid) -> SwIoChannel:
        return self.iochannels()[ iochannelid]

    def iochannels( self):
        if not self.__iochannels:
            self._build_iochannels_()

        return self.__iochannels


################################################################################
#### C o n t r o l   -   Base Class aller Controls
#
class ControlCP(mtp.CyclingProcess):

    """Unit Control, die bereits mit einigen Standard-Features ausgestattet ist.

    Features:
        -   Lesen SwIoImage Instanzen
        -   Schreiben SwIoImage Instanzen

    \note   Eine Control hat IoImages und läuft zyklisch.

    \note   Images von der Hardware lesen und auf sie schreiben darf nur die
            HwIoControl!
    """

    def __init__( self, cycletime):
        super().__init__( id=self.__class__.__name__, cycletime=cycletime)

        ### Channels und ihre Reader und Writer
        #
        self._inpchannels_by_channelid = {}
        self._outchannels_by_channelid = {}

        self._swioimagereader = SwIoImagereader( self._inpchannels_by_channelid)
        self._swioimagewriter = SwIoImagewriter( self._outchannels_by_channelid)
        return

    def ainp_value( self, iochannelid, iousrid):
        return self._inpchannels_by_channelid[ iochannelid].rcvimage().ainp_value( iousrid)

    def aout_value( self, iochannelid, iousrid, value=None):
        if value is None:
            return self._outchannels_by_channelid[ iochannelid].sndimage().aout_value( iousrid)

        return self._outchannels_by_channelid[ iochannelid].sndimage().dout_value( iousrid, value)

    def dinp_value( self, iochannelid, iousrid):
        return self._inpchannels_by_channelid[ iochannelid].rcvimage().dinp_value( iousrid)

    def dout_value( self, iochannelid, iousrid, value=None):
        if value is None:
            return self._outchannels_by_channelid[ iochannelid].sndimage().dout_value( iousrid)

        return self._outchannels_by_channelid[ iochannelid].sndimage().dout_value( iousrid, value)

    def inpchannel( self, iochannelid):
        return self._inpchannels_by_channelid[ iochannelid]

    def outchannel( self, iochannelid):
        return self._outchannels_by_channelid[ iochannelid]

    def iochannel_connect( self, iochannelid, control):
        """Zu einer Control gehörigen Sendekanal mit einem anderen Control verbinden.
        """
        control._inpchannels_by_channelid[ iochannelid] = self._outchannels_by_channelid[ iochannelid]
                                        # 2DO: Methode einführen
        return

#    def iochannel_create( self, iochannelid, sndimage):
#        """Zu einer Control gehörigen Sendekanal erzeugen.
#
#        Usage
#            \code{.py}
#                proloco = _PLC( 0.010)
#
#                roco = _RC( 0.010)
#
#                usr = Usr()
#
#
#                iochannelid = "plc -> rc"
#                outimage = cu.SwIoImage( \
#                    [ \
#                        ( "enable", 0, "d"),
#                        ( "start", 0, "d"),
#                        ( "RESERVED.1", 0, "a"),
#                        ( "RESERVED.2", 0, "a"),
#                        ( "RESERVED.3", 0, "a"),
#                        ( "RESERVED.4", 0, "a"),
#                        ( "RESERVED.5", 0, "a"),
#                        ( "RESERVED.6", 0, "a"),
#                        ( "RESERVED.7", 0, "a"),
#                        ( "RESERVED.8", 0, "a"),
#                        ( "RESERVED.9", 0, "a"),
#                    ]
#                )
#                proloco.iochannel_create( iochannelid, outimage)
#                proloco.iochannel_connect( iochannelid, roco)
#
#                iochannelid = "plc -> usr"
#                outimage = cu.SwIoImage( \
#                    [ \
#                        ( "rop.is_enabled", 0, "d"),
#                        ( "rop.is_started", 0, "d"),
#                        ( "RESERVED.1", 0, "a"),
#                        ( "RESERVED.2", 0, "a"),
#                        ( "RESERVED.3", 0, "a"),
#                        ( "RESERVED.4", 0, "a"),
#                        ( "RESERVED.5", 0, "a"),
#                        ( "RESERVED.6", 0, "a"),
#                        ( "RESERVED.7", 0, "a"),
#                        ( "RESERVED.8", 0, "a"),
#                        ( "RESERVED.9", 0, "a"),
#                    ]
#                )
#                proloco.iochannel_create( iochannelid, outimage)
#                proloco.iochannel_connect( iochannelid, usr)
#
#                outimage = cu.SwIoImage( \
#                    [ \
#                        ( "enabled", 0, "d"),
#                        ( "started", 0, "d"),
#                        ( "errornumber", 0, "a"),
#                        ( "RESERVED.1", 0, "a"),
#                        ( "RESERVED.2", 0, "a"),
#                        ( "RESERVED.3", 0, "a"),
#                        ( "RESERVED.4", 0, "a"),
#                        ( "RESERVED.5", 0, "a"),
#                        ( "RESERVED.6", 0, "a"),
#                        ( "RESERVED.7", 0, "a"),
#                        ( "RESERVED.8", 0, "a"),
#                        ( "RESERVED.9", 0, "a"),
#                    ]
#                )
#                roco.iochannel_create( "rc -> plc", outimage)
#                roco.iochannel_connect( "rc -> plc", proloco)
#
#
#                proloco.start( syncly=True)
#                roco.start( syncly=True)
#
#                swioreader = cu.SwIoImagereader( usr._inpchannels_by_channelid)
#                t0 = time.time()
#                while time.time() - t0 <= 1.0:
#                    swioreader.execute( "plc -> usr")
#                    time.sleep( 0.010)
#
#                roco.shutdown( True)
#                proloco.shutdown( True)
#
#            \endcode
#        """
#        self._outchannels_by_channelid[ iochannelid] = SwIoChannel( sndimage, MailboxBasedOnMpPipe( iochannelid))
#        return

    def iochannel_add( self, iochannelid, iochannel):
        self._outchannels_by_channelid[ iochannelid] = iochannel

        return

    def _swioimages_read_( self):
        """Liest ein IO-Image aus dem IoChannel.

        Bedient sich hierzu eines SwIoImagereader -s.
        """
        for iochannelid in self._inpchannels_by_channelid:
            self._swioimagereader.execute( iochannelid)
                                            # Liefert ein Image MMIC -> PLC usw.
        return self

    def _swioimages_write_( self):
        """Schreibt ein IO-Image in den IoChannel.

        Bedient sich hierzu eines SwIoImagewriter -s.
        """
        for iochannelid in self._outchannels_by_channelid:
            self._swioimagewriter.execute( iochannelid)

        return

    @overrides( mtp.CyclingProcess)
    def on_cycleend( self):
        #with Timer2( "%s: Write ioimages" % self.__class__.__name__, info_about_testee=False) as timer:
        if 1:
            ### Images lesen
            #
            self._swioimages_write_()

            super().on_cycleend()

        #print( timer.results())
        return

    @overrides( mtp.CyclingProcess)
    def on_cyclebeg( self):
        #with Timer2( "%s: Read ioimages" % self.__class__.__name__, info_about_testee=False) as timer:
        if 1:
            ### Images lesen
            #
            self._swioimages_read_()

            super().on_cyclebeg()

        #print( timer.results())
        return


class ControlCT(mtt.CyclingThread, metaclass=abc.ABCMeta):

    def __call__( self):
        return self

    @overrides(mtt.CyclingThread)
    def on_cyclebeg( self):
        #with Timer2( "%s.on_cyclebeg()" % self.__class__.__name__) as timer:
        if 1:
            self._transfer_inps_()

            super().on_cyclebeg()

        #print( timer.results())
        return

    @overrides(mtt.CyclingThread)
    def on_cycleend( self):
        #with Timer2( "%s.on_cycleend()" % self.__class__.__name__) as timer:
        if 1:
            self._transfer_outs_()

            super().on_cycleend()

        #print( timer.results())
        return

    @abc.abstractmethod
    def _run_( self):
        pass

    @abc.abstractmethod
    def _transfer_inps_( self):
        pass

    @abc.abstractmethod
    def _transfer_outs_( self):
        pass


################################################################################
#### I O - C o n t r o l
#
class HwIoControl(ControlCP):

    """Unit Control, die die Hardware liest und schreibt.

    Sie bedient sich hierbei Instanzen der Klassen HwIoChannel und HwIoImageTransferrer.

    \param  cycletime

    \param  hwinpimage  Image der HARDWARE-Eingänge

    \param  hwoutimage  Image der HARDWARE-Ausgänge

    """

    def __init__( self, cycletime, ioport: HwIoPort):
        super().__init__( cycletime=cycletime)

        self.__ioport = ioport
        self.__hwioimagetransferrer = None

        return

    @overrides( ControlCP)
    def _run_( self, ipm):
        return

    def hwinpimage( self):
        """Image, das von der Hardware gelesen wird - also die Eingänge.

        Usage
            Kann dazu verwendet werden, ein SwIoImage zu erstellen, das vom PLC
            Control benötigt wird, um das HwIoControl ansprechen zu können (IOs
            lesen und schreiben).

            \code{.py}
                iochannelid = "hwioc -> plc"
                outimage = hioc.hwinpimage().as_SwIoImage()
                hioc.iochannel_create( iochannelid, outimage)
                hioc.iochannel_connect( iochannelid, proloco)
            \endcode
        """
        return self.__ioport.inpimage()

    def hwoutimage( self):
        """Image, das auf die Hardware geschrieben wird - also die Ausgänge.

        Usage
            Kann dazu verwendet werden, ein SwIoImage zu erstellen, das vom PLC
            Control benötigt wird, um das HwIoControl ansprechen zu können (IOs
            lesen und schreiben).

            \code{.py}
                iochannelid = "plc -> hwioc"
                outimage = hioc.hwoutimage().as_SwIoImage()
                plc.iochannel_create( iochannelid, outimage)
                plc.iochannel_connect( iochannelid, hioc)

            \endcode
        """
        return self.__ioport.outimage()

    def _hwioimages_read_( self):
        """Liest ein HwIoImage von der Hardware und ein SwIoImage aus einem Channel.
        """
        self.__hwioimagetransferrer.inps_from_hardware( self.__ioport.inpimage())
        return

    def _hwioimages_write_( self):
        """Schreibt ein HwIoImage auf die Hardware und ein SwIoImage in einen SwIoChannel.
        """
        self.__hwioimagetransferrer.outs_to_hardware( self.__ioport.outimage())
        return

    @overrides( ControlCP)
    def on_cycleend( self):
        """IoImage -s   s c h r e i b e n.
        """
        ### SW-Images schreiben
        #
        super().on_cycleend()

        ### SW-Image (nur das erste und hoffentlich einzige) aufs HW-Image schreiben
        #
        swioimage = list( self._inpchannels_by_channelid.values())[ 0]._rcvimage
        for usrid in self._hwoutchannel._sndimage._imagelines_by_usrid:
            hwil = self._hwoutchannel._sndimage._imagelines_by_usrid[ usrid]
            swil = swioimage._iodefs_by_usrid[ usrid]
            hwil._value = swil._value

        ### HW-Image schreiben
        #
        self._hwioimages_write_()
        return

    @overrides( ControlCP)
    def on_cyclebeg( self):
        """IoImage -s   l e s e n
        """
        ### SW-Images lesen
        #
        super().on_cyclebeg()

        ### HW-Image lesen
        #
        self._hwioimages_read_()

        ### HW-Image auf SW-Images schreiben
        #
        swioimage = list( self._outchannels_by_channelid.values())[ 0]._sndimage
        for usrid in self._hwinpchannel._rcvimage._iodefs_by_usrid:
            hwil = self._hwinpchannel._rcvimage._iodefs_by_usrid[ usrid]
            swil = swioimage._iodefs_by_usrid[ usrid]
            swil._value = hwil._value

        return

    @overrides( ControlCP)
    def setup( self):
        """Board konfiguieren, Transferrer für die HwIoImage2 -s instanzieren.
        """
        self.__ioport.boards_configure()
        self.__hwioimagetransferrer = HwIoImageTransferrer( self.__boards, self.__ioport)
        return


################################################################################
#### P r o g r a m m a b l e   L o g i c   C o n t r o l
#
class ProgrammableLogicControl(ControlCP):

    """SPS.
    """

    def __init__( self, cycletime):
        super().__init__( cycletime)
        return

    @abc.abstractmethod
    def _hwinps_read_( self):
        pass

    @abc.abstractmethod
    def _hwouts_write_( self):
        pass

    @overrides( ControlCP)
    def on_cycleend( self):
        super().on_cycleend()

        self._hwouts_write_()
        return

    @overrides( ControlCP)
    def on_cyclebeg( self):
        super().on_cyclebeg()

        self._hwinps_read_()
        return


################################################################################
#### R o b o t   C o n t r o l
#
class RobotControl(ControlCP):

    """RC.

    Aktuell gibt es 2 Stantdard Control Classes:

    -   ProgrammableLogicControl
    -   RobotControl
    """

    def __init__( self, cycletime):
        super().__init__( cycletime)
        return