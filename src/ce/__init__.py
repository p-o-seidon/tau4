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

import logging; _Logger = logging.getLogger()


import abc
from tau4.sweng import overrides
from tau4.data import flex


class _AlgorithmDigital(metaclass=abc.ABCMeta):
    
    """Basisklasse für alle Algorithmen.
    
    :param  id:                 Id des Algorithmus. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    :param  FlexVarblHL fv_Ts:  Abstastzeit.
    
    Die Abtastzeit ist zwar eine "teure" FlexVarblHL, wird aber intern als 
    schnelle FlexVarblLL gespeichert, die sich für Änderungen der FlexVarblHL 
    registriert.
    """
    
    def __init__( self, *, id, fv_Ts, fv_e, fv_u):
        self.__id = id
        self.__fv_Ts = flex.Variable( value=fv_Ts.value())
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        fv_Ts.reg_tau4s_on_modified( lambda pc: self._fv_Ts.value( pc.client().value()))
        return
    
    @abc.abstractclassmethod
    def configure( self, fv_Ts):
        """Konfigurieren des Algorithmus.
        
        Beispielsweise wird der Algorithmus hier die Koeffizienten der 
        Differenzengleichung berechnen wollen.

        :param  FlexVarblLL fv_Ts:  Abtastzeit.
        """
        pass
    
    def fv_e( self):
        """Eingangssignal.
        """
        return self.__fv_e

    def fv_Ts( self):
        """Abstatszeit.
        """
        return self.__fv_Ts

    def fv_u( self):
        """Ausgangssignal.
        """
        return self.__fv_u

    @abc.abstractclassmethod    
    def configure( self):
        """Konfiguarion.
        
        Kann dazu verwendet werden, die Koeffizienten neu zu berechnen, währen 
        Instanzen schon ausgeführt werden.
        """
        pass
    
    def id( self):
        """Eindeutige Id.
        """
        return self.__id

    @abc.abstractclassmethod    
    def execute( self):
        """Ausführung des Regelalgorithmus.
        """
        pass
    
    @abc.abstractclassmethod    
    def info( self):
        """Info zum Algorithmus (z.B. Name).
        """
        pass
    
    @abc.abstractclassmethod    
    def name( self):
        """Name des Algorithmus.
        """
        pass
    
    @abc.abstractclassmethod    
    def reset( self):
        """Reset des Algorithmus, also seiner Daten.
        """
        pass


