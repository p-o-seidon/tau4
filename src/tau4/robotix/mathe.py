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

from __future__ import division


from math import atan2, radians, tan
import numpy as np

from tau4.mathe.linalg import Matrix3x3, R3D, R3DFromEuler, T3D, T3DFromEuler, T3Dnp, V3D # Hier nichts streichen, weil andere von hier importieren!


def ResultantHeadingAlpha( T_):
    """Berechnung eines Richtungsvektors als Resultierende aller Sensorvektoren.

    Die Richtung eines Sensorvektors ist bestimmt durch die Richtung des Sensors,
    die Länge durch den gemessenen Abstand zu einem Hindernis.
    """
    r = V3D( 0, 0, 0)
                                    # Resultierende
    for T in T_:
        r = r + T._P_()

    x, y = r.xy()
    if x == 0:
        if y == 0:
            return 0

        return radians( 90)

    alpha = atan2( y, x)
    return alpha
