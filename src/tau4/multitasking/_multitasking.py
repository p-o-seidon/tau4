#!/usr/bin/env python3
#   -*- coding: utf8 -*- #
#
#
#   Copyright (C) by F. Geiger, 1998 - 2017
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

import sys
import time

from tau4 import Object


class _Stopwatch:

    """Eine Art Stoppuhr.
    """

    def __init__( self):
        self.__t = 0
        self.__dt = 0
        self.__dt_min = sys.maxsize
        self.__dt_max = 0
        self.__dt_sum = 0
        self.__was_used = False
        self.__num_calls = 0
        return

    def __enter__( self):
        self.__t = time.time()
        self.__was_used = True
        return

    def __exit__( self, *args):
        self.__dt = time.time() - self.__t
        self.__dt_min = min( self.__dt_min, self.__dt)
        self.__dt_max = max( self.__dt_max, self.__dt)
        self.__dt_sum += self.__dt
        self.__num_calls += 1
        return

    def is_valid( self):
        return self.__was_used

    def reset_statistics( self):
        self.__dt_min = sys.maxsize
        self.__dt_max = 0
        self.__dt_sum = 0
        self.__num_calls = 0
        return

    def time( self):
        return self.__dt

    def time_min( self):
        return self.__dt_min

    def time_max( self):
        return self.__dt_max

    def time_average( self):
        return self.__dt_sum / self.__num_calls


class _CycletimeMonitor(Object):

    def __init__( self, id, cycletime, tolerance:float=0.10, cycletime_for_reporting:float=5.0, reporter:callable=print):
        super().__init__( id=id)

        self.__cycletime = cycletime
        self.__tolerance = tolerance
        self.__cycletime_for_reporting = cycletime_for_reporting
        self.__reporter = reporter

        self.__cycletime_effective = cycletime
        self.__then = 0
        self.__cycletime_effective_min = sys.maxsize
        self.__cycletime_effective_max = 0
        self.__time_of_last_reporting = 0
        self.__num_exceeds = 0
        self.__num_calls = 0

        self.__stopwatch_usr = _Stopwatch()
        return

    def execute( self):
        """1-mal pro Zyklus ausführen!
        """
        now = time.time()

        self.__cycletime_effective = (now - self.__then) if self.__then else self.__cycletime
        self.__then = now

        self.__cycletime_effective_min = min( self.__cycletime_effective_min, self.__cycletime_effective)
        self.__cycletime_effective_max = max( self.__cycletime_effective_max, self.__cycletime_effective)

        self.__num_calls += 1
        if self.__cycletime_effective > self.__cycletime * (1 + self.__tolerance):
            self.__num_exceeds += 1

        if now - self.__time_of_last_reporting >= self.__cycletime_for_reporting:
            num_exceeds_100 = self.__num_exceeds / self.__num_calls * 100
            s = "\n%s:\n\t%.1f %% cycletime exceeds discovered. Effective cycletimes lie in between (%.3f, %.3f). " \
                % (self.id(), num_exceeds_100, self.__cycletime_effective_min, self.__cycletime_effective_max)
            self.__reporter( s)

            if self.__stopwatch_usr.is_valid():
                s = "\t%.3f ms average time (min: %.3f ms, max: %.3f ms) consumed by user (method _run_()). " \
                    % ( \
                        self.__stopwatch_usr.time_average()*1000,
                        self.__stopwatch_usr.time_min()*1000,
                        self.__stopwatch_usr.time_max()*1000
                    )
                self.__reporter( s)

                self.__stopwatch_usr.reset_statistics()

            self.__time_of_last_reporting = now
            self.__cycletime_effective_min = sys.maxsize
            self.__cycletime_effective_max = 0

        return

    def stopwatch_user( self):
        return self.__stopwatch_usr