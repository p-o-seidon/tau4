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
import inspect

import tau4
import threading


### Decorators
#
"""Template für Decortors mit Parametern

def outer_decorator(*outer_args,**outer_kwargs):
    def decorator(fn):
        def decorated(*args,**kwargs):
            do_something(*outer_args,**outer_kwargs)
            return fn(*args,**kwargs)
        return decorated
    return decorator
"""

def execute_cyclically( cycletime):
    def decorator( fun_org):
        import time
        period_of_execution = cycletime
        time_of_last_execution = 0
        def fun_new( *args, **kwargs):
            nonlocal time_of_last_execution
            t = time.time()
            if t - time_of_last_execution >= period_of_execution:
                q = fun_org( *args, **kwargs)
                time_of_last_execution = t

                return q

        return fun_new
    return decorator


def overrides( interface_class):
    """Decorator."""
    def overrider( method):
        assert( method.__name__ in dir( interface_class))
        return method

    return overrider


class _PublisherChannel:

    """Basisklasse für alle Arten von Channeln für Instanzen, die publishen wollen.

    Parameters:
        publisher:
            Objekt, das diese Klasse instanziert hat und publishen will.

    Usage:
        p = PublisherChannel( self)
        p()
                                        # Schickt die PublisherChannel-Instanz
                                        #   an alle Subscriber,
                                        #   die sich registriert haben.

    Usage:
        p = PublisherChannel( self)
        p( 42)
                                        # Schickt die PublisherChannel-Instanz und
                                        #   den Wert 42 an alle Subscriber,
                                        #   die sich registriert haben.

    History:
        2014-09-06:
            Created.

            Unterschied zu _Publisher: Nur Namensgebung. Obwohl: Es wäre
            denkbar, dass einmal nicht die PublisherChannel-Instanz an die Subscriber
            verschickt wird, sondern die Instanz des Publishers selbst.
    """

    __metaclass__ = abc.ABCMeta

    def __init__( self, publisher):
        self.__publisher = publisher

        self.__subscribers = []
        self.__lock = threading.Lock()
        return

    @abc.abstractmethod
    def __call__( self, *args, **kwargs):
        pass

    def __len__( self):
        return len( self.__subscribers)

    def client( self):
        """Same as ``parent()``: Returns hosting (= publishing) instance.
        """
        return self.__publisher

    def is_empty( self):
        """Prüft, ob Handler auszuführen sind.
        """
        return len( self.__subscribers) == 0

    @abc.abstractmethod
    def is_sync( self):
        """Prüft, ob es sich um einen a/synchronen Handler handelt.
        """
        pass

    def parent( self):
        """Returns hosting instance.
        """
        return self.__publisher

    def publisher( self):
        """Returns hosting instance, which may be considered being the actual publisher.
        """
        return self.__publisher

    def subscriber_count( self):
        return len( self.__subscribers)

    def subscriber_register( self, subscriber):
        """Neuen Subscriber hinzufügen.

        Parameters:
            subscriber:
                callable, der ausgeführt werden soll. Damit ist jedes Objekt ein
                Subscriber, das callable ist, d.s. Methode oder Objekte, die die
                Methode __call__() implementieren!

        Raises:
            ValueError wenn der Subscriber bereits bekannt ist.
        """
        with self.__lock:
            if self.__subscribers.count( subscriber):
                raise ValueError( "Subscriber already registered!")

            self.__subscribers.append( subscriber)

        return self

    def subscriber_is_registered( self, subscriber):
        """Subscriber schon registriert?
        """
        with self.__lock:
            return self.__subscribers.count( subscriber) > 0

    def subscriber_un_register( self, subscriber):
        """Subscriber entfernen.
        """
        with self.__lock:
            if not self.__subscribers.count( subscriber):
                raise ValueError( "Subscriber not registered!")

            self.__subscribers.remove( subscriber)

        return self

    def subscriber_un_register_all( self):
        """Alle Handler entfernen.
        """
        with self.__lock:
            self.__subscribers[:] = []

        return self

    def subscribers( self, copy=True):
        """Liefert (Kopie der) Subscribers.
        """
        if copy:
            with self.__lock:
                return self.__subscribers[ :]

        return self.__subscribers


