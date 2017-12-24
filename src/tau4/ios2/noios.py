#   -*- coding: utf8 -*- #
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2015
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

import random

from tau4 import Id
from tau4 import ios2
from tau4.ios2._common import AInp, AOut, DInp, DOut


class Board(ios2.IOBoard):

    def __init__( self, usrid):
        super().__init__( usrid)

    def ainp_value( self, *args): pass
    def aout_value( self, *args): pass

    def dinp_value( self, *args): pass
    def dout_value( self, *args): pass


class AInpNIO(AInp):

    def __init__( self, id_sys: Id, label: str):
        super().__init__( id_sys, label)
        return

    def execute( self):
        self.p_box().value( random.randint(1, 1000)/1000)
        return self

    def port2box( self):
        return


class AOutNIO(AOut):

    def __init__( self, id_sys: Id):
        super().__init__( id)
        return

    def box2port( self):
        return

    def execute( self):
        return self


class DInpNIO(DInp):

    def __init__( self, id_sys: Id, is_hi_active, label):
        super().__init__( "noios", id, is_hi_active, label)
        return

    def execute( self):
        return self

    def port2box( self):
        return


class DOutNIO(DOut):

    def __init__( self, id_sys: Id, is_hi_active, label):
        super().__init__( id, is_hi_active, label)
        return

    def box2port( self):
        return

    def execute( self):
        return self
