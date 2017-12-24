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
from tau4 import datalogging

from . import filters_py as py
import pyximport; pyximport.install()
#from . import filters_cy as cy
from tau4.dsp import filters_cy as cy

try:
#    if not tau4._settings._TAU4_TAU4DSP_CY:
#        text = "Use of py code is forced in %s!" % __file__
#        tau4logging.SysEventLog().log_warning( text, __file__)
#        raise ImportError( text)

    text = "Cython code version is used."
#    from tau4.dsp.filters_cy import Filter4DummyUse
    from tau4.dsp.filters_cy import MovingAverageFilter
#    from tau4.dsp.filters_cy import MovingAverageFilterExponentiallyWeighted
#    from tau4.dsp.filters_cy import MovingAverageFilterSlow
#    from tau4.dsp.filters_py import NoiseSpikeFilter # 2DO
#    from tau4.dsp.filters_py import NoiseSpikeFilter2 # 2DO

    datalogging.SysEventLog().log_info( text, __file__)

except ImportError as e:
    text = "Pure Python code version is used."
    _Logger.error("%s. %s ", e, text)
#    from tau4.dsp.filters_py import Filter4DummyUse
    from tau4.dsp.filters_py import MovingAverageFilter
#    from tau4.dsp.filters_py import MovingAverageFilterExponentiallyWeighted
#    from tau4.dsp.filters_py import MovingAverageFilterSlow
#    from tau4.dsp.filters_py import NoiseSpikeFilter
#    from tau4.dsp.filters_py import NoiseSpikeFilter2

    datalogging.SysEventLog().log_warning( text, __file__)