class EulerBw4DT1(_AlgorithmDigital):
    
    r"""Algorithmus *Euler rückwärts* für DT1-Regler.
    
    :param              id:         Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    :param  FlexVarblLL fv_Kd:      Reglerverstärkung.
    :param  FlexVarblLL fv_alpha:   **2DO** 
    :param  FlexVarblLL fv_Ts:      Abstastzeit.
    :param  FlexVarblLL fv_e:       Regeldifferenz. 
    :param  FlexVarblHL fv_u:       Stellgröße. Muss eine FlexVarbl sein, damit eine Reg'ung für Bereichsüberschreitungen möglich ist.
    
    Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem 
    .execute() neu berechnet werden.
    
    .. todo::   **Ändern:**
        Die Koeffizienten sollen nicht bei jedem .execute() berechnet werden, 
        das ist neu Aufgabe von .configure().
        
    **No, How?**
    
    .. math::
    
        DT1(s) = \frac {K_D s}{1 + \tau_D s} = K_P \frac {T_D s}{1 + \alpha T_D s},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        
        DT1(z) = K_P \frac {T_D' (1 - z{⁻1})}{(1 + \alpha T_D') - \alpha T_D' z^{-1}},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
        
        u_k = \frac 1 {1 + \alpha K_D'} \left[ \alpha K_D' u_{k-1} + K_D'(e_k - e_{k-1}\right],\ \ \ K_D' = \frac {K_D}{T_s},\ \ \ \alpha = 0...1
    """
    
    def __init__( self, *, id, fv_Kd, fv_alpha, fv_Ts, fv_e, fv_u):
        super().__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_Kd = fv_Kd
        self.__fv_alpha = fv_alpha
        
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        self.__e_ = [ 0, 0]
        self.__u_ = [ 0, 0]
        return
    
    def configure( self):
        pass
    
    def execute( self):
        """Executes the algorithm.
        
        .. math::
        
            DT1(s) = \frac {K_D s}{1 + \tau_D s} = K_P \frac {T_D s}{1 + \alpha T_D s},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
            
            DT1(z) = K_P \frac {T_D' (1 - z{⁻1})}{(1 + \alpha T_D') - \alpha T_D' z^{-1}},\ \ \ \alpha = \frac {\tau_D}{T_D}, \ \ \ T_D = \frac {K_D}{K_P}
            
            u_k = \frac 1 {1 + \alpha K_D'} \left[ \alpha K_D' u_{k-1} + K_D'(e_k - e_{k-1}\right],\ \ \ K_D' = \frac {K_D}{T_s},\ \ \ \alpha = 0...1
        """
        ##  Abkürzungen
        #
        e_ = self.__e_
        u_ = self.__u_
        Kd = self.__fv_Kd.value()
        alpha = self.__fv_alpha.value()
        Ts = self.fv_Ts().value()
        
        ##  Werte aus letztem Schritt übernehmen
        #
        e_[-1] = e_[0]
        u_[-1] = u_[0]
        
        ##  Input lesen
        #
        e_[0] = self.__fv_e.value()
        
        ##  Algorithmus ausführen
        #
        Kds = Kd/Ts
        u_[0] = alpha*Kds*u_[-1] + Kds*(e_[0] - e_[-1])
        u_[0] /= (1 + alpha*Kds)
        
        u = u_[0]

        ##  Output schreiben
        #
        self.__fv_u.value( u)

        return
    
    def info( self):
        return "%s (%s): Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(), 
                   self.__class__.__name__, 
                   self.__fv_Kd.value(), 
                   self.__fv_alpha.value(), 
                   self.fv_Ts().value()
               )
        
    def name( self):
        return u"DT1"
    
    def reset( self):
        self.__fv_e.value( 0.0)
        self.__fv_u.value( 0.0)
        self.__e_ = [ 0, 0]
        self.__u_ = [ 0, 0]
        return


