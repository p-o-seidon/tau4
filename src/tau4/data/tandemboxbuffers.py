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
#
################################################################################

"""\package tandemboxbuffers    Dieses Modul ist für den Austausch von internal IOs von Control Units und ist extrem viel schneller als doublebuffers.py.

Eine sendende Control Unit (z.B. "plc") besitzt eine ImageCollection, die aus so
vielen Image's besteht, wie es Control Units gibt, die Interesse an den internal
Outs der sendenden Control unit haben.

Jedes Image besteht aus sogenannten _TandemBox's, die wiederum aus 2 Box's
bestehen - einer Inbox und einer Outbox.

Die TandemBox'es unterscheiden sich in _TandemBoxS und _TandemBoxR, ebenso die
_Image's: _ImageS und _ImageR.

Der Sender schreibt während seines Zyklusses in die Inbox der _TandemBoxS
"seines" _ImageS. Am Ende des Zyklusses kopiert er die Inbox aller _TandemBoxS's
in deren Outbox. Damit sind aber automatisch alle Inboxes aller Empfängerimages
auf dem neuesten Stand, weil deren Inbox identisch (im Sinn von 'is') ist mit der
jeweiligen Outbox des _ImageS, das gerade kopiert worden ist. Sie müssen nun nur
noch ihrerseits die Inboxes in die Outboxes aller _ImageR's kopieren.

Dieses Konzept erlaubt es den Empfängern, immer mit einem konsistenten Datensatz
(Outboxes der _TandemBoxR's des _ImageR) zu arbeiten.

Performance-Fall 1::

    [fgeiger@triton tau4]$ python3 test__data_tandemboxbuffers.py
    test__performance (__main__._TESTCASE__0) ...
    3 images with 10 values each.
    -----------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.001 ms = 1.331 us.
    Timer(): Start timing 'Publishing image'...
    Timer2(): 'Publishing image' took 0.000 s = 0.015 ms = 14.751 us.
    Timer(): Start timing 'Copying image'...
    Timer2(): 'Copying image' took 0.000 s = 0.013 ms = 13.132 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 0.825 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.031s

    OK
    Press any key to exit...

Performance-Fall 2::

    [fgeiger@triton tau4]$ python3 test__data_tandemboxbuffers.py
    test__performance (__main__._TESTCASE__0) ...
    3 images with 100 values each.
    ------------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.001 ms = 1.294 us.
    Timer(): Start timing 'Publishing image'...
    Timer2(): 'Publishing image' took 0.000 s = 0.110 ms = 110.036 us.
    Timer(): Start timing 'Copying image'...
    Timer2(): 'Copying image' took 0.000 s = 0.111 ms = 111.086 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 0.811 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.226s

    OK
    Press any key to exit...

Performance-Fall 3::

    test__performance (__main__._TESTCASE__0) ...
    10 images with 100 values each.
    -------------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.001 ms = 1.269 us.
    Timer(): Start timing 'Publishing image'...
    Timer2(): 'Publishing image' took 0.000 s = 0.111 ms = 111.005 us.
    Timer(): Start timing 'Copying image'...
    Timer2(): 'Copying image' took 0.000 s = 0.111 ms = 111.259 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 0.815 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.233s

    OK
    Press any key to exit...

Performance-Fall 4::

    [fgeiger@triton tau4]$ python3 test__data_tandemboxbuffers.py
    test__performance (__main__._TESTCASE__0) ...
    20 images with 100 values each.
    -------------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.001 ms = 1.406 us.
    Timer(): Start timing 'Publishing image'...
    Timer2(): 'Publishing image' took 0.000 s = 0.110 ms = 110.429 us.
    Timer(): Start timing 'Copying image'...
    Timer2(): 'Copying image' took 0.000 s = 0.112 ms = 112.196 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 0.804 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.242s

    OK
    Press any key to exit...

\_2DO
    In CRUISER4 einbauen.

"""


import abc
import copy
import threading


from tau4.data import pandora
from tau4.oop import overrides, PublisherChannel
from tau4.multitasking import RWLock


_DO_LOGGING = False


