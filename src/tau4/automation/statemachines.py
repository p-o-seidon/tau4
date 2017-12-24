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

from tau4 import Object
from tau4 import oop
from tau4 import ThisName
from tau4 import threads


class StatemachineStandard(Object):

    """State Machine.
    """

    class State(Object, metaclass=abc.ABCMeta):

        """State of the State Machine.

        This is an abstract class, i.e. you have to inherit from it and to
        override some methods then.
        """

        @classmethod
        def Name( cls):
            """The name of the state.
            """
            return cls.__name__

        class ExitPoint:

            """An exit point of a state.

            A state may have more than one exit point.

            **Parameters**
                meth_condition : callabale
                    The exit point's target state is jumped to, if
                    meth_condition() returns True.

                class_targetstate : State
                    The new state the state machine executes next time, if
                    meth_condition() was True.
            """

            def __init__( self, meth_condition, class_targetstate):
                assert callable( meth_condition)
                assert issubclass( class_targetstate, StatemachineStandard.State)

                self.__meth_condition = meth_condition
                self.__class_targetstate = class_targetstate
                return

            def condition( self):
                """The exit point's exit condition.
                """
                return self.__meth_condition()

            def condition_name( self):
                return self.__meth_condition.__name__

            def targetstate( self, states):
                """The exit point's target state, which is executed the next time, if the exit point's exit condition was True.
                """
                return states[ self.__class_targetstate.Name()]

            def targetstate_class( self):
                """The exit point's target-state class.

                See :py:meth:`targetstate`.
                """
                return self.__class_targetstate


        def __init__( self, exitpoints):
            self.__exitpoints = exitpoints

            self.__statemachine = None
            return

        @abc.abstractmethod
        def close( self, udata=None):
            """This method is called by the state machine on the current state before a new state is executed.
            """
            pass

        @abc.abstractmethod
        def execute( self, udata=None):
            """The state's payload method.
            """
            pass

        def exitpoints( self):
            """The state's exit points.

            See :py:class:`ExitPoint`.
            """
            return self.__exitpoints

        def name( self):
            return self.Name()

        @abc.abstractmethod
        def number( self):
            """Zahl, die den State identifiziert (pure virtual).
            """
            pass

        @abc.abstractmethod
        def open( self, udata=None):
            """This method is called by the state machine on the current state after a state change.
            """
            pass

        def _statemachine_( self, statemachine):
            self.__statemachine = statemachine
            return self

        def statemachine( self):
            return self.__statemachine


    def __init__( self, *, id, class_state_1):
        super().__init__( id=id)

        self.__tau4p_on_state_changed = oop.PublisherChannel.Synch( self)

        self.__states = {}
        self.__exitpoint = None

        self.__state = self._add_state_( class_state_1)

        self._create_states_( self.__state)

        self._assert_sanity_()

        self.__is_call_to_open_needed = True
        return

    def _add_state_( self, state_class):
        if not state_class.Name() in self.__states:
            state = state_class()
            state._statemachine_( self)
            self.__states[ state.Name()] = state
            #print( ThisName( self) + "(): Added state '%s'. " % state_class.Name())
            return state

        return None

    def _assert_sanity_( self):
        for state in self.__states.values():
            assert state.statemachine() is self

        return

    def _create_states_( self, state):
        for exitpoint in state.exitpoints():
            state_class = exitpoint.targetstate_class()
            state = self._add_state_( state_class)
            if state:
                self._create_states_( state)

        return

    def execute( self):
        """The :py:class:`Cycler` 's payload.
        """
        if self.__is_call_to_open_needed:
            self.__state.open()
            self.__is_call_to_open_needed = False

        self.__state.execute()
                                        # Execute the current state.
        for exitpoint in self.__state.exitpoints():
                                        # For each exit point of the current
                                        #   state: Check it's exit conditions.
            if exitpoint.condition():
                                            # An exit condition of the current
                                            #   state is True.
                self.exitpoint( exitpoint)
                                                # Reason why we leave the current state
                self.__state.close()
                                                # Cleanup the current state.
                self.__state = exitpoint.targetstate( self.__states)
                                                # Switch the current state. Exceution
                                                #   of the new current state happens
                                                #   in the next run.
                self.__is_call_to_open_needed = True
                self.__tau4p_on_state_changed()
                                                # At this point all states are closed!
                break

        return

    def exitpoint( self, arg: State.ExitPoint=None):
        if arg is None:
            return self.__exitpoint

        self.__exitpoint = arg
        return self

    def reg_tau4s_on_state_changed( self, tau4s):
        self.__tau4p_on_state_changed += tau4s
        return self

    def state_name( self):
        return self.__state.name()

    def state_number( self):
        return self.__state.number()


class StatemachineStandardThreaded(StatemachineStandard, threads.Cycler):

    def __init__( self, class_state_1):
        StatemachineStandard.__init__( self, class_state_1)
        threads.Cycler.__init__( self, cycletime=0.001, udata=None)
        return

    def _run_( self, udata):
        self.execute()
        return
