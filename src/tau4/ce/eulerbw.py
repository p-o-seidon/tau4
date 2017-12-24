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

import math

from tau4 import Id
from tau4.ce._common import _AlgorithmDigital
from tau4.data import pandora
from tau4.oop import overrides


class GeneralController2ndOrder(_AlgorithmDigital):

    """Allgemeiner Regler der Ordnung 2 in allgemeiner Form.
    """

    def __init__( self, id, K, b2, b1, b0, a2, a1, a0, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)
        self.__K = K
        self.__b_ = b0, b1, b2
        self.__a_ = a0, a1, a2

        self.__d_ = [ 0] * len( self.__b_)
        self.__c_ = [ 0] * len( self.__a_)

        self.__e_ = [0, 0, 0]
        self.__u_ = [0, 0, 0]

        self.recal_coeffs()
        return

    @overrides( _AlgorithmDigital)
    def configure( self, Ts):
        return

    def _eL_( self):
        return self.__e_

    @overrides( _AlgorithmDigital)
    def execute( self):
        """Ausführung des Algorithmus.

        Der Shift der Werte von k - i nach k - i - 1 erfolgt am Beginn der Methode
        und nicht an deren Ende, damit ein erneutes Berechnen mit einem
        2. Algorithmus (s. _u_by_2nd_algorithm_() in Subclasses) möglich wird.
        """
        K = self.__K
        d = self.__d_
        c = self.__c_

        e = self.__e_
        u = self.__u_

        e[ -2] = e[ -1]; e[ -1] = e[ 0]
        u[ -2] = u[ -1]; u[ -1] = u[ 0]

        e[ 0] = self.p_e().value()

        u[ 0] = 1/c[ 0]*(-c[ 1]*u[ -1] - c[ 2]*u[ -2] + K*( d[ 0]*e[ 0] + d[ 1]*e[ -1] + d[ 2]*e[ -2]))

        self.p_u().value( u[ 0])

        return

    @overrides( _AlgorithmDigital)
    def info( self):
        return self.name()

    @overrides( _AlgorithmDigital)
    def name( self):
        return "PDT1"

    def recal_coeffs( self):
        """Koeffizienten neu berechnen.
        """
        b = self.__b_
        a = self.__a_
        d = self.__d_
        c = self.__c_
        Ts = self.p_Ts().value()

        d[ 0] = b[ 0] + b[ 1]/Ts + b[ 2]/Ts/Ts
        d[ 1] = -b[ 1]/Ts - 2*b[ 2]/Ts/Ts
        d[ 2] = b[ 2]/Ts/Ts

        c[ 0] = a[ 0] + a[ 1]/Ts + a[ 2]/Ts/Ts
        c[ 1] = -a[ 1]/Ts - 2*a[ 2]/Ts/Ts
        c[ 2] = a[ 2]/Ts/Ts
        return

    @overrides( _AlgorithmDigital)
    def reset( self):
        """Stellgröße "löschen" und Koeffizienten neu berechnen.
        """
        self.p_u().value( 0)
        self.recal_coeffs()
        return

    def _uL_( self):
        return self.__u_


class DT1(_AlgorithmDigital):

    """Algorithmus *Euler rückwärts* für DT1-Regler (realer D-Regler).

    \param  id          Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    \param  p_Kd:       Reglerverstärkung.
    \param  p_alpha:    **2DO**
    \param  p_Ts:       Abstastzeit.
    \param  p_e:        Regeldifferenz.
    \param  p_u:        Stellgröße. Muss eine pandora.Box sein, damit eine Regelung für Bereichsüberschreitungen möglich ist.

    Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
    .execute() neu berechnet werden.

    \_2DO
        **Ändern:**
        Die Koeffizienten sollen nicht bei jedem .execute() berechnet werden,
        das ist neu Aufgabe von .configure().

    No, How?

        \f[
            DT1(s) = \frac {K_D s}{1 + \tau_D s} = K_P \frac {T_D s}{1 + \alpha T_D s},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        \f]

        \f[
            DT1(z) = K_P \frac {T_D' (1 - z{⁻1})}{(1 + \alpha T_D') - \alpha T_D' z^{-1}},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        \f]

        \f[
            u_k = \frac 1 {1 + \alpha K_D'} \left[ \alpha K_D' u_{k-1} + K_D'(e_k - e_{k-1}\right],\ \ \ K_D' = \frac {K_D}{T_s},\ \ \ \alpha = 0...1
        \f]
    """

    def __init__( self, *, id, p_Kd, p_alpha, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_Kd = p_Kd
        self.__p_alpha = p_alpha

        self.__p_e = p_e
        self.__p_u = p_u

        self.__e_ = [ 0, 0]
        self.__u_ = [ 0, 0]
        return

    @overrides( _AlgorithmDigital)
    def configure( self, p_Ts):
        self._recal_algorithms_()
        return

    def execute( self):
        """Regelgesetz ausführen.

        \f[
            DT1(s) = \frac {K_D s}{1 + \tau_D s} = K_P \frac {T_D s}{1 + \alpha T_D s},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        \f]

        \f[
            DT1(z) = K_P \frac {T_D' (1 - z{⁻1})}{(1 + \alpha T_D') - \alpha T_D' z^{-1}},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        \f]

        \f[
            u_k = \frac 1 {1 + \alpha K_D'} \left[ \alpha K_D' u_{k-1} + K_D'(e_k - e_{k-1}\right],\ \ \ K_D' = \frac {K_D}{T_s},\ \ \ \alpha = 0...1
        \f]
        """
        ### Abkürzungen
        #
        e_ = self.__e_
        u_ = self.__u_
        Kd = self.__p_Kd.value()
        alpha = self.__p_alpha.value()
        Ts = self.p_Ts().value()

        ### Werte aus letztem Schritt übernehmen
        #
        e_[-1] = e_[0]
        u_[-1] = u_[0]

        ### Input lesen
        #
        e_[0] = self.__p_e.value()

        ### Algorithmus ausführen
        #
        Kds = Kd/Ts
        u_[0] = alpha * Kds * u_[-1] + Kds * (e_[0] - e_[-1])
        u_[0] /= (1 + alpha * Kds)

        u = u_[0]

        ### Output schreiben
        #
        self.__p_u.value( u)

        return

    def info( self):
        return "%s (%s): Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(),
                   self.__class__.__name__,
                   self.__p_Kd.value(),
                   self.__p_alpha.value(),
                   self.p_Ts().value()
               )

    def name( self):
        return u"DT1"

    def _recal_algorithms_( self):
        """Koeffizienten neu berechnen.

        Algorithmus ist nicht aufwendig, wird daher in execute() gemacht.
        """
        return

    def reset( self):
        self.__p_e.value( 0.0)
        self.__p_u.value( 0.0)
        self.__e_ = [ 0, 0]
        self.__u_ = [ 0, 0]
        return