class _TandemBox(metaclass=abc.ABCMeta):

    """pandora.Box-Paar, das für die Kommunikation zwischen Control Units verwendet werden kann.

    Die TandemBox besteht aus 2 Box'en, eine fürs Schreiben, eine fürs Lesen.
    Deise beiden Box'en können (und sollten nur) vom Leser umgeschaltet werden.
    Wenn mehrere TandemBox'en im Einsatz sind, kann der Leser so sicherstellen,
    mit einem konsistenten Datensatz zu arbeiten.

    \param  vid
        Value Id

    \param  value
        Startwert. \b Achtung: Der Typ des angegebenen Wertes bestimmt den Typ
        der TandemBox!

    """

    def __init__( self, vid, value, label="", dim=""):
        self.__vid = vid
        self._inbox = pandora.Box( value=value)
        self._outbox = pandora.Box( value=value)
        self._inbox.label( label)
        self._outbox.label( label)
        self._inbox.dim( dim)
        self._outbox.dim( dim)

        self.__is_inbox_dirty = False

        self.__lock = threading.Lock()
        self.__on_value_changed = PublisherChannel.Synch( self)
        return

    def reg_tau4s_on_modified( self, tau4s):
        self.__on_value_changed += tau4s
        return

    def _inbox_( self):
        """Nur für Testzwecke - siehe Testsuite.
        """
        return self._inbox

    def inbox_to_outbox( self):
        """Sender-Inbox in Sender-Outbox (Publishing)  o d e r  Receiver-Inbox in Receiver-Outbox kopieren.
        """
        self._outbox.value( self._inbox.value())
        return self

    def _outbox_( self):
        return self._outbox

    def unreg_tau4s_on_modified( self, tau4s):
        self.__on_value_changed -= tau4s
        return

    @abc.abstractmethod
    def value( self, value=None):
        """Wert lesen/schreiben.
        """
        pass

    def vid( self):
        """Value Id.
        """
        return self.__vid


class _TandemBoxS(_TandemBox):

    def __init__( self, vid, value, label="", dim=""):
        super().__init__( vid, value, label="", dim="")
        return

    @overrides( _TandemBox)
    def value( self, value=None):
        """Wert lesen/schreiben aus/in Inbox.
        """
        if value is None:
            return self._inbox.value()

        self._inbox.value( value)
        self.__is_inbox_dirty = True
        return self


class _TandemBoxR(_TandemBox):

    """

    \param  inbox
        Outbox des Senders.
    """

    def __init__( self, vid, value, inbox, label="", dim=""):
        super().__init__( vid, value, label="", dim="")

        self._inbox = inbox
        return

    @overrides( _TandemBox)
    def value( self):
        """Wert lesen aus Outbox.
        """
        return self._outbox.value()


class _Image(metaclass=abc.ABCMeta):

    """"Liste" von TandemBox's.

    Jede TandemBox ist einem Out einer Control Unit zugeordnet.
    """

    def __init__( self, lock: RWLock):
        self._tandemboxes = {}
        self._lock = lock
        return

    @abc.abstractmethod
    def inboxes_to_outboxes( self):
        """Inboxes nach Outboxes kopieren.
        """
        pass

    def value( self, id_value, value=None):
        if value is None:
            return self._tandemboxes[ id_value].value()

        self._tandemboxes[ id_value].value( value)
        return self

    def vids( self):
        return self._tandemboxes.keys()


class _ImageS(_Image):

    """Sender-Image, jede Control Unit hat genau eines.

    Es gibt also m Sender-Images, wenn es m Control Units gibt.
    """

    def _add_tandembox_( self, vid, value, label="", dim=""):
        """_TandemBoxS hinzufügen.
        """
        self._tandemboxes[ vid] = tandemboxS = _TandemBoxS( vid, value, label, dim)
        return tandemboxS

    def inboxes_to_outboxes( self):
        """Inboxes nach Outboxes kopieren.

        Jeder Sender arbeitet nur mit der Inbox, wobei das allerdings
        transparent ist.
        """
        self._lock.acquire_writeaccess()

        for tandembox in self._tandemboxes.values():
            assert isinstance( tandembox, _TandemBoxS)
            tandembox.inbox_to_outbox()

        self._lock.release_writeaccess()

        return self


