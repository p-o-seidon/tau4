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

import logging

import abc
import random
import wx
from wx.adv import Joystick

from tau4.data import pandora
from tau4.sweng import PublisherChannel
from tau4.threads import Cycler


class _Hardware:

    def __init__( self, wx_joystick):
        self.__wx_joystick = wx_joystick
        return

    def is_available( self):
        is_available = self.__wx_joystick.GetManufacturerId() != 0
        is_available = True     # 2DO
        return is_available

    def is_button_pressed( self, index):
        return self.__wx_joystick.GetButtonState( index)

    def num_axes( self):
        return self.__wx_joystick.GetNumberAxes()

    def num_buttons( self):
        return self.__wx_joystick.GetNumberButtons()

    def num_sticks( self):
        #return self.__wx_joystick.GetNumberJoysticks()
        return 2 # Wie komme ich an dieses Datum?! GetNumberJoysticks() scheint die Anzahl an Controllern am PC zu liefern.

    def position_axis( self, axis):
        return self.__wx_joystick.GetPosition( axis)


class _GamepadItem(metaclass=abc.ABCMeta):

    def __init__( self, hardware, index):
        self.__hardware = hardware
        self.__index = index

        self.__data = None

        self._tau4p_on_modified = PublisherChannel.Synch( self)
        return

    def value( self, value=None):
        if value is None:
            return self.__data

        is_modified = value != self.__data
        self.__data = value
        if is_modified:
            self._tau4p_on_modified()

        return self

    @abc.abstractmethod
    def execute( self):
        pass

    def hardware( self): return self.__hardware
    def index( self): return self.__index


class _Button(_GamepadItem):

    def execute( self):
        self.value( self.hardware().is_button_pressed( self.index()))

    def is_pressed( self):
        return self.value()


class _JoystickFilter(pandora.plugins.Plugin):

    def __init__( self, id, print=False):
        super().__init__( id=id)

        self.__print = print
        return

    def process_value( self, value):
        value_org = value

        if value >= 0:
            if value < self._clipperRHS.min():
                value = 0
                value = self.value( int( value))
                if self.__print: print( "%d -> %d. " % (value_org, value))
                return value

            value = self._clipperRHS.process_value( value)
            value = self._mapperRHS.process_value( value)
            value = self.value( int( value))
            if self.__print: print( "%d -> %d. " % (value_org, value))
            return value

        if value > self._clipperLHS.max():
            value = 0
            self.value( int( value))
            if self.__print: print( "%d -> %d. " % (value_org, value))
            return value

        value = self._clipperLHS.process_value( value)
        value = self._mapperLHS.process_value( value)

        value += random.randint( -10, 10)
                                                # Damit der MD25 nicht glaubt, wir seien tot.
        value = self.value( int( value))
        if self.__print: print( "%d -> %d. " % (value_org, value))
        return value

    def is_clipping( self):
        return True


class _JoystickFilter4Omega(_JoystickFilter):

    def __init__( self):
        super().__init__( id=self.__class__.__name__, print=False)

        x1 = -32767; y1 = x1/4; x2 = -5000; y2 = 0
        self._clipperLHS = pandora.plugins.Clipper4Numbers( id=self.id()+".clipper.lhs", bounds=(x1, x2))
        self._mapperLHS = pandora.plugins.Mapper4Numbers( id=self.id()+".lhs", x1=x1, y1=y1, x2=x2, y2=y2)

        x1 = 5000; y1 = 0; x2 = 32767; y2 = x2/4
        self._clipperRHS = pandora.plugins.Clipper4Numbers( id=self.id()+".clipper.rhs", bounds=(x1, x2))
        self._mapperRHS = pandora.plugins.Mapper4Numbers( id=self.id()+".rhs", x1=x1, y1=y1, x2=x2, y2=y2)

        return