class EulerBw4gPIDT1p(_AlgorithmDigital):
    
    r"""PID allgemein, real, Euler rückwärts, 3 Übertragungsfunktionen PARALLEL, Windup Prevention.
    
    :param              id:         Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    :param  FlexVarblHL fv_Kr:      Gesamtverstärkung.
    :param  FlexVarblHL fv_b0:      Polynomkoeffizient.
    :param  FlexVarblHL fv_b1:      Polynomkoeffizient.
    :param  FlexVarblHL fv_b2:      Polynomkoeffizient.
    :param  FlexVarblHL fv_alpha:   0...1
    :param  FlexVarblHL fv_Ts:      Abstastzeit.

    Art der Windup-Prävention:
        Abschalten des Integrators.
    
    Hier lässt sich das Windup des Integrators verhindern, indem der Integrator 
    auf Pause geschaltet wird, wenn die Summe der drei Einzelsignale die 
    Stellgrenzen überschreiten. 
    
    .. note::
    
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
        
        .. math:: 
        
            K_R (1 + b_1 s + b_2 s^2) = \omega_0^2 \left( 1 + \frac {2\sigma}{\omega_0^2} s + \frac 1 {\omega_0^2} s^2 \right)
        
        mit
        
        .. math:: 
        
            \omega_0^2 = \sigma^2 + \omega_d^2
        
        Der Standard-PIDT1-Regler ist so definiert:
        
        .. math:: 
        
            PIDT_1(s) = K_I \frac {1 + \left(\tau_D + \frac {K_P}{K_I}\right) s + \frac {K_P}{K_I} \left(\tau_D + \frac {K_D}{K_P}\right) s^2}{s \left(1 + \tau_D s\right)}
            
        Damit gilt also:
        
        .. math::
        
            K_R = K_I
    
            b_1 = \tau_D + \frac {K_P}{K_I}
    
            b_2 = \frac {K_P}{K_I} \left(\tau_D + \frac {K_D}{K_P}\right)
            

    .. note::
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem 
        .execute() neu berechnet werden.
    """
    
    def __init__( self, *, id, fv_Kr, fv_b0, fv_b1, fv_b2, fv_alpha, fv_Ts, fv_e, fv_u):
        super().__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_Kr = fv_Kr
        self.__fv_b0 = fv_b0
        self.__fv_b1 = fv_b1
        self.__fv_b2 = fv_b2
        self.__fv_alpha = fv_alpha
        
        self.__fv_e = fv_e
        self.__fv_u = fv_u

        fv_uPT1 = FlexVarblLL( value=.0)
        fv_uDT1 = FlexVarblLL( value=0.0)
        fv_uI = FlexVarblLL( value=0.0)
        
        self.__algorithmPT1 = EulerBw4PT1( id=id + ": PT1", fv_K1=0, fv_T1=0, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uPT1)
        self.__algorithmDT1 = EulerBw4DT1( id=id + ": DT1", fv_Kd=0, fv_alpha=0, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uDT1)
        self.__algorithmI = EulerBw4I( id=id + ": I", fv_Ki=0, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uDT1)
        
        fv_u.reg_tau4p_on_violated( lambda *arg: self.__algorithmI.pause())
        fv_u.reg_tau4p_on_unviolated( lambda *arg: self.__algorithmI.resume())
                                        # Kann das der Aktuator? Wenn nicht, 
                                        #   müssen wir den Integrierer pausieren 
                                        #   lassen, d.h. er bleibt einfach "stehen" 
                                        #   (schaltet sich nicht aus).
                                        #   Das funktioniert allerdings nur dann 
                                        #   richtig, wenn der Regler die 
                                        #   Werte aus dem Aufruf k-1 zu Beginn 
                                        #   von execute() übernimmt und nicht 
                                        #   schon am Ende von execute().
        self.__fv_Kr.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__fv_b0.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__fv_b1.reg_tau4p_on_modified( lambda *args: self.configure())
        self.__fv_b2.reg_tau4p_on_modified( lambda *args: self.configure())
        
        self.configure()
        return
    
    def configure( self):
        self._recal_algorithms_()
        return
    
    def fv_Kp( self):
        """Zugriff auf fv_Kp.
        
        Delegiert an EulerBw4PT1.
        """
        return self.__algorithmPT1.fv_K1()
    
    def fv_Ki( self):
        """Zugriff auf fv_Ki.
        
        Delegiert an EulerBw4I.
        """
        return self.__algorithmI.fv_Ki()
    
    def fv_Kd( self):
        return self.__algorithmDT1.fv_Kd()
    
    def fv_alpha( self):
        return self.__algorithmDT1.fv_alpha()
    
    def fv_Kr( self):
        return self.__fv_Kr
    
    def fv_b0( self):
        return self.__fv_b0
    
    def fv_b1( self):
        return self.__fv_b1
    
    def fv_b2( self):
        return self.__fv_b2
    
    
    def execute( self):
        """Berechnung der Differenzengleichung.
        
        Die Regeldifferenz steht im FlexEntity fv_e, der dem Ctor übergeben wird 
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
        fv_uDT1 = self.__algorithmPT1.fv_u()
        fv_uI = self.__algorithmPT1.fv_u()
        fv_uPT1 = self.__algorithmPT1.fv_u()
        fv_u.value( fv_uPT1.value() + fv_uDT1.value() + fv_uI.value())
                                        # Löst eine Limit Violation aus. Dazu 
                                        #   muss es sich bei fv_u aber auch um 
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
                   self.__fv_Kp.value(), 
                   self.__fv_Ki.value(), 
                   self.__fv_Kd.value(), 
                   self.__fv_alpha.value(), 
                   self.fv_Ts().value()
               )
    
    def name( self):
        return "gPIDT1 (parallel form)"
    
    def reset( self):
        self.__fv_e.value( 0.0)
        self.__fv_u.value( 0.0)
        
        self.__algorithmPT1.reset()
        self.__algorithmI.reset()
        self.__algorithmDT1.reset()
        return

    def _recal_algorithms_( self):
        b0 = self.__fv_b0
        b1 = self.__fv_b1
        b2 = self.__fv_b2
        Kr = self.__fv_Kr
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

    
class EulerBw4I(_AlgorithmDigital):
    
    """Integrator.
    
    Provides windup protection!
    
    Parameters:
    :param              id:     Id des Reglers. Das ist ganz praktisch, wenn es mehr als einen Regler im System gibt.
    :param  FlexVarbl   fv_Ki:  Integral constant.
    :param  FlexVarbl   fv_Ts:  Abstastzeit.

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
    
    def __init__( self, *, id, fv_Ki, fv_Ts, fv_e, fv_u):
        super().__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_Ki = fv_Ki
        
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
    def configure( self):
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
        Ki, Ts = self.__fv_Ki.value(), self.fv_Ts().value()
        
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
        e_[0] = self.fv_e().value()

        ##  Ausführen des eigentlichen Algorithmus
        #
        u_[0] = u_[-1] + Ki*Ts*e_[0]
        
        u = u_[0]

        ##  Write to the plant
        #
        self.fv_u().value( u)
        
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
    
    def fv_Ki( self, arg=None):
        """Integrationsbeiwert.
        """
        return self.__fv_Ki
    
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
            self.fv_u().value( self.__u_[0])
            
        return
        
    def resume( self):
        if self.__is_paused:
            self.__is_paused = False
            
        return
        
    @overrides(_AlgorithmDigital)
    def reset( self):
        """
        """
        self.fv_e().value( 0)
        self.fv_u().value( 0)
        self.__e_ = [0, 0]
        self.__u_ = [0, 0]
        return
    