class PublisherChannel:
    """Namespace.

    Usage:
        tau4pc = PublisherChannel.Synch( self)

    History:
        2014-09-06:
            Created.
    """

    class Synch(_PublisherChannel):

        """Siehe Base Class ``_Publisher``.
        """

        def __init__( self, parent):
            _PublisherChannel.__init__( self, parent)

            self.__is_safe_mode = False
            return

        def __call__( self, *args, **kwargs):
            """Ausführen aller registrierter Subscribers.

            Usage:
                Variante ohne Parent:
                    p = _Publisher( None)
                    p( 42)

                    Da hier ``None`` als ``parent`` übergeben worden ist, kann/muss der
                    Subscriber folgendermaßen definiert werden:
                        def _tau4s_on_data_( self, value):
                            return

                Variante mit Parent:
                    p = _Publisher( self)
                    p( 42)

                    Da hier das hostende Objekt als ``parent`` übergeben worden ist,
                    kann/muss der Subscriber folgendermaßen definiert werden:
                        def _tau4s_on_data_( self, tau4pc, value):
                            '''Subscriber.

                            Parameters:
                                tau4pc:
                                    PublisherChannel.

                                value:
                                    Additional arg sent by publisher.

                            Note:
                                You may get at the publishing object by a call to
                                ``tau4pc.publisher()``.
                            '''
                            return

            """
            ss = self.subscribers( copy=self.is_safe_mode())
            for s in ss:
                s( self, *args, **kwargs)

            return self

        def __iadd__( self, subscriber):
            """'Syntactic sugar', führt einfach subscriber_register() aus.
            """
            assert callable( subscriber)
            self.subscriber_register( subscriber)
            return self

        def __isub__( self, subscriber):
            """'Syntactic sugar', führt einfach subscriber_un_register() aus.
            """
            assert callable( subscriber)
            self.subscriber_un_register( subscriber)
            return self

        def is_sync( self):
            """
            """
            return True

        def is_safe_mode( self, arg=None):
            """Zugriff auf Subscribers über Zugriffsregelung per Lock?
            """
            if arg is None:
                return self.__is_safe_mode

            self.__is_safe_mode = arg
            return self


    class Async(_PublisherChannel):

        """Siehe Base Class ``_Publisher``.

        Note:
            D214:
                Work in progress: Kann noch nicht instanziert werden, weil die Implementierung
                der __call__-Methode noch fehlt.
        """

        def __init__( self, parent):
            _PublisherChannel.__init__( self, parent)

            self.__is_safe_mode = True
            return

        def __iadd__( self, subscriber):
            """'Syntactic sugar', führt einfach subscriber_register() aus.
            """
            assert callable( subscriber)
            self.subscriber_register( subscriber)
            return self

        def __isub__( self, subscriber):
            """'Syntactic sugar', führt einfach subscriber_un_register() aus.
            """
            assert callable( subscriber)
            self.subscriber_un_register( subscriber)
            return self

        def is_sync( self):
            """
            """
            return False

        def is_safe_mode( self, arg=None):
            """Zugriff auf Subscribers über Zugriffsregelung per Lock?
            """
            if arg is None:
                return self.__is_safe_mode

            self.__is_safe_mode = arg
            return self


class Singleton(type):

    """ Thread-safe Singleton, after http://timka.org/tech/2008/12/17/singleton-in-python/.

    We can make any existing class a singleton by simply adding the __metaclass__ attribute.
    The only Singleton instance is stored in the __instance__ class attribute.
    However, there's a problem here: Note that the __init__() method is called
    on every instantiation. This is normal behaviour of types in Python. When
    you instantiate a class, __new__() and __init__() are called internally.
    But we want the single instance to be created and initialized only once.
    The only(?) way to achieve this is metaclasses. In metaclass you can define
    what happens when you call its instances (which are also classes).

    Usage:
        \

        ::

            def test( self):
                 print

                 class MySingleton:
                     __metaclass__ = Singleton

                     def __init__( self, a, b):
                         self._a = a
                         self._b = b
                         return

                     def __eq__( self, other):
                         if not isinstance( other, MySingleton):
                             return False

                         return self._a == other._a and self._b == other._b

                     def __ne__( self, other):
                         return not self == other


                 s1 = MySingleton( 1, 2)
                 s2 = MySingleton( 3, 4)
                 self.assertTrue( s1 == s2)
                 self.assertTrue( s1 is s2)

                 return
    """

    def __new__( klass, name, bases, namespace):
        namespace.setdefault( '__lock__', threading.RLock())
                                        # Allocate lock, if not already allocated manually.
        namespace.setdefault( '__instance__', None)
                                        # Since we are already using __new__,
                                        #   we can also initialize the
                                        #   __instance__ attribute here.
        return super( Singleton, klass).__new__( klass, name, bases, namespace)

    ### Define the __call__ method in metaclass where __new__() and __init__()
    #   are called manually and only once.
    #
    def __call__( klass, *args, **kwargs):
        klass.__lock__.acquire()
        try:
                                        # __instance__ is now always initialized,
                                        #   so no need to use a default value.
            if klass.__instance__ is None:
                instance = klass.__new__( klass, *args, **kwargs)
                instance.__init__( *args, **kwargs)
                klass.__instance__ = instance
        finally:
            klass.__lock__.release()

        return klass.__instance__