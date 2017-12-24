#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2017
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


import abc
from tau4.sweng import PublisherChannel


class _PublishersChannelDict(dict):

    def __missing__( self, key):
        return _PublisherChannel()


class _PublisherChannel(PublisherChannel.Synch):

    def __init__( self):
        super().__init__( None)
        return

    def __call__( self, *args, **kwargs):
        """Ausführen aller registrierter Subscribers.

        **Unterschied zu PublisherChannel.Synch**:
            Der PublisherChannel wird im Publisher Call nicht mitübergeben!
        """
        ss = self.subscribers( copy=self.is_safe_mode())
        for s in ss:
            s( *args, **kwargs)

        return self


class Message(metaclass=abc.ABCMeta):

    """Message, die "weiß", an wen sie zu publishen ist.

    Alleine ist diese Klasse noch nicht verwendbar, es müssen App-Klassen davon
    abgeleitet werden.

    Usage:
        Siehe file:/home/fgeiger/projects/tau4/src/py3/dox/_tau4com.odt
    """

    __PublisherChannels = _PublishersChannelDict()

    @classmethod
    def RegisterSubscriber( klass, subscriber):
        Message.__PublisherChannels[ klass.__name__] += subscriber
        return

    @classmethod
    def UnRegisterSubscriber( klass, subscriber):
        Message.__PublisherChannels[ klass.__name__] -= subscriber
        return

    @abc.abstractmethod
    def __init__( self):
        pass

    def publish( self):
        """Publish der Message.

        Den Subscribern wird (nur) die Message übergeben.
        """
        self.__PublisherChannels[ self.__class__.__name__]( self)
        return