class EulerBw4P(_AlgorithmDigital):
    
    """P-Regelalgorithmus.
    
    :param  fv_Kp:  FlexVarblLL Proportionalverstärkung
    :param  fv_Ts:  FlexVarblLL Abtastzeit (wird hier nicht gebraucht).
    :param  fv_e:   FlexVarblLL für Eingangssignal *Regelabweichung*.
    :param  fv_u:   FlexVarblLL für Ausgangssignal *Stellgröße*.
    """
    
    def __init__( self, *, id, fv_Kp, fv_Ts, fv_e, fv_u):
        super().__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_e = fv_e; assert isinstance( self.__fv_e, flex.Variable)
        self.__fv_Kp = fv_Kp; assert isinstance( self.__fv_Kp, flex.Variable) 
        return
    
    def configure( self, fv_Ts):
        """Ausführung einer Neukonfiguration.
        
        Ausführung mindestens bei Ausführung des Ctor von :py:class:`SISOController`.
        
        .. note::
        
            Man könnte sich also die Übergabe von fv_Ts an diesen Ctor sparen!
        """
        assert self.fv_Ts() == fv_Ts
        return
    
    def execute( self):
        """Execute the algorithm.
        """
        self.fv_u().value( self.__fv_Kp.value() * self.fv_e().value())
        return True
    
    def fv_Kp( self):
        """Reglerverstärkung
        """
        return self.__fv_Kp

    def is_windup_protection_active( self):
        """
        """
        return False
    
    def info( self):
        return "%s (%s): Kp = %.3f; Ts = %.3f;" % (self.name(), self.__class__.__name__, self.fv_Kp().value(), self.fv_Ts().value())
    
    def name( self):
        """
        """
        return "P"
    
    def reset( self):
        """
        """
        self.__fv_e.value( 0.0)
        self.__fv_u.value( 0.0)
        return self
    
    
