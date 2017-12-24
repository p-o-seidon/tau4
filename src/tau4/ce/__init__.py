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
#
################################################################################

import abc
from tau4 import Id
from tau4.ce._common import _AlgorithmDigital
from tau4.ce import eulerbw
from tau4.oop import overrides
from tau4.data import pandora


EulerBw4DT1 = eulerbw.DT1
                                # Für Rückwärtskomp.
EulerBw4gPIDT1p = eulerbw.gPIDT1p
                                # Für Rückwärtskomp.
EulerBw4I = eulerbw.I
                                # Für Rückwärtskomp.
EulerBw4P = eulerbw.P
                                # Für Rückwärtskomp.
Euler4Lead = eulerbw.Lead
                                # Für Rückwärtskomp.
EulerBw4PDT1 = eulerbw.PDT1
                                # Für Rückwärtskomp.
EulerBw4PIDT1 = eulerbw.PIDT1
                                # Für Rückwärtskomp.
EulerBw4PIDT1p = eulerbw.PIDT1p
                                # Für Rückwärtskomp.
EulerBw4PT1 = eulerbw.PT1
                                # Für Rückwärtskomp.
EulerBw4PI = eulerbw.PI
                                # Für Rückwärtskomp.
EulerBw4PT1PT1 = eulerbw.PT1PT1
                                # Für Rückwärtskomp.