class gPIDT1p(_AlgorithmDigital):

    """PID allgemein, real, Euler rückwärts, 3 Übertragungsfunktionen PARALLEL, Windup Prevention.

    \param  id:        Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    \param  p_Kr:      Gesamtverstärkung.
    \param  p_b0:      Polynomkoeffizient.
    \param  p_b1:      Polynomkoeffizient.
    \param  p_b2:      Polynomkoeffizient.
    \param  p_alpha:   0...1
    \param  p_Ts:      Abstastzeit.

    Art der Windup-Prävention:
        Abschalten des Integrators.

    Hier lässt sich das Windup des Integrators verhindern, indem der Integrator
    auf Pause geschaltet wird, wenn die Summe der drei Einzelsignale die
    Stellgrenzen überschreiten.

    \note

        Es gibt keine Methode, die es ermöglicht, aus Zeitkonstanten die
        Polynomkoeffizienten zu berechnen, das muss die App selber machen.
        Da Algorithmen über grafische Frontends programmiert werden und dafür
        Modelle geschrieben werden müssen, ist das in einem Modell zu machen.
        Modelle müssen sowieso ausreichend viel über die Datenstrukturen wissen,
        die sie verwalten.

    Berechnung Polynomkoeffizienten:
        Da das Zählerpolynom konjugiert-komplexe Lösungen hat, ist die Berechnung
        aus Zeitkonstanten nicht möglich. Was man aber angeben kann, sind genau
        diese konjugiert komplexen Pole :math:`s = -\sigma \pm j\omega_d`.

        Es gilt dann:

        \f[
            K_R (1 + b_1 s + b_2 s^2) = \omega_0^2 \left( 1 + \frac {2\sigma}{\omega_0^2} s + \frac 1 {\omega_0^2} s^2 \right)
        \f]

        mit

        \f[
            \omega_0^2 = \sigma^2 + \omega_d^2
        \f]

        Der Standard-PIDT1-Regler ist so definiert:

        \f[
            PIDT_1(s) = K_I \frac {1 + \left(\tau_D + \frac {K_P}{K_I}\right) s + \frac {K_P}{K_I} \left(\tau_D + \frac {K_D}{K_P}\right) s^2}{s \left(1 + \tau_D s\right)}
        \f]

        Damit gilt also:

        \f[
            K_R = K_I

            b_1 = \tau_D + \frac {K_P}{K_I}

            b_2 = \frac {K_P}{K_I} \left(\tau_D + \frac {K_D}{K_P}\right)
        \f]


    \note
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.
    """

    def __init__( self, *, id, p_Kr, p_b0, p_b1, p_b2, p_alpha, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_Kr = p_Kr
        self.__p_b0 = p_b0
        self.__p_b1 = p_b1
        self.__p_b2 = p_b2
        self.__p_alpha = p_alpha

        self.__p_e = p_e
        self.__p_u = p_u

        p_uPT1 = pandora.Box( value=.0)
        p_uDT1 = pandora.Box( value=0.0)
        p_uI = pandora.Box( value=0.0)

        self.__algorithmPT1 = PT1( id=id + ": PT1", p_K1=0, p_T1=0, p_Ts=p_Ts, p_e=p_e, p_u=p_uPT1)
        self.__algorithmDT1 = DT1( id=id + ": DT1", p_Kd=0, p_alpha=0, p_Ts=p_Ts, p_e=p_e, p_u=p_uDT1)
        self.__algorithmI = I( id=id + ": I", p_Ki=0, p_Ts=p_Ts, p_e=p_e, p_u=p_uDT1)

        p_u.reg_tau4p_on_violated( lambda *arg: self.__algorithmI.pause())
        p_u.reg_tau4p_on_unviolated( lambda *arg: self.__algorithmI.resume())
                                        # Kann das der Aktuator? Wenn nicht,
                                        #   müssen wir den Integrierer pausieren
                                        #   lassen, d.h. er bleibt einfach "stehen"
                                        #   (schaltet sich nicht aus).
                                        #   Das funktioniert allerdings nur dann
                                        #   richtig, wenn der Regler die
                                        #   Werte aus dem Aufruf k-1 zu Beginn
                                        #   von execute() übernimmt und nicht
                                        #   schon am Ende von execute().
        self.__p_Kr.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__p_b0.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__p_b1.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__p_b2.reg_tau4p_on_modified( lambda *args: self.configure())

        self.configure()
        return

    def configure( self, p_Ts):
        self._recal_algorithms_()
        return

    def p_Kp( self):
        """Zugriff auf p_Kp.

        Delegiert an EulerBw4PT1.
        """
        return self.__algorithmPT1.p_K1()

    def p_Ki( self):
        """Zugriff auf p_Ki.

        Delegiert an EulerBw4I.
        """
        return self.__algorithmI.p_Ki()

    def p_Kd( self):
        return self.__algorithmDT1.p_Kd()

    def p_alpha( self):
        return self.__algorithmDT1.p_alpha()

    def p_Kr( self):
        return self.__p_Kr

    def p_b0( self):
        return self.__p_b0

    def p_b1( self):
        return self.__p_b1

    def p_b2( self):
        return self.__p_b2


    def execute( self):
        """Berechnung der Differenzengleichung.

        Die Regeldifferenz steht im FlexEntity p_e, der dem Ctor übergeben wird
        und dort den beteiligten Algoorithmen. Es ist aso nicht notwendig, den
        Algorithmen diesen Wert zu übergeben - sie haben ihn in dem Moment,
        in dem er geschrieben wird.
        """
        ##  Alle Elemente ausführen
        #
        self.__algorithmPT1.execute()
        self.__algorithmDT1.execute()
        self.__algorithmI.execute()

        ##  Ausgangssignal = Summe der einzelnen Ausgangssignale
        #
        p_uDT1 = self.__algorithmPT1.p_u()
        p_uI = self.__algorithmPT1.p_u()
        p_uPT1 = self.__algorithmPT1.p_u()
        p_u.value( p_uPT1.value() + p_uDT1.value() + p_uI.value())
                                        # Löst eine Limit Violation aus. Dazu
                                        #   muss es sich bei p_u aber auch um
                                        #   eine FlexVarbl handeln. Siehe Ctor.
        return

    def info( self):
        """Info über Algorithmus, z.B. zur Anzeige auf GUIs.

        Hier sollte nicht nur der Name sondern auch eine nähere Beschreibung
        zum Algorithmus zu finden sein.
        """
        return "%s (%s): Kp = %.3f; Ki = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(),
                   self.__class__.__name__,
                   self.__p_Kp.value(),
                   self.__p_Ki.value(),
                   self.__p_Kd.value(),
                   self.__p_alpha.value(),
                   self.p_Ts().value()
               )

    def name( self):
        return "gPIDT1 (parallel form)"

    def reset( self):
        self.__p_e.value( 0.0)
        self.__p_u.value( 0.0)

        self.__algorithmPT1.reset()
        self.__algorithmI.reset()
        self.__algorithmDT1.reset()
        return

    def _recal_algorithms_( self):
        b0 = self.__p_b0
        b1 = self.__p_b1
        b2 = self.__p_b2
        Kr = self.__p_Kr
        Kd = Kr * b2
        Ki = Kr * b0
        alpha = self.__alpha
        tau = alpha * b2
        K1 = Kr * (b1 - b0 * tau)

        if K1 < 0:
            raise ValueError( "(tau == %.3f) >= (b1/b0 == %.3f), i.e. (alpha == %.3f) <= ((b1/b0)/b2 == %.3f)" % (tau, b1/b0, alpha, b1/b0/b2))

        self.__algorithmPT1.K1( K1).T1( tau)
        self.__algorithmDT1.Kd( Kd).alpha( alpha)
        self.__algorithmI.Ki( Ki)

        return


