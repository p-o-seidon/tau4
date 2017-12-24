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

import abc

from tau4 import ThisName
from tau4.data import flex
from tau4.datalogging import UsrEventLog
from tau4.sweng import PublisherChannel, Singleton


class SM:

    """State Machine.

    An app can have more than one state machine.
    But be aware, that state machine states are singletons and you have to decide at
    runtime, which state machine they belong to!

    Usage:

        self.__sm = _SMStates4ROP().sm()

        class _SMStates4ROP:

            ############################################################################
            ### States As Local Classes
            #
            class _SMState(SMState):

                def close( self):
                    super().close()

                    UsrEventLog().log_info( "Leaving state '%s'. " % self.name(), ThisName( self))
                    return

                def exitcondition_ROPDISABLE_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_ENABLE().value() == 0

                def exitcondition_ROPENABLE_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_ENABLE().value() == 1

                def exitcondition_ROPSTART_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_START().value() == 1

                def exitcondition_ROPSTOP_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_STOP().value() == 1

                def exitcondition_ROPPAUSE_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_PAUSE().value() == 1

                def exitcondition_ROPRESUME_IS_REQUESTED( self):
                    return iIOs().idinps_rop().idinp_ROP_RESUME().value() == 1

                def robot( self):
                    return self.common().robot()

                def world( self):
                    return self.common().world()


            class ROPSMAvoiding(_SMState):

                def execute( self):
                    alpha = iIOs().iainps_rop().iainp_ROP_ALPHA().value()
                    if degrees( alpha) > 90:
                                                    # Obstacle approaches from the rhs
                        self.robot().uck_100( v_100=75, omega_100=-50)

                    elif degrees( alpha) < 90:
                                                    # Obstacle approaches from the lhs
                        self.robot().uck_100( v_100=75, omega_100=+50)

                    self.robot().execute()
                    return

                def exitcondition_ROPSTOP_IS_REQUESTED( self):
                    b = iIOs().idinps_rop().idinp_ROP_STOP().value() != 0
                    if b:
                        this_name = ThisName( self)
                        UsrEventLog().log_warning( this_name, this_name)

                    return b

                def exitcondition_NO_OBSTACLE_DETECTED( self):
                    b = iIOs().idinps_rop().idinp_ROP_ALPHA_DEVIATES().value() == 0
                    return b

                def exitcondition_VERY_CLOSE_OBSTACLE_DETECTED( self):
                    b = False
                    if iIOs().idinps_rop().idinp_ROP_ALPHA_DEVIATES().value() != 0:
                        if not 85 <= degrees( iIOs().iainps_rop().iainp_ROP_ALPHA().value()) <= 105:
                            b = True

                    return b


            class ROPSMEscaping(_SMState):

                def execute( self):
                    alpha = iIOs().iainps_rop().iainp_ROP_ALPHA().value()
                    if degrees( alpha) > 90:
                                                    # Obstacle approaches from the rhs
                        self.robot().uck_100( v_100=25, omega_100=-100)

                    elif degrees( alpha) < 90:
                                                    # Obstacle approaches from the lhs
                        self.robot().uck_100( v_100=25, omega_100=+100)

                    self.robot().execute()
                    return


            class ROPSMIdle(_SMState):

                def close( self):
                    super().close()

                    iIOs().idouts_rop().idout_ROP_IS_ENABLED().value( 1)
                                                    # Wir zeigen an, dass wir enabled-t sind.
                    return

                def exitcondition_IS_READY( self):
                    '''We may change over to READY.

                    Conditions:

                    -   Batteries ready
                    -   GPS ready
                    '''
                    is_batteries_ready = True
                    is_navi_ready = len( self.world().robots()) and self.common().robot().sensors().navis( 0).status().is_ok()
                    is_rop_enabled = iIOs().idinps_rop().idinp_ROP_ENABLE().value() == 1
                                                    # PLC enable-t uns
                    if False not in (is_navi_ready, is_rop_enabled, is_batteries_ready):
                        UsrEventLog().log_info( "Batteries are ok and NavSys and ROP are ready. ", ThisName( self))

                    return is_navi_ready and is_rop_enabled

                def open( self, *args):
                    super().open( *args)

                    #self.robot().uck_100( v_100=0, omega_100=0)
                    #self.robot().execute()
                    # ##### Das Environment ist noch nicht aufgesetzt. 2DO: Wie können wir das sicherstellen?
                    return

            class ROPSMGoaling(_SMState):

                def close( self):
                    super().close()

                def exitcondition_NAVI_IS_NOT_READY( self):
                    b = iIOs().idinps_rop().idinp_ROP_IS_NAVIDATA_OK().value() == 0
                                                    # PLC sends us a 1, if it is receiving
                                                    #   valid data, and a 0 otherwise
                    if b:
                        this_name = ThisName( self)
                        UsrEventLog().log_warning( this_name, this_name)

                    return b


            class ROPSMLoading(_SMState):

                def exitcondition_MAP_IS_LOADED( self):
                    return True # 2DO


            class ROPSMPausing(_SMState):

                def close( self):
                    super().close()

                    if self.__is_stop_requested:
                        self.robot().stop()
                        return

                    if self.__is_resume_requested:
                        self.robot().stop()
                        return

                    if self.__is_diable_requested:
                        self.robot().stop()
                        iIOs().idouts_rop().idout_ROP_IS_ENABLED().value( 0)
                                                        # Wir zeigen an, dass wir disablet sind.
                        return

                    return

                def execute( self):
                    self.robot().uck_100( v_100=0, omega_100=0)
                    self.robot().execute()
                    return

                def exitcondition_STOP_IS_REQUESTED( self):
                    self.__is_stop_requested = iIOs().idinps_rop().idinp_ROP_STOP().value() # S T O P -Button
                    return self.__is_stop_requested

                def exitcondition_RESUME_IS_REQUESTED( self):
                    self.__is_resume_requested = iIOs().idinps_rop().idinp_ROP_RESUME().value() # R E S U M E -Button
                    return self.__is_resume_requested

                def exitcondition_DISABLE_IS_REQUESTED( self):
                    self.__is_diable_requested = iIOs().idinps_rop().idinp_ROP_ENABLE().value() == 0    # D I S A B L E -Button
                                                    # PLC disablet uns
                    return self.__is_diable_requested

                def open( self, *args):
                    super().open( *args)

                    self.__is_diable_requested = False
                    self.__is_resume_requested = False
                    self.__is_stop_requested = False
                    return


            class ROPSMReady(_SMState):

                def close( self):
                    super().close()

                    if self.__is_ropstart_requested:
                        self.robot().start()
                        return

                    if self.__is_ropdisable_requested:
                        iIOs().idouts_rop().idout_ROP_IS_ENABLED().value( 0)
                                                        # Wir zeigen an, dass wir disablet sind.
                        return

                    if self.__is_ropenable_requested:
                        iIOs().idouts_rop().idout_ROP_IS_ENABLED().value( 1)
                                                        # Wir zeigen an, dass wir enabled-t sind.
                    return

                def execute( self):
                    self.robot().uck_100( v_100=0, omega_100=0)
                    self.robot().execute()
                                                    # Robot ausführen: Behaviours und Chassis.
                                                    #   Die Sensoren werden im SensorReader
                                                    #   gelesen.
                    return

                def exitcondition_ROPSTART_IS_REQUESTED( self):
                    self.__is_ropstart_requested = super().exitcondition_ROPSTART_IS_REQUESTED()
                    if self.__is_ropstart_requested:
                        this_name = ThisName( self)
                        UsrEventLog().log_info( this_name, this_name)

                    return self.__is_ropstart_requested

                def exitcondition_ROPDISABLE_IS_REQUESTED( self):
                    self.__is_ropdisable_requested = super().exitcondition_ROPDISABLE_IS_REQUESTED()
                    if self.__is_ropdisable_requested:
                        this_name = ThisName( self)
                        UsrEventLog().log_info( this_name, this_name)

                    return self.__is_ropdisable_requested

                def exitcondition_ROPENABLE_IS_REQUESTED( self):
                    self.__is_ropenable_requested = super().exitcondition_ROPENABLE_IS_REQUESTED()
                    if self.__is_ropenable_requested:
                        this_name = ThisName( self)
                        UsrEventLog().log_warning( this_name, this_name)

                    return self.__is_ropenable_requested

                def open( self, *args):
                    super().open( *args)

                    self.__is_ropdisable_requested = False
                    self.__is_ropenable_requested = False
                    self.__is_ropstart_requested = False
                    return


            class ROPSMWaitingForNavi(_SMState):

                def close( self):
                    super().close()

                    if self.__is_stop_requested:
                        self.robot().stop()
                        return

                    if self.__is_resume_requested:
                        self.robot().stop()
                        return

                    if self.__is_diable_requested:
                        self.robot().stop()
                        iIOs().idouts_rop().idout_ROP_IS_ENABLED().value( 0)
                                                        # Wir zeigen an, dass wir disablet sind.
                        return

                    return

                def execute( self):
                    self.robot().uck_100( v_100=0, omega_100=0)
                    self.robot().execute()
                    return

                def exitcondition_STOP_IS_REQUESTED( self):
                    self.__is_stop_requested = iIOs().idinps_rop().idinp_ROP_STOP().value() # S T O P -Button
                    return self.__is_stop_requested

                def exitcondition_NAVI_IS_READY( self):
                    b = iIOs().idinps_rop().idinp_ROP_IS_NAVIDATA_OK().value() == 1
                                                    # PLC sends us a 1, if it is receiving
                                                    #   valid data, and a 0 otherwise
                    if b:
                        this_name = ThisName( self)
                        UsrEventLog().log_warning( this_name, this_name)

                    return b

                def exitcondition_DISABLE_IS_REQUESTED( self):
                    self.__is_diable_requested = iIOs().idinps_rop().idinp_ROP_ENABLE().value() == 0    # D I S A B L E -Button
                                                    # PLC disablet uns
                    return self.__is_diable_requested

                def open( self, *args):
                    super().open( *args)

                    self.__is_diable_requested = False
                    self.__is_resume_requested = False
                    self.__is_stop_requested = False
                    return


            class ROPSMNone(_SMState):

                def is_none( self):
                    False


            ############################################################################
            ### Attributes And Methods
            #
            def __init__( self):
                self.__sm = SM( self.table(), self.ROPSMIdle(), _Common())
                return

            def sm( self):
                return self.__sm

            def table( self):
                d = {\
                        self.ROPSMAvoiding(): \
                            {\
                                self.ROPSMAvoiding().exitcondition_NO_OBSTACLE_DETECTED: self.ROPSMGoaling(),
                                self.ROPSMAvoiding().exitcondition_VERY_CLOSE_OBSTACLE_DETECTED: self.ROPSMEscaping(),
                                self.ROPSMAvoiding().exitcondition_ROPDISABLE_IS_REQUESTED: self.ROPSMIdle(),
                                self.ROPSMAvoiding().exitcondition_ROPSTOP_IS_REQUESTED: self.ROPSMReady(),
                            },

                        self.ROPSMIdle(): \
                            {\
                                self.ROPSMIdle().exitcondition_IS_READY: self.ROPSMReady(),
                            },

                        self.ROPSMReady(): \
                            {\
                                self.ROPSMReady().exitcondition_ROPSTART_IS_REQUESTED: self.ROPSMLoading(),
                                self.ROPSMReady().exitcondition_ROPDISABLE_IS_REQUESTED: self.ROPSMIdle(),
                            },

                        self.ROPSMLoading(): \
                            {\
                                self.ROPSMLoading().exitcondition_MAP_IS_LOADED: self.ROPSMGoaling(),
                            },

                        self.ROPSMGoaling(): \
                            {\
                                self.ROPSMGoaling().exitcondition_ROPSTOP_IS_REQUESTED: self.ROPSMReady(),
                                self.ROPSMGoaling().exitcondition_ROPDISABLE_IS_REQUESTED: self.ROPSMIdle(),
                                self.ROPSMGoaling().exitcondition_ROPPAUSE_IS_REQUESTED: self.ROPSMPausing(),

                                self.ROPSMGoaling().exitcondition_NAVI_IS_NOT_READY: self.ROPSMWaitingForNavi(),
                            },

                        self.ROPSMPausing(): \
                            {\
                                self.ROPSMPausing().exitcondition_ROPSTOP_IS_REQUESTED: self.ROPSMReady(),
                                self.ROPSMPausing().exitcondition_ROPDISABLE_IS_REQUESTED: self.ROPSMIdle(),
                                self.ROPSMPausing().exitcondition_ROPRESUME_IS_REQUESTED: self.ROPSMGoaling(),
                            },

                        self.ROPSMWaitingForNavi(): \
                            {\
                                self.ROPSMWaitingForNavi().exitcondition_ROPSTOP_IS_REQUESTED: self.ROPSMReady(),
                                self.ROPSMWaitingForNavi().exitcondition_ROPDISABLE_IS_REQUESTED: self.ROPSMIdle(),

                                self.ROPSMWaitingForNavi().exitcondition_NAVI_IS_READY: self.ROPSMGoaling(),
                            },

                        self.ROPSMNone(): \
                            {\
                                self.ROPSMNone().is_none: self.ROPSMNone(),
                            },

                    }
                return d

    """

    def __init__( self, sms_table, sms_initial, sms_common_data):
        self.__sms_table = sms_table
        self.__sms_current = sms_initial
        self.__sms_common_data = sms_common_data

        self.__sms_current.open( self.__sms_common_data)

        self.__fv_smstate_name = flex.VariableDeMo( id=-1, value="???", label="SM State")
        self.__fv_smstate_number = flex.VariableDeMo( id=-1, value=-1, label="SM State")

        self.__is_finished = False
        return

    def common( self):
        return self.__sms_common_data

    def execute( self):
        if self.is_finished():
            UsrEventLog.log_error( "Cannot execute a state machine that has finished already!", ThisName( self))
            return

        self.__sms_current.execute()
        self.__fv_smstate_name.value( self.__sms_current.name())
        self.__fv_smstate_number.value( self.__sms_current.value())
        try:
            for exitconditionmethod, sms_next in self.__sms_table[ self.__sms_current]:
                if exitconditionmethod():
                    self.__sms_current.close()
                                                    # Close this state
                    self.__sms_current = sms_next
                                                    # Get the next state and set
                                                    #   it as the (new) current one
                    if self.__sms_current is None:
                        self.__is_finished = True
                        break

                    self.__sms_current.open( self.__sms_common_data)
                                                    # Open the new current state
                    break

        except KeyError as e:
            UsrEventLog().log_error( e + ". You forgot to enter this state in your state table!", ThisName( self))

        return self

    def fv_smstatename_current( self):
        return self.__fv_smstate_name
    fv_smstate_name = fv_smstatename_current # DEPRECATED

    def fv_smstatenumber_current( self):
        return self.__fv_smstate_number

    def is_finished( self):
        return self.__is_finished

    def smstate_current( self):
        return self.__sms_current


class SMState(metaclass=Singleton):

    def __init__( self):
        self._tau4p_on_close = PublisherChannel.Synch( self)
                                        # Called before closing the state
        self._tau4p_on_execute = PublisherChannel.Synch( self)
                                        # Called before executing the state
        self._tau4p_on_opened = PublisherChannel.Synch( self)
                                        # Called after opening the state
        self.__common = None
        self.__is_open = False
        return

    def close( self):
        """Close the state.

        May be overridden, but doesn't need to be.
        """
        assert self.__is_open
        self._tau4p_on_close()
        self.__is_open = False
        return

    def common( self):
        return self.__common

    @abc.abstractmethod
    def execute( self):
        self._tau4p_on_execute()
        assert self.__is_open

    def name( self):
        return self.__class__.__name__

    def open( self, common):
        """Open the state.

        May be overridden, but doesn't need to be.

        In case, the overriding method needs to call this class' method!
        """
        self.__common = common
        self.__is_open = True
        self._tau4p_on_opened()
        return self

    @abc.abstractmethod
    def value( self):
        raise NotImplementedError()

