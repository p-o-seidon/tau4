#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2017
#
#   This file is part of pandora.
#
#   pandora is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   pandora is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with pandora. If not, see <http://www.gnu.org/licenses/>.

import abc


class Formatter(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def alignH_centre( self): return False

    @abc.abstractmethod
    def alignH_left( self): return True

    @abc.abstractmethod
    def alignH_right( self): return False

    @abc.abstractmethod
    def as_str( self, value):
        pass


class FloatFormatter(Formatter):

    def __init__( self, format="%.03f"):
        self.__format = format
        return

    def alignH_centre( self): return False

    def alignH_left( self): return False

    def alignH_right( self): return True

    def as_str( self, value):
        return self.__format % value


class IntFormatter(Formatter):

    def __init__( self, format="%d"):
        self.__format = format
        return

    def alignH_centre( self): return False

    def alignH_left( self): return False

    def alignH_right( self): return True

    def as_str( self, value):
        return self.__format % value


class StrFormatter(Formatter):

    def __init__( self, format="%s"):
        self.__format = format
        return

    def alignH_centre( self): return True

    def alignH_left( self): return False

    def alignH_right( self): return False

    def as_str( self, value):
        return self.__format % value
