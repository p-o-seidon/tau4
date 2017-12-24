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

import logging; _Logger = logging.getLogger()
import sys

import tau4

import tau4.mathe.linalg_py
                                # Falls im Client-Code explizit die PY-Version
                                #   verwendet werden soll.
try:
    import pyximport; pyximport.install()
    import tau4.mathe.linalg_cy
                                    # Falls im Client-Code explizit die CY-Version
                                    #   verwendet werden soll.
    text = "Cython code version is used."
    from tau4.mathe.linalg_cy import Matrix3x3
    from tau4.mathe.linalg_cy import R3D
    from tau4.mathe.linalg_cy import R3DFromEuler
    from tau4.mathe.linalg_cy import R3DFromVectors
    from tau4.mathe.linalg_cy import T3D
    from tau4.mathe.linalg_cy import T3DFromEuler
    from tau4.mathe.linalg_py import T3Dnp
    from tau4.mathe.linalg_cy import V3D

except ImportError as e:
    text = "Pure Python code version is used."
    _Logger.error( "%s. %s ", e, text)
    from tau4.mathe.linalg_py import Matrix3x3
    from tau4.mathe.linalg_py import R3D
    from tau4.mathe.linalg_py import T3D
    from tau4.mathe.linalg_py import T3Dnp
    from tau4.mathe.linalg_py import V3D


