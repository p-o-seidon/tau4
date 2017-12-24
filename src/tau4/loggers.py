#   -*- coding: utf8 -*-
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
#
################################################################################


import argparse
import logging
import sys

from tau4 import DictWithUniqueKeys
from tau4.oop import Singleton


getLogger = logging.getLogger


class _LoggerSetup:

    def __init__( self, name, is_enabled, logginglevel):
        self._name = name
        self._is_enabled = is_enabled
        self._logginglevel = logginglevel
        return


class Pool(metaclass=Singleton):

    def __init__( self):
        self.__logginglevels = { \
            None: logging.INFO,
            "": logging.INFO,
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }

        self.__loggersetups = DictWithUniqueKeys()
        self.__loggers = DictWithUniqueKeys()

        ### Root Logger zurechtbiegen
        #
        logging.basicConfig()
        root = logging.getLogger()
        root.handlers[ 0].setLevel( logging.CRITICAL)
                                        # Auf die Console nur Exceptions
        ### Main Handler
        #
        self._logger_add_( "main")
        return

    def logger( self, loggername="main", add_if_not_existent=True):
        if not self._logger_exists_( loggername) and add_if_not_existent:
            self._logger_add_( loggername)

        return self.__loggers[ loggername]

    def logger_add( self, loggername):
        self._logger_add_( loggername)
        return self

    def _logger_add_( self, loggername, format_is_ascii=False):
        self.__loggersetups[ loggername] =  _LoggerSetup( loggername, True, self.__logginglevels[ "critical"])
        logger = getLogger( loggername)

        logger = logging.getLogger( loggername)
        logger.propagate = True
                                        # Die SUb-Logger loggen alle auch
                                        #   in den Root Logger
        if format_is_ascii:
            handler = logging.handlers.RotatingFileHandler( "./" + loggername + ".log", "a", 10000000, 10)
            formatter = logging.Formatter( "%(asctime)s - %(process)10d - %(thread)20d - %(levelname)10s %(message)s")

        else:
            handler = logging.handlers.RotatingFileHandler( "./" + loggername + ".log.csv", "a", 10000000, 10)
            formatter = logging.Formatter( "%(asctime)s\t%(process)d\t%(thread)d\t%(levelname)s\t%(message)s")

        handler.setFormatter( formatter)
        logger.addHandler( handler)
        logger.setLevel( self.__loggersetups[ loggername]._logginglevel)

        logger.critical( "***** Logger '%s' created. *****" % loggername)

        self.__loggers[ loggername] = logger

        return

    def _logger_exists_( self, loggername):
        return loggername in self.__loggers

    def logginglevel_to_DEBUG( self, loggername="main"):
        self.logginglevel_to( loggername, "debug")
        return self

    def logginglevel_to_INFO( self, loggername="main"):
        self.logginglevel_to( loggername, "info")
        return self

    def logginglevel_to_WARNING( self, loggername="main"):
        self.logginglevel_to( loggername, "warning")
        return self

    def logginglevel_to_ERROR( self, loggername="main"):
        self.logginglevel_to( loggername, "warning")
        return self

    def logginglevel_to_CRITICAL( self, loggername="main"):
        self.logginglevel_to( loggername, "critical")
        return self

    def logginglevel_to( self, loggername, logginglevelname):
        self.__loggers[ loggername].setLevel( self.__logginglevels[ logginglevelname])
        return self