class _ImageR(_Image):

    """Empfänger-Image, jede Control Unit hat so viele, wie es andere Control Units gibt.

    Es gibt also m * (m - 1) Empfänger-Images, wenn es wenn es m Control Units gibt.

    """

    def __lshift__( self, other: _ImageS):
        """Neues Empfänger-Image dem entsprechenden Sender-Image 'nachbauen', sodass es die _TandemBoxR's hat, die mit den _TandemBoxS's des Senders verbunden sind.
        """
        assert isinstance( other, _ImageS)
        for tandemboxS in other._tandemboxes.values():
            assert isinstance( tandemboxS, _TandemBoxS)
            self._tandemboxes[ tandemboxS.vid()] \
                = _TandemBoxR( \
                    tandemboxS.vid(),
                    tandemboxS.value(),
                    tandemboxS._inbox_(),
                    tandemboxS.label(),
                    tandemboxS.dim()
                  )

        return self

    def _add_tandembox_( self, vid, inbox):
        """_TandemBoxR hinzufügen.
        """
        self._tandemboxes[ vid] = tandemboxR = _TandemBoxR( vid=vid, inbox=inbox, value=inbox.value())
        return tandemboxR

    def inboxes_to_outboxes( self):
        """Inboxes nach Outboxes kopieren.

        Jeder Empfänger arbeitet nur mit der Outbox, wobei das allerdings
        transparent ist.
        """
        self._lock.acquire_readaccess()

        for tandembox in self._tandemboxes.values():
            assert isinstance( tandembox, _TandemBoxR)
            tandembox.inbox_to_outbox()

        self._lock.release_readaccess()
        return self


class _ImageCollection:

    """Images aller Control Units.
    """

    def __init__( self, id_sending_control_unit):
        self.__id_sending_control_unit = id_sending_control_unit

        self.__lock = RWLock( do_logging=_DO_LOGGING)
        self.__receiverimages = {}
        self.__senderimage = _ImageS( self.__lock)
        return

    def __getitem__( self, rid):
        """Ermöglicht dict-like Zugriff auf Receiver Images.

        \param  rid
            Receiver Id
        """
        return self.__receiverimages[ rid]

    def image_add( self, id_receiving_control_unit):
        """Ein neues Empfänger-Image _ImageR zu dieser TandemBoxCollections-Instanz hinzufügen.
        """
        self.__receiverimages[ id_receiving_control_unit] = _ImageR( self.__lock) << self.__senderimage
        return self

    def id( self):
        return self.__id_sending_control_unit

    def inboxes_to_outboxes( self):
        """Sender kopiert Inboxes in die Outboxes des Sender-Images _ImageS.
        """
        self.__senderimage.inboxes_to_outboxes()
        return

    def value( self, vid, value=None):
        """Schreibt in die Inbox, liest aus der Inbox.
        """
        return self.__senderimage.value( vid, value)

    def value_add( self, vid, value, label="", dim=""):
        """Eine neue TandemBox zum Sender-Image und allen Empfänger-Images dieser TandemBoxCollections-Instanz hinzufügen.
        """
        tandemboxS = self.__senderimage._add_tandembox_( vid, value, label, dim)

        for image in self.__receiverimages.values():
            image._add_tandembox_( vid=vid, inbox=tandemboxS._outbox_())

        return self



_Images = {}
def Images( senderids=None):

    """Images des ganzen Systems erzeugen.

    Usage
        \code{.py}
            ### Alle Images aufbauen
            #
            images = Images( ("plc", "mmi", "rc", "any"))

            ### Value in die ImageCollection einhängen
            #
            images[ "plc"].add_value( "value.1", 1.0)
            self.assertAlmostEqual( 1.0, images[ "plc"].value( "value.1"))
            self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

            ### Value schreiben
            #
            images[ "plc"].value( "value.1", 42.0)
            self.assertAlmostEqual( 42.0, images[ "plc"].value( "value.1"))
            self.assertAlmostEqual( 1.0, images[ "plc"][ "mmi"].value( "value.1"))

            ### Sender "switcht"
            #
            images[ "plc"].inboxes_to_outboxes()

            ### Empfänger "switcht"
            #
            images[ "plc"]["mmi"].inboxes_to_outboxes()

            ### Empfänger liest Wert
            #
            value = images[ "plc"][ "mmi"].value( "value.1")
            self.assertAlmostEqual( 42.0, images[ "plc"][ "mmi"].value( "value.1"))

        \endcode
    """


    if senderids:
        _Images.clear()

        sids = set( senderids)
        for sid in sids:
            _Images[ sid] = _ImageCollection( sid)
            for rid in sids - set( (sid,)):
                _Images[ sid].image_add( rid)

    return _Images

