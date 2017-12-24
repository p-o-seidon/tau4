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

import abc
import collections

from tau4 import Object
from tau4.data import pandora


class Filter(Object, metaclass=abc.ABCMeta):

    def __init__( self, id, label, dim, p_Ts : pandora.BoxMonitored):
        super().__init__( id=id)

        self.__p_value = pandora.BoxMonitored( id=id, value=0.0, label=label, dim=dim)
        self.__p_Ts = p_Ts
        return

    @abc.abstractmethod
    def execute( self):
        pass

    def reg_tau4s_on_modified( self, tau4s):
        return self.__p_value.reg_tau4s_on_modified( tau4s)

    def ureg_tau4s_on_modified( self, tau4s):
        return self.__p_value.ureg_tau4s_on_modified( tau4s)

    def value( self, arg=None):
        if arg is None:
            return self.__p_value.value()

        self.__p_value.value( arg)
        return self


class FilterImpls:

    class SavitzkyGolayFilter(Filter):

        """"Das Savitzky-Golay-Filter ist ein mathematischer Glättungsfilter in der Signalverarbeitung.

        Er wurde erstmals 1964 von Abraham Savitzky und Marcel J. E. Golay beschrieben.
        Es leistet im Wesentlichen eine polynomiale Regression (k-ten Grades) über einer
        Serie von Werten (auf wenigstens k+1 Stützstellen, die als äquidistant behandelt
        werden), um einen geglätteten Wert für jeden Punkt zu bestimmen. Ein Vorteil
        des Savitzky-Golay-Filters ist, dass, anders als bei anderen Glättungsfiltern,
        Anteile von hohen Frequenzen nicht einfach abgeschnitten werden, sondern in die
        Berechnung mit einfließen. Dadurch zeigt der Filter ausgezeichnete Eigenschaften
        der Verteilung wie relative Maxima, Minima und Streuung zu erhalten, die von
        herkömmlichen Methoden wie der Bildung des gleitenden Mittelwerts gewöhnlich
        durch Abflachung oder Verschiebung verfälscht werden.

        Wie bereits erwähnt nutzt der Filter eine variable Fensterbreite und variable
        Glättungsfaktoren; diese Werte beeinflussen entscheidend die Wirkung des Filters.
        So kann der Filter durch Anpassung der Koeffizienten nicht nur wie eine
        Polynomialglättung sondern auch wie eine gleitende Mittelwertsbildung oder
        gar eine geglättete Ableitung wirken.

        Angewendet wird das Savitzky-Golay-Filter in der Spektroskopie. Die
        Erstveröffentlichung von Savitzky und Golay wird von einigen Autoren als
        eines der wichtigsten und meistzitierten Grundlagenveröffentlichungen im
        Bereich der computergestützten Numerik eingeschätzt. [https://de.wikipedia.org/wiki/Savitzky-Golay-Filter]"

        """

        def __init__( self, id, label, dimension):
            super().__init__( id, label, dimension)
            return

        def execute( self):
            return


    class AverageFilterRecursive(Filter):

        """Rekursive average filter.

        The average is defined by ::

                      n
                    -----
                  1  \
            m  = ---  )   x
              n   n  /     k
                    -----
                    k = 1

        Subtraction of the last average ::

                        n-1
                       -----
                     1  \
            m    =  ---  )   x
              n-1   n-1 /     k
                       -----
                       k = 1

        yields

                             x
                 n-1          n
            m  = --- m    + ---
             n    n   n-1    n

        or ::
                        m       x
                         n-1     n
            m  = m    - ---- + ---
             n    n-1    n      n

            respectively.

        Usage:
            \code{.py}
                f = AverageFilterRecursive( "filter", "Filter", "")
                while True:
                    f.value( YOUR VALUE GOES HERE)
                    f.execute()
                                                    # Calls all subscribers, if any.
                    print( "Mean = %.3f. " % f.value())
            \endcode
        """

        def __init__( self, id, label, dim):
            super().__init__( id, label, dim, None)

            self.__n = 0
            self.__value = 0.0
            super.value( 0)
            return

        def execute( self):
            self.__n += 1
            n = self.__n

            super().value( (n - 1)/n * super().value() + self.__value/n)
                                            # Calls all subscribers, if any.
            return self

        def value( self, arg=None):
            if arg is None:
                return super().value()

            self.__value = arg
            return self


class MovingAverageFilter(Filter):

    """Moving aveage filter.

    \_2DO
        StrategyChooser implementieren, der zur Laufzeit bestimmt, was schneller
        ist und entsprechend wählt.
    """

    def __init__( self, id, label, dim, depth):
        super().__init__( id, label, dim, None)

        self.__depth = depth
        self.__buffer = collections.deque( [ 0]*self.__depth, self.__depth)
        self.__value = 0.0

        if depth <= 10000:
            self._execute_ = self.execute_using_SUM_being_fast_for_small_depths

        else:
            self._execute_ = self.execute_working_recursively_being_fast_for_large_depths

        return

    def execute( self):
        return self._execute_()

    def execute_using_SUM_being_fast_for_small_depths( self):
        """Implementation by calculating a sum devided by the depth of the flter.
        """
        self.__buffer.rotate( -1)
        self.__buffer.append( self.__value)
        super().value( sum( self.__buffer)/self.__depth)
        return self

    def execute_working_recursively_being_fast_for_large_depths( self):
        """Implementation variant avoiding the calculation of a sum.
        """
        m = super().value()
        m -= self.__buffer[ 0]/self.__depth
        self.__buffer.rotate( -1)
        self.__buffer[ self.__depth-1] = self.__value
        m += self.__value/self.__depth
        super().value( m)
        return self

    def value( self, arg=None):
        if arg is None:
            return super().value()

        self.__value = arg
        return self

