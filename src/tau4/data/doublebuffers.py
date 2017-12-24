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

"""\package doublebuffers   Dieses Modul ist für den Austausch von internal IOs von Cotrol Units.

Eine sendende Control Unit (z.B. "plc") besitzt eine ImageCollection, die aus so
vielen Image's besteht, wie es Control Units gibt, die Interesse an den internal
Outs der sendenden Control unit haben.

Jedes Image besteht aus sogenannten TandemBox's, die wiederum aus 2 Box's
bestehen - einer Sender Box und einer Receiver Box. Dieses Konzept erlaubt es,
statt Values zu kopieren, einfach die beiden Box's umzuschalten.

Um alle Box's eines Image's umzuschalten, muss der Sender oder Empfänger einfach
das Image umschalten.

Dieses onzept erlaubt es den Empfängern, immer mit einem konsitsnten Datensatz
(Image) zu arbeiten.

Performance mit 3 Control Units mit je 10 Outs::

    [fgeiger@triton tau4]$ python3 test__data_doublebuffers.py
    test__performance (__main__._TESTCASE__0) ...
    3 images with 10 values each.
    -----------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.002 ms = 1.747 us.
    Timer(): Start timing 'Flushing master image'...
    Timer2(): 'Flushing master image' took 0.000 s = 0.043 ms = 42.967 us.
    Timer(): Start timing 'Switching all images'...
    Timer2(): 'Switching all images' took 0.000 s = 0.005 ms = 5.344 us.
    Timer(): Start timing 'Switching one image'...
    Timer2(): 'Switching one image' took 0.000 s = 0.003 ms = 2.684 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 1.276 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.055s

    OK
    Press any key to exit...

Performance mit 3 Control Units mit je 100 Outs::

    [fgeiger@triton tau4]$ python3 test__data_doublebuffers.py
    test__performance (__main__._TESTCASE__0) ...
    3 images with 100 values each.
    ------------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.002 ms = 1.707 us.
    Timer(): Start timing 'Flushing master image'...
    Timer2(): 'Flushing master image' took 0.000 s = 0.412 ms = 411.703 us.
    Timer(): Start timing 'Switching all images'...
    Timer2(): 'Switching all images' took 0.000 s = 0.044 ms = 43.832 us.
    Timer(): Start timing 'Switching one image'...
    Timer2(): 'Switching one image' took 0.000 s = 0.023 ms = 23.031 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.002 ms = 1.578 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.485s

    OK
    Press any key to exit...

Performance mit 10 Control Units mit je 100 Outs::

    [fgeiger@triton tau4]$ python3 test__data_doublebuffers.py
    test__performance (__main__._TESTCASE__0) ...
    10 images with 100 values each.
    -------------------------------
    Timer(): Start timing 'Writing value'...
    Timer2(): 'Writing value' took 0.000 s = 0.002 ms = 1.783 us.
    Timer(): Start timing 'Flushing master image'...
    Timer2(): 'Flushing master image' took 0.002 s = 1.544 ms = 1543.605 us.
    Timer(): Start timing 'Switching all images'...
    Timer2(): 'Switching all images' took 0.000 s = 0.207 ms = 207.113 us.
    Timer(): Start timing 'Switching one image'...
    Timer2(): 'Switching one image' took 0.000 s = 0.022 ms = 21.714 us.
    Timer(): Start timing 'Reading value'...
    Timer2(): 'Reading value' took 0.000 s = 0.001 ms = 1.294 us.
    ok
    test__simple (__main__._TESTCASE__0) ...
    ok
    test (__main__._TESTCASE__) ...
    ok

    ----------------------------------------------------------------------
    Ran 3 tests in 1.783s

    OK
    Press any key to exit...

"""


import copy
import threading


from tau4.data import pandora
from tau4.oop import PublisherChannel


class _Image:

    """"Liste" von TandemBox's.

    Jede TandemBox ist einem Out einer Control Unit zugeordnet.
    """

    def __init__( self):
        self.__tandemboxes = {}
        self.__lock = threading.Lock()
        return

    def add_value( self, vid, value):
        self.__tandemboxes[ vid] = _TandemBox( vid, value)

    def clone( self):
        this = self.__class__()
        this.__tandemboxes = copy.deepcopy( self.__tandemboxes)
        return this

    def switch( self):
        """Sender Box und Receiver Box "switchen".

        \warning    Der Sender muss zuvor flush() ausgführt haben!
        """
        with self.__lock:
            for tandembox in self.__tandemboxes.values():
                tandembox._switch_boxes_()

        return self

    def value( self, id_value, value=None):
        if value is None:
            return self.__tandemboxes[ id_value].value()

        self.__tandemboxes[ id_value].value( value)
        return self

    def _value_( self, id_value, value=None):
        """Nur für Testzwecke - siehe Testsuite.
        """
        if value is None:
            return self.__tandemboxes[ id_value]._senderbox_().value()

        self.__tandemboxes[ id_value].value( value)
        return self

    def value_add( self, vid, value, label="", dim=""):
        self.__tandemboxes[ vid] = _TandemBox( vid, value, label, dim)

    def vids( self):
        return self.__tandemboxes.keys()