class EulerBw4PDT1(_AlgorithmDigital):
    
    r"""PD real, tau-Variante, Euler rückwärts, EINE Übertragungsfunktion.

    Differenzengleichung **PDT1 By Euler Backwards (Variante DT1)** für 
    Implementation auf einem Rechner.

    **Laplace-Transformierte**
    
    .. math::
    
        R(s) = K_P + \frac {K_D s}{1 + \tau_D s} 
             = K_P \left ( 1 + \frac {T_D s}{1 + \tau_D s} \right ) 
             = K_P \left ( 1 + \frac {T_D s}{1 + \alpha T_D s} \right )
    
    **Differenzengleichung**
    
    .. math::
    
        u_k = \frac 1 {1 + \tau_D'} \left[ \tau_D' u_{k-1} + (K_P [1 + \tau_D'] + K_D') e_k  - (K_P \tau_D' + K_D') e_{k-1} \right]

    mit 
    
    .. math::
    
        K_D' = \frac {K_D}{T_s},\ \tau_D' = \frac {\tau_D}{T_s} = \alpha T_D'

    .. note::   Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem 
                .execute() neu berechnet werden.

    
    :param  fv_Kp:  
    :param  fv_Kd:
    :param  fv_alpha:
    :param  fv_Ts:
    
    :param  fv_e:   Eingangssignal *Regeldifferenz*
    :param  fv_u:   Ausgangssignal *Stellgröße*

    **History**
    
    -   2016-04-19: Created.

    """

    @staticmethod
    def KrTd( Kp, Kd, alpha):
        """
        """
        Kr = Kp
        Td = Kd/Kp
        return Kr, Td
    
    
    @staticmethod
    def KpKd( Kr, Td, alpha):
        """
        """
        Kp = Kr
        Kd = Kr*Td
        return Kp, Kd
    
    
    def __init__( self, *, id, fv_Kp, fv_Kd, fv_alpha, fv_Ts, fv_e, fv_u):
        super().__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)

        self.__fv_Kp = fv_Kp 
        self.__fv_Kd = fv_Kp 
        self.__fv_alpha = fv_alpha
        
        self.__e_ = [ 0] * 2
        self.__u_ = [ 0] * 2
        
        self.configure()        
        return
    
    def configure( self):
        pass
    
    def execute( self):
        """Berechnung der Differenzengleichung.
        """
        ##  Ein paar Abkürzungen
        #
        Kp = self.__fv_Kp.value()
        Kd = self.__fv_Kd.value()
        alpha = self.__fv_alpha.value()
        Ts = self.fv_Ts().value()
        
        e_ = self.__e_
        u_ = self.__u_
        
        ##  Signal-Listen vorbereiten
        #
        e_[-1] = e_[ 0]
        u_[-1] = u_[ 0]
    
        ##  Eingangssignal lesen
        #
        e_[0] = self.fv_e().value()

        ##  Ausführung des effektiven Algorithmus
        #
        Kds = Kd/Ts
        tauD = alpha*Kd/Kp
        tauDs = tauD/Ts
        
        u_[0] = tauDs * u_[-1] + (Kp + (1 + alpha) * Kds) * e_[0] - (1 + alpha) * Kds * e_[-1]
        u_[0] /= (1 + tauDs)
        
        ##  Ausgangssignal schreiben, dabei evtl. die Bounds berücksichtigen
        #
        self.fv_u().value( u_[ 0])

        return

    def info( self):
        return "%s (%s): Kp = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(), 
                   self.__class__.__name__, 
                   self.__fv_Kp.value(), 
                   self.__fv_Kd.value(), 
                   self.__fv_alpha.value(), 
                   self.fv_Ts().value()
               )
    
    def name( self):
        return "PDT1"
    
    def reset( self):
        self.__fv_e.value( 0.0)
        self.__fv_u.value( 0.0)
        
        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3
        return
    