class _JoystickFilter4Speed(_JoystickFilter):

    def __init__( self):
        super().__init__( id=self.__class__.__name__, print=False)

        x1 = -32767; y1 = x1/2; x2 = -5000; y2 = 0
        self._clipperLHS = pandora.plugins.Clipper4Numbers( id=self.id()+".clipper.lhs", bounds=(x1, x2))
        self._mapperLHS = pandora.plugins.Mapper4Numbers( id=self.id()+".lhs", x1=x1, y1=y1, x2=x2, y2=y2)

        x1 = 5000; y1 = 0; x2 = 32767; y2 = x2/2
        self._clipperRHS = pandora.plugins.Clipper4Numbers( id=self.id()+".clipper.rhs", bounds=(x1, x2))
        self._mapperRHS = pandora.plugins.Mapper4Numbers( id=self.id()+".rhs", x1=x1, y1=y1, x2=x2, y2=y2)

        return


class _Stick(_GamepadItem):

    """Joystick on a gamepad.

    Assumes, that all sticks have the same position-value range running from -32767 to 32767.
    """

    def __init__( self, hardware, index, is_y_inverted, filter : pandora.plugins.Plugin):
        super().__init__( hardware, index)

        self.__factor_y = -1 if is_y_inverted else 1

        self.__p_x = pandora.Box( value=0, plugins=(filter,))
        self.__p_y = pandora.Box( value=0, plugins=(filter,))
        return

    def execute( self):
        x = self.hardware().position_axis( self.index() * 3)
        y = self.hardware().position_axis( self.index() * 3 + 1)
        x = self.__p_x.value( int( x))
        y = self.__p_y.value( int( y))
        self.value( (x, y))
        return

    def x( self):
        return self.value()[ 0]

    def y( self):
        return self.value()[ 1] * self.__factor_y

    def x_100( self):
        return self.x() / abs( self.x_max()) * 100

    def y_100( self):
        return self.y() / abs( self.y_max()) * 100

    def x_max( self):
        return 32767

    def y_max( self):
        return 32767


class _Stick4Omega(_Stick):

    def __init__( self, hardware, index, is_y_inverted):
        super().__init__( hardware, index, is_y_inverted, _JoystickFilter4Omega())
        return


class _Stick4Speed(_Stick):

    def __init__( self, hardware, index, is_y_inverted):
        super().__init__( hardware, index, is_y_inverted, _JoystickFilter4Speed())
        return



class Gamepad(Cycler):

    def __init__( self, index, is_y_inverted=True):
        super().__init__( cycletime=0.1, udata=None )

        self.__hardware = _Hardware( Joystick( (wx.JOYSTICK1, wx.JOYSTICK2)[ index]))

        self.__buttons = [ _Button( self._hardware_(), index) for index in range( self._hardware_().num_buttons())]
        lhs_stick_controlling_omega = _Stick4Omega( self._hardware_(), 0, is_y_inverted)
        rhs_stick_controlling_v = _Stick4Speed( self._hardware_(), 1, is_y_inverted)
        self.__sticks = [ lhs_stick_controlling_omega, rhs_stick_controlling_v]

        self.__is_modified = False
        self.__tau4p_on_modified = PublisherChannel.Synch( self)

        for item in self.buttons() + self.sticks():
            item._tau4p_on_modified += self._tau4s_on_gamepaditem_modified_

        return

    def _hardware_( self):
        return self.__hardware

    def buttons( self, index=None):
        if index is None:
            return self.__buttons

        return self.__buttons[ index]

    def reg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified += tau4s
        return

    def sticks( self, index=None):
        if index is None:
            return self.__sticks

        return self.__sticks[ index]

    def _tau4s_on_gamepaditem_modified_( self, tau4pc):
        self.__is_modified = True
        return

    def unreg_tau4s_on_modified( self, tau4s):
        self.__tau4p_on_modified -= tau4s
        return

    def _run_( self, udata):
        if self._hardware_().is_available():

            self.__is_modified = False

            for item in self.buttons() + self.sticks():
                item.execute()

            if self.__is_modified:
                self.__tau4p_on_modified()

        return