class _ImageCollection:

    """Images aller Control Units.
    """

    def __init__( self, id_sending_control_unit):
        self.__id_sending_control_unit = id_sending_control_unit

        self.__images = {}
        self.__masterimage = _Image()
        return

    def __getitem__( self, rid):
        """Ermöglicht dict-like Zugriff auf Receiver Images.

        \param  rid
            Receiver Id
        """
        return self.__images[ rid]

    def image_add( self, id_receiving_control_unit):
        """Eine neue TandemBoxCollectionzu dieser TandemBoxCollections-Instanz hinzufügen.
        """
        self.__images[ id_receiving_control_unit] = self.__masterimage.clone()
        return self

    def add_value( self, vid, value):
        """Eine neue TandemBox zu allen TandemBoxCollection's dieser TandemBoxCollections-Instanz hinzufügen.
        """
        self.__masterimage.add_value( vid, value)

        for image in self.__images.values():
            image.add_value( vid, value)

        return self

    def flush( self):
        """Schreibt alle geschriebenen Werte in alle Sender Boxees aller Images.
        """
        for vid in self.__masterimage.vids():
            value = self.__masterimage._value_( vid)

            for image in self.__images.values():
                image.value( vid, value)

        return self

    def id( self):
        return self.__id_sending_control_unit

    def _switch_( self, dont_flush=False):
        """Nur für Testzwecke - der Sender darf nicht switchen!
        """
        if not dont_flush:
            self.flush()

        for image in self.__images.values():
            image.switch()

        return self

    def value( self, id_value, value=None):
        """Schreibt in die Sender Box, liest aus der Receiver Box.
        """
        q = self.__masterimage.value( id_value, value)
        if value is None:
            return q

        return self

    def _value_( self, id_value, value=None):
        """Schreibt in die Sender Box, liest aus der Sender Box.
        """
        q = self.__masterimage._value_( id_value, value)
        if value is None:
            return q

        return self

    def value_add( self, vid, value, label="", dim=""):
        """Eine neue TandemBox zu allen TandemBoxCollection's dieser TandemBoxCollections-Instanz hinzufügen.
        """
        self.__masterimage.value_add( vid, value, label, dim)

        for image in self.__images.values():
            image.value_add( vid, value, label, dim)

        return self


class _TandemBox:

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
        self.__senderbox = pandora.Box( value=value)
        self.__receiverbox = pandora.Box( value=value)
        self.__senderbox.label( label)
        self.__receiverbox.label( label)
        self.__senderbox.dim( dim)
        self.__receiverbox.dim( dim)

        self.__is_sender_dirty = False

        self.__lock = threading.Lock()
        self.__on_value_changed = PublisherChannel.Synch( self)
        return

    def reg_tau4s_on_modified( self, tau4s):
        self.__on_value_changed += tau4s
        return

    def _senderbox_( self):
        """Nur für Testzwecke - siehe Testsuite.
        """
        return self.__senderbox

    def switch_boxes( self):
        """Switch Box'es after locking them - \b DEPRECATED, do not use!
        """
        with self.__lock:
            return self._switch_boxes_()

    def _switch_boxes_( self):
        """Switch Box'es w/o locking them.
        """
        if self.__is_sender_dirty:
            self.__senderbox, self.__receiverbox = self.__receiverbox, self.__senderbox
            self.__on_value_changed()

        self.__is_sender_dirty = False
        return self

    def unreg_tau4s_on_modified( self, tau4s):
        self.__on_value_changed -= tau4s
        return

    def value( self, value=None):
        """Wert lesen/schreiben mit Zugrffsregelung (Lock).
        """
        with self.__lock:
            return self._value_( value)

    def _value_( self, value=None):
        """Wert lesen/schreiben ohne Zugrffsregelung (Lock).
        """
        if value is None:
            return self.__receiverbox.value()

        self.__senderbox.value( value)
        self.__is_sender_dirty = True
        return self

    def vid( self):
        """Value Id.
        """
        return self.__vid


_Images = {}
def Images( senderids=None):
    if senderids:
        _Images.clear()

        sids = set( senderids)
        for sid in sids:
            _Images[ sid] = _ImageCollection( sid)
            for rid in sids - set( (sid,)):
                _Images[ sid].image_add( rid)

    return _Images

