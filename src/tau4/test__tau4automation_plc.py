#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by p.oseidon@datec.at, 1998 - 2016
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


from __future__ import division

import logging; _Logger = logging.getLogger()
import socket

import tau4
from tau4 import ThisName
from tau4.datalogging import UsrEventLog
import time
import unittest

from tau4.automation.plc import OperationMode


class _TESTCASE__OperationMode(unittest.TestCase):

    def test__basix( self):
        """
        """
        print()

        om = OperationMode()
        print( om.name())
        self.assertTrue( om.is_OFF())

        om.button_START( True)
        om.sm().execute()   # Normally executed by the PLC
        print( om.name())
        self.assertTrue( om.is_OFF())

        om.switch_ON( True)
        om.sm().execute()   # Normally executed by the PLC
        print( om.name())
        self.assertTrue( om.is_ON())

        om.switch_AUTO( False)
        om.sm().execute()   # Normally executed by the PLC
        print( om.name())
        self.assertTrue( om.is_MANU())

        om.switch_AUTO( True)
        om.sm().execute()   # Normally executed by the PLC
        print( om.name())
        self.assertTrue( om.is_ON())
        om.sm().execute()   # Normally executed by the PLC
        print( om.name())
        self.assertTrue( om.is_AUTO())

        return


_Testsuite = unittest.makeSuite( _TESTCASE__OperationMode)


class _TESTCASE__(unittest.TestCase):

    def test( self):
        """
        """
        print()
        return


_Testsuite.addTest( unittest.makeSuite( _TESTCASE__))


def _lab_():
    return


def _Test_():
    unittest.TextTestRunner( verbosity=2).run( _Testsuite)


if __name__ == '__main__':
    _Test_()
    _lab_()
    input( u"Press any key to exit...")



