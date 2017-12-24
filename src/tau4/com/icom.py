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


class iComId:

    def __init__( value):
        self.__value = value
        return

    def __repr__( self):
        return "% ( %s)" % (self.__class__.__name__, self.__value)

    def __str__( self):
        return str( self.__value)


class IComMessage(metaclass=abc.ABCMeta):

    def __init__( self):
        return


@Singleton
class IComManager:

    def __init__( self):
        return

    def channel_create( self, id_channel : iComId):
        return

    def message_create( self, id_channel : iComId, id_message : iComId):
        return

    def message_emit( self, id_channel, id_message, message : IComMessage):
        return

    def message_register_for( self, id_channel, id_message, callable):
        return

    def message_unregister_from( self, id_channel, id_message, callable):
        return


class IComMessageSender:

    def message_put( self, id_channel, id_message, message):
        return

    def messages_send( self):
        return


class IComMessageReceiver:

    def message_get( self):
        return

    def messages_receive( self):
        return


class IComRelais:

    def __init__( self):
        return