class I(_AlgorithmDigital):

    """Integrator.

    Provides windup protection!

    Parameters:
    :param              id:     Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    :param  FlexVarbl   p_Ki:  Integral constant.
    :param  FlexVarbl   p_Ts:  Abstastzeit.

    Art der Windup-Prävention:
        Abschalten des Integrators.

    NOTE:
        Die Anti-Windup-Maßnahme funktioniert nur bei kleinen Abtastzeiten wirklich befriedigend.
        Denn wenn der Regler auf Pause geschaltet wird, hat er das Stellgrößen-Limit
        schon überschritten und hat sich u. U. schon ordentlich aufgezogen.

    NOTE:
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.
    """

    def __init__( self, *, id, p_Ki, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_Ki = p_Ki

        self.__e_ = [ 0, 0]
        self.__u_ = [ 0, 0]

        self.__e_last_known_good_ = [ 0, 0]
        self.__u_last_known_good_ = [ 0, 0]

        self.__e_bak_ = [ 0, 0]
        self.__u_bak_ = [ 0, 0]

        self.__is_windup_protection_active = False
        self.__is_windup_protection_available = True
        self.__is_paused = False

        return

    @overrides( _AlgorithmDigital)
    def configure( self, p_Ts):
        return

    @overrides( _AlgorithmDigital)
    def execute( self):
        """Execute the algorithm.
        """
        ##  Sind wir in der Sättigung?
        #
        if self.__is_windup_protection_available:
            if self.__is_paused:
                self.is_windup_protection_active( True)
                return

            self.is_windup_protection_active( False)

        ##  Some abbreviations
        #
        Ki, Ts = self.__p_Ki.value(), self.p_Ts().value()

        ##  Some pointers
        #
        e_ = self.__e_
        u_ = self.__u_

        ##  Zuletzt als gut befundene Werte sichern
        #
        self.__e_last_known_good_[:] = self.__e_
        self.__u_last_known_good_[:] = self.__u_

        self.__e_bak_[:] = self.__e_
        self.__u_bak_[:] = self.__u_

        ##  Werte vom letzten Schritt
        #
        e_[-1] = e_[0]
        u_[-1] = u_[0]

        ##  Erst jetzt dürfen wir das Eingangssignal lesen
        #
        e_[0] = self.p_e().value()

        ##  Ausführen des eigentlichen Algorithmus
        #
        u_[0] = u_[-1] + Ki*Ts*e_[0]

        u = u_[0]

        ##  Write to the plant
        #
        self.p_u().value( u)

        return True

    def is_windup_protection_active( self, arg=None):
        """
        """
        if arg is None:
            return self.__is_windup_protection_active

        self.__is_windup_protection_active = arg
        return self

    def is_windup_protection_available( self):
        """
        """
        return self.__is_windup_protection_available

    def p_Ki( self, arg=None):
        """Integrationsbeiwert.
        """
        return self.__p_Ki

    def info( self):
        return self.name()

    def name( self):
        """
        """
        return "I (Euler Bw)"

    def pause( self):
        """Anti-Windup-Erkennung schaltet uns auf Pause, weil wir die Stellgröße in die Sättigung getrieben haben.

        Wir machen daher den letzten Schritt rückgängig::

            self.__e_[:] = self.__e_last_known_good_
            self.__u_[:] = self.__u_last_known_good_
        """
        if not self.__is_paused:
            self.__is_paused = True
#            self.__e_[:] = self.__e_last_known_good_
#            self.__u_[:] = self.__u_last_known_good_
            self.p_u().value( self.__u_[0])

        return

    def resume( self):
        if self.__is_paused:
            self.__is_paused = False

        return

    @overrides(_AlgorithmDigital)
    def reset( self):
        """
        """
        self.p_e().value( 0)
        self.p_u().value( 0)
        self.__e_ = [0, 0]
        self.__u_ = [0, 0]
        return


class Lead(GeneralController2ndOrder):

    """Lead-Regler als Subclass des allgemeien Reglers zweiter Ordnung: \f$ R(s) = K \frac {1 + T s}{1 + \alpha T s}, \ \ \ \alpha < 1 \f$

    Differenzengleichung **PDT1 By Euler Backwards (Variante Lead-Lag)** für
    Implementation auf einem Rechner.

    Laplace-Transformierte

        \f[
            R(s) = K \frac {1 + T s}{1 + \alpha T s}, \ \ \ \alpha < 1
        \f]

    """

    def __init__( self, id, p_K, p_T, p_alpha, p_Ts, p_e, p_u):
        super().__init__( id, K=p_K.value(), b2=0, b1=p_T.value(), b0=1, a2=0, a1=p_alpha.value()*p_T.value(), a0=1, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__K = p_K.value()
        self.__T = p_T.value()
        self.__alpha = p_alpha.value()
        return

    def _u_by_2nd_algorithm_( self):
        """Nur für Testzwecke.
        """
        K = self.__K
        T = self.__T
        alpha = self.__alpha
        Ts = self.p_Ts().value()

        e = self._eL_()
        u = self._uL_()

        return 1/(1 + alpha*T/Ts)*(alpha*T/Ts*u[ -1] + K*((1 + T/Ts)*e[ 0] - T/Ts*e[ -1]))



class P(_AlgorithmDigital):

    """P-Regelalgorithmus.

    :param  pandora.Box p_Kp:   Proportionalverstärkung
    :param  pandora.Box p_Ts:   Abtastzeit (wird hier nicht gebraucht).
    :param  pandora.Box p_e:    für Eingangssignal *Regelabweichung*.
    :param  pandora.Box p_u:    für Ausgangssignal *Stellgröße*.
    """

    def __init__( self, *, id, p_Kp : pandora.Box, p_Ts : pandora.Box, p_e : pandora.Box, p_u : pandora.Box):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_e = p_e; assert isinstance( self.__p_e, pandora.Box)
        self.__p_Kp = p_Kp; assert isinstance( self.__p_Kp, pandora.Box)
        return

    def configure( self, p_Ts):
        """Ausführung einer Neukonfiguration.

        Ausführung mindestens bei Ausführung des Ctor von :py:class:`SISOController`.

        \note
            Man könnte sich also die Übergabe von p_Ts an diesen Ctor sparen!
        """
        assert self.p_Ts() == p_Ts
        return

    def execute( self):
        """Execute the algorithm.
        """
        self.p_u().value( self.__p_Kp.value() * self.p_e().value())
        return True

    def p_Kp( self):
        """Reglerverstärkung
        """
        return self.__p_Kp

    def is_windup_protection_active( self):
        """
        """
        return False

    def info( self):
        return "%s (%s): Kp = %.3f; Ts = %.3f;" % (self.name(), self.__class__.__name__, self.p_Kp().value(), self.p_Ts().value())

    def name( self):
        """
        """
        return "P"

    def reset( self):
        """
        """
        self.__p_e.value( 0.0)
        self.__p_u.value( 0.0)
        return self


class PDT1(_AlgorithmDigital):

    """PD real, tau-Variante, Euler rückwärts, EINE Übertragungsfunktion: \f$ R(s) = K_P + \frac {K_D s}{1 + \tau_D s} = K_P \left ( 1 + \frac {T_D s}{1 + \tau_D s} \right ) = K_P \left ( 1 + \frac {T_D s}{1 + \alpha T_D s} \right ) = K_P \frac {1 + (1 + \alpha) T_D s}{1 + \alpha T_D s}, \ \ \alpha < 1 \f$  mit \f$ T_D = \frac {K_D}{K_P},\ \tau_D = \alpha T_D \f$

    Differenzengleichung **PDT1 By Euler Backwards (Variante DT1)** für
    Implementation auf einem Rechner.

    Laplace-Transformierte

        \f[
            R(s) = K_P + \frac {K_D s}{1 + \tau_D s}
                 = K_P \left ( 1 + \frac {T_D s}{1 + \tau_D s} \right )
                 = K_P \left ( 1 + \frac {T_D s}{1 + \alpha T_D s} \right )
                 = K_P \frac {1 + (1 + \alpha) T_D s}{1 + \alpha T_D s}, \ \ \ \alpha < 1
        \f]

        mit

        \f[
            T_D = \frac {K_D}{K_P},\ \tau_D = \alpha T_D
        \f]

    Differenzengleichung

        \f[
            u_k = \frac 1 {1 + \tau_D'} \left[ \tau_D' u_{k-1} + (K_P [1 + \tau_D'] + K_D') e_k  - (K_P \tau_D' + K_D') e_{k-1} \right]
        \f]

        mit

        \f[
            K_D' = \frac {K_D}{T_s},\ \tau_D' = \frac {\tau_D}{T_s} = \alpha T_D'
        \f]

    \param  p_Kp
    \param  p_Kd
    \param  p_alpha
    \param  p_Ts

    \param  p_e
        Eingangssignal *Regeldifferenz*

    \param  p_u
        Ausgangssignal *Stellgröße*

    \note
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.

    History

        -   2016-04-19: Created.

    """

    @staticmethod
    def KpTd( Kp, Kd, alpha):
        """Reglerverstärkung und Zeitkonstante aus Koeffizenten.

        \f[ T_D = \frac K_D K_P,\ \tau_D = \alpha T_D \f]
        """
        Kr = Kp
        Td = Kd/Kp
        return Kr, Td


    @staticmethod
    def KpKd( Kr, Td, alpha):
        """Koeffizienten aus Reglerverstärkung und Zeitkonstante.

        \f[ T_D = \frac K_D K_P,\ \tau_D = \alpha T_D \f]
        """
        Kp = Kr
        Kd = Kr*Td
        return Kp, Kd


    def __init__( self, *, id, p_Kp, p_Kd, p_alpha, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_Kp = p_Kp
        self.__p_Kd = p_Kp
        self.__p_alpha = p_alpha

        self.__e_ = [ 0] * 2
        self.__u_ = [ 0] * 2

        self.configure( p_Ts)
        return

    @overrides( _AlgorithmDigital)
    def configure( self, p_Ts):
        pass

    @overrides( _AlgorithmDigital)
    def execute( self):
        """Berechnung der Differenzengleichung.
        """
        ### Ein paar Abkürzungen
        #
        Kp = self.__p_Kp.value()
        Kd = self.__p_Kd.value()
        alpha = self.__p_alpha.value()
        Ts = self.p_Ts().value()

        e_ = self.__e_
        u_ = self.__u_

        ### Signal-Listen vorbereiten
        #
        e_[-1] = e_[ 0]
        u_[-1] = u_[ 0]

        ##  Eingangssignal lesen
        #
        e_[0] = self.p_e().value()

        ### Ausführung des effektiven Algorithmus
        #
        Kds = Kd/Ts
        tauD = alpha*Kd/Kp
        tauDs = tauD/Ts

        u_[0] = tauDs * u_[-1] + (Kp + (1 + alpha) * Kds) * e_[0] - (1 + alpha) * Kds * e_[-1]
        u_[0] /= (1 + tauDs)

        ### Ausgangssignal schreiben, dabei evtl. die Bounds berücksichtigen
        #
        self.p_u().value( u_[ 0])

        return

    def info( self):
        return "%s (%s): Kp = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(),
                   self.__class__.__name__,
                   self.__p_Kp.value(),
                   self.__p_Kd.value(),
                   self.__p_alpha.value(),
                   self.p_Ts().value()
               )

    def name( self):
        return "PDT1"

    def reset( self):
        self.__p_e.value( 0.0)
        self.__p_u.value( 0.0)

        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3
        return



class PIDT1(_AlgorithmDigital):

    """PID real (= PID + T1), Euler rückwärts, EINE Übertragungsfunktion.

    \param  p_Kp:       Proportional gain.
    \param  p_Ki:       Integral gain.
    \param  p_Kd:       Differential gain.
    \param  p_alpha:    \$ \alpha = \frac {\tau_D}{T_D},\ \ \ T_D = \frac {K_D}{K_P} \$
                        As \% \tau_D \$ is needed for the calculations, the representation
                        \$ \tau_D = \alpha \frac {K_d}{K_p} \$ fits much better.
    \param  p_Ts:       Sample time.
    \param  p_e:        Regeldifferenz.
    \param  p_u:        Stellgröße.

    \note

        Keine Windup-Prävention! Grund: Der Integrator ist nicht separat zugänglich,
        weil nur EINE Übertragungsfunktion realisiert ist.

    \note
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.
    """

    @staticmethod
    def KpKiKd( Kr, Tr1, Tr2, alpha):
        """Transform works as follows (cal'ed with *Sage 5.3*, simplified manually):

        \f[
            K_I = K_R
        \f]

        \f[
            K_D = K_R \frac {T_{R1} T_{R2}}{1 + \alpha}
        \f]

        \f[
            K_P = K_R \frac {T_{R1} + T_{R2}}{2} \pm \frac {K_R} {2} \sqrt{2 \frac {1 - \alpha}{1 + \alpha} T_{R1} T_{R2} + (1 + \alpha)(T_{R1}^2 + T_{R2}^2)}
        \f]
        """
        Ki = Kr
        Kd = Kr*Tr1*Tr2/(1 + alpha)
        Kp = Kr*(Tr1 + Tr2)/2. + Kr/2*math.sqrt( 2*(1 - alpha)/(1 + alpha)*Tr1*Tr2 + (1 + alpha)*(Tr1*Tr1 + Tr2*Tr2))
        return Kp, Ki, Kd

    @staticmethod
    def KrTr1Tr2( Kp, Ki, Kd, alpha):
        """Transform works as follows (cal'ed with *Sage 5.3*, simplified manually):

        \f$ K_P \ne,\ K_I \ne 0,\ K_D \ne 0 \f$ :

            \f[
                K_R = K_I
            \f]

            \f[
                T_{R1} = \frac {\alpha K_D}{2 K_P} + \frac {K_P}{2 K_I}\pm \frac 1 {2 K_I K_P} \sqrt{(\alpha K_D K_I)^2 - 2 (\alpha + 2) K_D K_I K_P^2 + K_P^4}
            \f]

            \f[
                T_{R2} = \frac {2 (\alpha +1) K_D K_P}{\alpha K_D K_I + K_P^2 \pm \sqrt{(\alpha K_D K_I)^2 - 2 \alpha K_D K_I K_P^2 - 4 K_D K_I K_P^2 + K_P^4}}
            \f]

        \f$ K_P \ne,\ K_I \ne 0,\ K_D = 0 \f$ :

            \f[
                K_R = K_I
            \f]

            \f[
                T_{R1} = \frac {K_P}{K_I}
            \f]

            \f[
                T_{R2} = 0
            \f]

        \f$ K_P \ne,\ K_I = 0,\ K_D \ne 0 \f$ :

            \f[
                K_R = K_P
            \f]

            \f[
                T_{R1} = (1 + \alpha)\frac {K_D}{K_P}
            \f]

            \f[
                T_{R2} = 0
            \f]

        \f$ K_P \ne,\ K_I = K_D = 0 \f$ :

            \f[
                K_R = K_P
            \f]

            \f[
                T_{R1} = T_{R2} = 0
            \f]
        """
        Kr, Tr1, Tr2 = 0., 0., 0.
        if Kp and Ki and Kd:
            Kr = Ki
            Tr1 = alpha*Kd/(2.*Kp) + Kp/(2.*Ki) + 1/(2.*Ki*Kp)*math.sqrt((alpha*Kd*Ki)**2 - 2*(alpha + 2)*Kd*Ki*Kp**2 + Kp**4)
            Tr2 = 2*(alpha + 1)*Kd*Kp/(alpha*Kd*Ki + Kp*Kp + math.sqrt((alpha*Kd*Ki)**2 - 2*alpha*Kd*Ki*Kp**2 - 4*Kd*Ki*Kp**2 + Kp**4))

        elif Kp and Ki:
            Kr = Ki
            Tr1 = Kp/Ki
            Tr2 = 0.

        elif Kp and Kd:
            Kr = Kp
            Tr1 = (1 + alpha)*Kd/Kp
            Tr2 = 0.

        elif Kp:
            Kr = Kp
            Tr1 = 0
            Tr2 = 0

        else:
            pass

        return Kr, Tr1, Tr2


    def __init__( self, *, id, p_Kp : pandora.Box, p_Ki : pandora.Box, p_Kd : pandora.Box, p_alpha : pandora.Box, p_Ts : pandora.Box, p_e : pandora.Box, p_u : pandora.Box):
        super().__init__( id=id,p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        assert isinstance( p_e, pandora.Box)
        assert isinstance( p_u, pandora.Box)
        p_u.reg_tau4s_on_limit_violated( self._tau4s_on_saturation_)

        self.__p_Kp = p_Kp
        self.__p_Ki = p_Ki
        self.__p_Kd = p_Kd
        self.__p_alpha = p_alpha

        self.__p_e = p_e
        self.__p_u = p_u

        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3

        self.configure()
        return

    def configure( self, p_Ts):
        pass

    def execute( self):
        r"""Berechnung der Differenzengleichung.

        .. note::

            Differenzengleichung *PIDT1 By Euler Backwards (Variante DT1)* für Implementation auf einem Rechner

            .. math:: u_k = \frac 1 {1 + \tau_D'}\left[ (1 + 2\tau_D') u_{k-1} - \tau_D' u_{k-2} + (b_0 T_s + b_1 + b_2') e_k - (b_1 + 2 b_2') e_{k-1} + b_2' e_{k-2}\right]

            .. math::

                b_0 = K_I,

                b_1 = (K_I\tau_D + K_P),

                b_2 = (K_D + K_P\tau_D),

                b_2' = b_2/T_s,

                \tau_D' = \tau_D/T_s

        ::

            tauD = alpha*Kd/Kp
            tauDs = tauD/Ts
            b0 = Ki
            b1 = Ki*tauD + Kp
            b2 = Kd + Kp*tauD
            b2s = b2/Ts

            u_[0] = (1 + 2*tauDs)*u_[-1] - tauDs*u_[-2] + (b0*Ts + b1 + b2s)*e_[0] - (b1 + 2*b2s)*e_[-1] + b2s*e_[-2]
            u_[0] /= (1 + tauDs)
        """
        ##  Ein paar Abkürzungen
        #
        Kp = self.__p_Kp.value()
        Ki = self.__p_Ki.value()
        Kd = self.__p_Kd.value()
        alpha = self.__p_alpha.value()
        Ts = self.p_Ts().value()

        e_ = self.__e_
        u_ = self.__u_

        ##  Signal-Listen vorbereiten
        #
        e_[-2] = e_[-1]
        e_[-1] = e_[ 0]
        u_[-2] = u_[-1]
        u_[-1] = u_[ 0]

        ##  Eingangssignal lesen
        #
        e_[0] = self.__p_e.value()

        ##  Ausführung des effektiven Algorithmus
        #
        tauD = alpha*Kd/Kp
        tauDs = tauD/Ts
        b0 = Ki
        b1 = Ki*tauD + Kp
        b2 = Kd + Kp*tauD
        b2s = b2/Ts

        u_[0] = (1 + 2*tauDs)*u_[-1] - tauDs*u_[-2] + (b0*Ts + b1 + b2s)*e_[0] - (b1 + 2*b2s)*e_[-1] + b2s*e_[-2]
        u_[0] /= (1 + tauDs)

        u = u_[0]

        ##  Ausgangssignal schreiben
        #
        self.__p_u.value( u)
        return

    def info( self):
        return "%s (%s): Kp = %.3f; Ki = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(),
                   self.__class__.__name__,
                   self.__p_Kp.value(),
                   self.__p_Ki.value(),
                   self.__p_Kd.value(),
                   self.__p_alpha.value(),
                   self.p_Ts().value()
               )

    def name( self):
        return "PIDT1"

    def reset( self):
        self.__p_e.value( 0)
        self.__p_u.value( 0)

        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3
        return

    def _tau4s_on_saturation_( self, pc):
        """Stellgrößenlimit überschritten.

        .. todo::
            In dieser Methode kann nun der Integrator dealtiviert werden.
        """
        return


class PIDT1p(_AlgorithmDigital):

    """PID real (= PID + T1), Euler rückwärts, 3 Übertragungsfunktionen **parallel**, die das Gesamtverhalten realisieren.

    \param  p_Kp:
    \param  p_Ki:
    \param  p_Kd:
    \param
    \param  FlexVarblHL p_Ts:

    Hier lässt sich das Windup des Integrators verhindern, indem der Integrator
    auf Pause geschaltet wird, wenn **die Summe der drei Einzelsignale** die
    Stellgrenzen überschreiten.

    Art der Windup-Prävention:
        Abschalten des Integrators.

    \note
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.
    """

    @staticmethod
    def KrTr1Tr_to_KpKiKd( Kr, Tr1, Tr2):
        """

        ::

            K  = K
             i    R

                       T   T
                        R1  R2
            K  = K  * ---------- bzw.
             d    R   1 + alpha

            K  .=  K  T   T  , alpha << 1
             d      R  R1  R2

                                           ______________________________
                                          /           2
                     T   + T             / (T   + T  )          T   T
                      R1    R2          /    R1    R2            R1  R2
            K  = K  ---------- +/- K  |/  ------------ - alpha ---------- bzw.
             P    R     2           R |         4              1 + alpha

            K  .= K  (T   + T  ), alpha << 1
             p     R   R1    R2

        """
        Ki = Kr
        Kd = Kr*Tr1*Tr2
        Kp = Kr*(Tr1 + Tr2)
        return Kp, Ki, Kd


    def __init__( self, *, id, p_Kp, p_Ki, p_Kd, p_alpha, p_Ts, p_e, p_u):
        super().__init__( id=id,p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_e = p_e
        self.__p_u = p_u

        p_uP = pandora.Box( value=0.0);    assert not p_uP.is_clipping()
        p_uDT1 = pandora.Box( value=0.0);  assert not p_uDT1.is_clipping()
        p_uI = pandora.Box( value=0.0);    assert not p_uI.is_clipping()
        self.__algorithmP = P( id=u"%s: P" % id, p_Kp=p_Kp, p_Ts=p_Ts, p_e=p_e, p_u=p_uP)
        self.__algorithmDT1 = DT1( id=u"%s: DT1" % id, p_Kd=p_Kd, p_alpha=p_alpha, p_Ts=p_Ts, p_e=p_e, p_u=p_uDT1)
        self.__algorithmI = I( id=u"%s: I" % id, p_Ki=p_Ki, p_Ts=p_Ts, p_e=p_e, p_u=p_uI)

        p_u.reg_tau4s_on_limit_violated( lambda pc, self=self: self.__algorithmI.pause())
        #p_u.reg_tau4s_on_limit_unviolated( lambda pc, self=self: self.__algorithmI.resume())
        # ##### Wozu das denn?

        ##  Die folgenden Attribute sind nur wegen .info() notwendig
        #
        self.__p_Kp = p_Kp
        self.__p_Ki = p_Ki
        self.__p_Kd = p_Kd
        self.__p_alpha = p_alpha

        return

    def configure( self, p_Ts):
        pass

    def p_Kp( self):
        return self.__algorithmP.p_Kp()

    def p_Ki( self):
        return self.__algorithmI.p_Ki()

    def p_Kd( self):
        return self.__algorithmDT1.p_Kd()

    def p_alpha( self):
        return self.__algorithmDT1.p_alpha()

    def info( self):
        return "%s (%s): Kp = %.3f; Ki = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(),
                   self.__class__.__name__,
                   self.__p_Kp.value(),
                   self.__p_Ki.value(),
                   self.__p_Kd.value(),
                   self.__p_alpha.value(),
                   self.p_Ts().value()
               )

    def execute( self):
        """Berechnung der Differenzengleichung.

        .. math::

            PIDT1(s) =

        .. math::

            PIDT1(z) =

        .. math::

            u_k =
        """
        ### Ein paar Abkürzungen
        #
        pass

        ### Eingangssignal lesen
        #
        e = self.__p_e.value()

        ### Alle Elemente mit Fehlersignal versorgen
        #
        self.__algorithmP.p_e().value( e)
        self.__algorithmDT1.p_e().value( e)
        self.__algorithmI.p_e().value( e)

        ### Alle Elemente ausführen
        #
        self.__algorithmP.execute()
        self.__algorithmDT1.execute()
        self.__algorithmI.execute()

        ### Alle Elemente "abernten"
        #
        uP = self.__algorithmP.p_u().value()
        uDT = self.__algorithmDT1.p_u().value()
        uI = self.__algorithmI.p_u().value()

        ### Ausgangssignal = Summe der einzelnen Ausgangssignale
        #
        u = uP + uDT + uI
        self.p_u().value( u)
                                        # Löst aus, wenn's eine FlexVarblHL ist.
        return

    def name( self):
        return "PIDT1p"

    def reset( self):
        self.input_value( 0)
        self.output_value( 0)

        self.__algorithmP.reset()
        self.__algorithmI.reset()
        self.__algorithmDT1.reset()
        return


class PI(PIDT1p):

    """PI-Regler.
    """

    def __init__( self, *, id, p_Kp : pandora.Box, p_Ki : pandora.Box, p_Ts : pandora.BoxMonitored, p_e : pandora.Box, p_u : pandora.BoxClippingMonitored):
        super().__init__( id=id, p_Kp=p_Kp, p_Ki=p_Ki, p_Kd=pandora.Box( value=0.0), p_alpha=pandora.Box( value=1.0), p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        return


class PT1(_AlgorithmDigital):

    """PT1

    ::

                    K
                      1
        PT1(s) = ---------
                 1 + T  s
                      1

    \param  id:    Unique identification of the element.

    \param  p_K1:  Gain.

    \param  p_T1:  Time constant.

    \param  p_Ts:  Sample time.

    \note
        p_Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem
        .execute() neu berechnet werden.
    """

    def __init__( self, *, id, p_K1, p_T1, p_Ts, p_e, p_u):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_K1 = p_K1
        self.__p_T1 = p_T1
        self.__p_e = p_e
        self.__p_u = p_u

        self.__u_ = [ 0, 0]
        self.__y_ = [ 0, 0]
        return

    def configure( self, p_Ts):
        """Es gibt hier nichts zu tun, denn execute() greift auf p_Ts, das sich bereits geändert hat, wenn es geändert worden ist.
        """
        return

    def name( self):
        return self.__class__.__name__

    def p_K1( self):
        """Streckenverstärkung.
        """
        return self.__p_K1

    def p_Ks( self):
        """Streckenverstärkung.
        """
        return self.__p_K1

    def p_T1( self):
        """Zeitkonstante.
        """
        return self.__p_T1

    def execute( self):
        """Execute the algorithm.

        ::

                        K
                         1
            PT1(s) = --------
                     1 + T  s
                          1

        When we substitute ::

                 1        -1
            s = --- (1 - z  )
                 T
                  s

        we get

        .. math::
            PT1(z)
            = \frac {K_1}{1 + T_1 (1 - z^{-1})}
            = \frac {K_1}{(1 + T_1) - T_1 z^{-1})}

        Difference equation *PT1 by Euler Bw*

        .. math::
            u_k = \frac {1}{1 + T_1} \left( T_1 u_{k-1} + K_1 e_k\right)

        """
        ##  Abkürzungen
        #
        u_ = self.__u_
        y_ = self.__y_
        K1 = self.__p_K1.value()
        T1 = self.__p_T1.value()
        Ts = self.p_Ts().value()

        ##  Werte aus letztem Schritt übernehmen
        #
        u_[-1] = u_[0]
        y_[-1] = y_[0]

        ##  Input lesen
        #
        u_[0] = self.__p_e.value()

        ##  Algorithmus ausführen
        #
        T1s = T1/Ts

        ##  Ausführen des effektiven Algorithmus
        #
        y_[0] = T1s*y_[-1] + K1*u_[0]
        y_[0] /= (1 + T1s)

        y = y_[0]

        ##  Output schreiben
        #
        self.__p_u.value( y)

        return

    def info( self):
        """
        """
        return "PT1 (Euler bw)"

    def reset( self):
        """
        """
        self.__p_e.value( 0)
        self.__p_u.value( 0)
        self.__u_ = [ 0, 0]
        self.__y_ = [ 0, 0]
        return



class PT1PT1(_AlgorithmDigital):

    """Kombi aus mehr als einer Übertragungsfunktion.

    \param  id      Eindeutige Identifikation.
    \param  p_K     Verstärkung.
    \param  p_T1    Erste Zeitkonstante.
    \param  p_T2    Zweite Zeitkonstante.
    \param  p_Ts    Abtastzeit. Änderungen nach Instanzierung sind erlaubt,
                    haben aber eine Neuberechnung der Koeffizienten zur Folge.
    \param  p_e     Eingangssignal.
    \param  p_u     Ausgangssignal.
    """

    def __init__( self, *, id: Id, p_K: pandora.Box, p_T1: pandora.Box, p_T2: pandora.Box, p_Ts: pandora.BoxMonitored, p_e: pandora.Box, p_u: pandora.Box):
        super().__init__( id=id, p_Ts=p_Ts, p_e=p_e, p_u=p_u)

        self.__p_K = p_K
        self.__p_T1 = p_T1
        self.__p_T2 = p_T2
        self.__p_e = p_e
        self.__p_u = p_u

        p_u_e = pandora.Box( value=0.0)
        self.__algos = (\
            PT1( \
                id=Id( "%s.%s" % (id, "pt1.1")),
                p_K1=p_K,
                p_T1=p_T1,
                p_Ts=p_Ts,
                p_e=self.__p_e,
                p_u=p_u_e
            ),
            PT1( \
                id=Id( "%s.%s" % (id, "pt1.2")),
                p_K1=pandora.Box( value=1.0),
                p_T1=p_T2,
                p_Ts=p_Ts,
                p_e=p_u_e,
                p_u=self.__p_u
            )
        )

        self.__u_ = [ 0, 0]
        self.__y_ = [ 0, 0]
        return

    def configure( self, p_Ts):
        for algo in self.__algos:
            algo.configure( p_Ts)

        return

    def execute( self):
        """Execute the algorithms.
        """

        for algo in self.__algos:
            algo.execute()

        return

    def info( self):
        """
        """
        return "PT1*PT1 (Euler bw)"

    def name( self):
        return self.__class__.__name__

    def p_K( self):
        """Streckenverstärkung.
        """
        return self.__p_K
    p_Ks = p_K
    p_K1 = p_K

    def p_T1( self):
        """Zeitkonstante 1.
        """
        return self.__p_T1

    def p_T2( self):
        """Zeitkonstante 2.
        """
        return self.__p_T2

    def reset( self):
        """
        """
        for algo in self.__algos:
            algo.reset()

        return

    def _tau4s_on_Ts_modified_( self, tau4pc):
        Ts = tau4pc().client().value()
        self.configure( pandora.Box( value=Ts))
        return