class EulerBw4PIDT1(_AlgorithmDigital):
    
    r"""PID real (= PID + T1), Euler rückwärts, EINE Übertragungsfunktion.
    
    :param  FlexEntity  fv_Kp:      Proportional gain.
    :param  FlexEntity  fv_Ki:      Integral gain.
    :param  FlexEntity  fv_Kd:      Differential gain.
    :param  FlexEntity  fv_alpha:   :math:`\alpha = \frac {\tau_D}{T_D},\ \ \ T_D = \frac {K_D}{K_P}`
                                    As :math:`\tau_D` is needed for the calculations, the representation 
                                    :math:`\tau_D = \alpha \frac {K_d}{K_p}` fits much better.        
    :param  FlexEntity  fv_Ts:      Sample time.
    :param  FlexEntity  fv_e:       Regeldifferenz.
    :param  FlexVarbl   fv_u:       Stellgröße.
    
    .. note:: 
        
        Keine Windup-Prävention! Grund: Der Integrator ist nicht separat zugänglich, 
        weil nur EINE Übertragungsfunktion realisiert ist.

    .. note::
        Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem 
        .execute() neu berechnet werden.
    """
            
    @staticmethod
    def KpKiKd( Kr, Tr1, Tr2, alpha):
        r"""Transform works as follows (cal'ed with *Sage 5.3*, simplified manually):
        
        :math:`K_I = K_R`
        
        :math:`K_D = K_R \frac {T_{R1} T_{R2}}{1 + \alpha}`
        
        :math:`K_P = K_R \frac {T_{R1} + T_{R2}}{2} \pm \frac {K_R} {2} \sqrt{2 \frac {1 - \alpha}{1 + \alpha} T_{R1} T_{R2} + (1 + \alpha)(T_{R1}^2 + T_{R2}^2)}`
        """
        Ki = Kr
        Kd = Kr*Tr1*Tr2/(1 + alpha)
        Kp = Kr*(Tr1 + Tr2)/2. + Kr/2*math.sqrt( 2*(1 - alpha)/(1 + alpha)*Tr1*Tr2 + (1 + alpha)*(Tr1*Tr1 + Tr2*Tr2))
        return Kp, Ki, Kd
            
    @staticmethod
    def KrTr1Tr2( Kp, Ki, Kd, alpha):
        r"""Transform works as follows (cal'ed with *Sage 5.3*, simplified manually):
        
        :math:`\underline{K_P \ne,\ K_I \ne 0,\ K_D \ne 0}`:
        
            :math:`K_R = K_I`
            
            :math:`T_{R1} = \frac {\alpha K_D}{2 K_P} + \frac {K_P}{2 K_I}\pm \frac 1 {2 K_I K_P} \sqrt{(\alpha K_D K_I)^2 - 2 (\alpha + 2) K_D K_I K_P^2 + K_P^4}`
            
            :math:`T_{R2} = \frac {2 (\alpha +1) K_D K_P}{\alpha K_D K_I + K_P^2 \pm \sqrt{(\alpha K_D K_I)^2 - 2 \alpha K_D K_I K_P^2 - 4 K_D K_I K_P^2 + K_P^4}}~\\`
            
        :math:`\underline{K_P \ne,\ K_I \ne 0,\ K_D = 0}`:
        
            :math:`K_R = K_I`
            
            :math:`T_{R1} = \frac {K_P}{K_I}`
            
            :math:`T_{R2} = 0~\\`
            
        :math:`\underline{K_P \ne,\ K_I = 0,\ K_D \ne 0}`:
        
            :math:`K_R = K_P`
            
            :math:`T_{R1} = (1 + \alpha)\frac {K_D}{K_P}`
            
            :math:`T_{R2} = 0~\\`
        
        :math:`\underline{K_P \ne,\ K_I = K_D = 0}`:
        
            :math:`K_R = K_P`
            
            :math:`T_{R1} = T_{R2} = 0~\\`
        
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

                
    def __init__( self, *, id, fv_Kp, fv_Ki, fv_Kd, fv_alpha, fv_Ts, fv_e, fv_u):
        super().__init__( id=id,fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        assert isinstance( fv_e, flex.Variable)
        assert isinstance( fv_u, flex._VariableMixinMonitor)
        fv_u.reg_tau4s_on_limit_violated( self._tau4s_on_saturation_)
        
        self.__fv_Kp = fv_Kp
        self.__fv_Ki = fv_Ki
        self.__fv_Kd = fv_Kd
        self.__fv_alpha = fv_alpha
        
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3
        
        self.configure()
        return
    
    def configure( self):
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
        Kp = self.__fv_Kp.value()
        Ki = self.__fv_Ki.value()
        Kd = self.__fv_Kd.value()
        alpha = self.__fv_alpha.value()
        Ts = self.fv_Ts().value()
        
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
        e_[0] = self.__fv_e.value()

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
        self.__fv_u.value( u)
        return

    def info( self):
        return "%s (%s): Kp = %.3f; Ki = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(), 
                   self.__class__.__name__, 
                   self.__fv_Kp.value(), 
                   self.__fv_Ki.value(), 
                   self.__fv_Kd.value(), 
                   self.__fv_alpha.value(), 
                   self.fv_Ts().value()
               )
    
    def name( self):
        return "PIDT1"
    
    def reset( self):
        self.__fv_e.value( 0)
        self.__fv_u.value( 0)
        
        self.__e_ = [ 0] * 3
        self.__u_ = [ 0] * 3
        return

    def _tau4s_on_saturation_( self, pc):
        """Stellgrößenlimit überschritten.
        
        .. todo::
            In dieser Methode kann nun der Integrator dealtiviert werden.
        """
        return
    
    
class EulerBw4PIDT1p(_AlgorithmDigital):
    
    r"""PID real (= PID + T1), Euler rückwärts, 3 Übertragungsfunktionen **parallel**, die das Gesamtverhalten realisieren.
    
    :param  FlexVarblHL fv_Kp:
    :param  FlexVarblHL fv_Ki:
    :param  FlexVarblHL fv_Kd:
    :param  FlexVarblHL fv_alpha:
    :param  FlexVarblHL fv_Ts:
                
    Hier lässt sich das Windup des Integrators verhindern, indem der Integrator 
    auf Pause geschaltet wird, wenn **die Summe der drei Einzelsignale** die 
    Stellgrenzen überschreiten. 
    
    Art der Windup-Prävention:
        Abschalten des Integrators.

    .. note::
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
    
    
    def __init__( self, *, id, fv_Kp, fv_Ki, fv_Kd, fv_alpha, fv_Ts, fv_e, fv_u):
        super().__init__( id=id,fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        fv_uP = flex.Variable( value=0.0);    assert not fv_uP.is_clipping()
        fv_uDT1 = flex.Variable( value=0.0);  assert not fv_uDT1.is_clipping()
        fv_uI = flex.Variable( value=0.0);    assert not fv_uI.is_clipping()
        self.__algorithmP = EulerBw4P( id=u"%s: P" % id, fv_Kp=fv_Kp, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uP)
        self.__algorithmDT1 = EulerBw4DT1( id=u"%s: DT1" % id, fv_Kd=fv_Kd, fv_alpha=fv_alpha, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uDT1)
        self.__algorithmI = EulerBw4I( id=u"%s: I" % id, fv_Ki=fv_Ki, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_uI)
        
        fv_u.reg_tau4s_on_limit_violated( lambda *arg: self.__algorithmI.pause())
        fv_u.reg_tau4s_on_limit_unviolated( lambda *arg: self.__algorithmI.resume())

        ##  Die folgenden Attribute sind nur wegen .info() notwendig
        #
        self.__fv_Kp = fv_Kp
        self.__fv_Ki = fv_Ki
        self.__fv_Kd = fv_Kd
        self.__fv_alpha = fv_alpha

        return

    def configure( self):
        pass
    
    def fv_Kp( self):
        return self.__algorithmP.fv_Kp()
    
    def fv_Ki( self):
        return self.__algorithmI.fv_Ki()
    
    def fv_Kd( self):
        return self.__algorithmDT1.fv_Kd()
    
    def fv_alpha( self):
        return self.__algorithmDT1.fv_alpha()

    def info( self):
        return "%s (%s): Kp = %.3f; Ki = %.3f; Kd = %.3f; alpha = %.3f; Ts = %.3f;" \
               % (
                   self.name(), 
                   self.__class__.__name__, 
                   self.__fv_Kp.value(), 
                   self.__fv_Ki.value(), 
                   self.__fv_Kd.value(), 
                   self.__fv_alpha.value(), 
                   self.fv_Ts().value()
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
        e = self.__fv_e.value()
        
        ### Alle Elemente mit Fehlersignal versorgen
        #
        self.__algorithmP.fv_e().value( e)
        self.__algorithmDT1.fv_e().value( e)
        self.__algorithmI.fv_e().value( e)

        ### Alle Elemente ausführen
        #
        self.__algorithmP.execute()
        self.__algorithmDT1.execute()
        self.__algorithmI.execute()

        ### Alle Elemente "abernten"
        #
        uP = self.__algorithmP.fv_u().value()
        uDT = self.__algorithmDT1.fv_u().value()        
        uI = self.__algorithmI.fv_u().value()

        ### Ausgangssignal = Summe der einzelnen Ausgangssignale
        #
        u = uP + uDT + uI
        self.fv_u().value( u)
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
    
    
class EulerBw4PT1(_AlgorithmDigital):
    
    """PT1
    
    ::
    
                    K
                      1
        PT1(s) = ---------
                 1 + T  s
                      1

    :param              id:     Unique identification of the element.
        
    :param  FlexVarblHL fv_K1:  Gain.
        
    :param  FlexVarblHL fv_T1:  Time constant.
        
    :param  FlexVarblHL fv_Ts:  Sample time.
      
    .. note::      
        fv_Ts darf während der Laufzeit geändert werden, weil die Koeffzienten in jedem 
        .execute() neu berechnet werden.
    """
    
    def __init__( self, *, id, fv_K1, fv_T1, fv_Ts, fv_e, fv_u):
        _AlgorithmDigital.__init__( id=id, fv_Ts=fv_Ts, fv_e=fv_e, fv_u=fv_u)
        
        self.__fv_K1 = fv_K1
        self.__fv_T1 = fv_T1
        self.__fv_e = fv_e
        self.__fv_u = fv_u
        
        self.__u_ = [ 0, 0]
        self.__y_ = [ 0, 0]
        return
    
    def fv_K1( self):
        """Streckenverstärkung.
        """
        return self.__fv_K1
    
    def fv_Ks( self):
        """Streckenverstärkung.
        """
        return self.__fv_K1    
    
    def fv_T1( self):
        """Zeitkonstante.
        """
        return self.__fv_T1
    
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
        K1 = self.__fv_K1.value()
        T1 = self.__fv_T1.value()
        Ts = self.fv_Ts().value()
        
        ##  Werte aus letztem Schritt übernehmen
        #
        u_[-1] = u_[0]
        y_[-1] = y_[0]
        
        ##  Input lesen
        #
        u_[0] = self.__fv_e.value()
        
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
        self.__fv_u.value( y)
        
        return
        
    def info( self):
        """
        """
        return "PT1 (Euler bw)"
    
    def reset( self):
        """
        """
        self.__fv_e.value( 0)
        self.__fv_u.value( 0)
        self.__u_ = [ 0, 0]
        self.__y_ = [ 0, 0]
        return

