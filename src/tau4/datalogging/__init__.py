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

import abc

from collections import deque
from datetime import datetime
import logging
import logging.config
from logging import handlers
import sys

from tau4 import ThisName
from tau4.time import Timer2
from tau4.oop import overrides, Singleton

import threading
import time


class LoggingLevel:

    _CRITICAL = logging.CRITICAL
    _FATAL = logging.CRITICAL
    _ERROR = logging.ERROR
    _WARNING = logging.WARNING
    _WARN = logging.WARNING
    _INFO = logging.INFO
    _DEBUG = logging.DEBUG
    _NOTSET = logging.NOTSET


class _Event(metaclass=abc.ABCMeta):

    """Basisklasse für Events.

    :param  reason:
            Ursache des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   reason: (int, str)

    :param  source:
            Quelle des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   source: (int, str)

    Das Verschicken eines Events erfolgt über Methode von SysEventLog() und UsrEventLog().
    """

    _SEVERITY_INFO, _SEVERITY_WARNING, _SEVERITY_ERROR = range( 3)


    def __init__( self, reason, source, severity):
        self.__reason = reason
        self.__source = source
        self.__severity = severity

        self.__time_stamp = time.time()
        return

    def __str__( self):
        severity = ["INFO", "WARNING", "ERROR"][ self.__severity]
        severity = " ".join( list( severity))
        return u"%s:\n\tReason: %s\n\tSource: %s" % (severity, self.__reason, self.__source)

    def reason_number( self):
        """Nummer der Alarmursache. """
        return self.__reason[ 0]

    def reason_text( self):
        """Text der Alarmursache. """
        return self.__reason[ 1]

    def severity_is_info( self):
        """
        """
        return self.__severity == self._SEVERITY_INFO

    def severity_is_warning( self):
        """
        """
        return self.__severity == self._SEVERITY_WARNING

    def severity_is_error( self):
        """
        """
        return self.__severity == self._SEVERITY_ERROR

    @abc.abstractmethod
    def severity_text( self):
        pass

    def source_number( self):
        """Nummer der Alarmquelle. """
        return self.__source[ 0]

    def source_text( self):
        """Text, der die Alarmquelle beschreibt. """
        return self.__source[ 1]

    def time_formatted( self):
        """Timestamp in einem lesbaren Format. """
        dt = datetime.fromtimestamp( self.timestamp())
        return dt.strftime( "%Y-%m-%d | %H:%M:%S")
#        try:
#            dt = datetime.fromtimestamp( self.timestamp())
#            return dt.strftime( "%Y-%m-%d | %H:%M:%S")
#
#        except TypeError, e:
#            return "EXCEPTION 'TypeError: %s', caused probably by timestamp = '%s'. " % ( str( e), self.timestamp())

    def timestamp( self):
        """Zeitpunkt, zu dem der Alarm entstanden ist. """
        return self.__time_stamp


class _ErrorEvent(_Event):

    """Error.

    :param  reason:
            Ursache des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   reason: (int, str)

    :param  source:
            Quelle des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   source: (int, str)

    Usage
        ::

            tau4logging.UsrEventLog().log_error( "Probleme mit Laufwerk", "Laufwerk A:")
            tau4logging.SysEventLog().log_error( "Wasser in Laufwerk", "Laufwerk A:")

    Das Verschicken eines Events erfolgt über Methode von SysEventLog() und UsrEventLog().
    """

    def __init__( self, reason, source):
        _Event.__init__( self, reason, source, self._SEVERITY_ERROR)
        return

    def severity_text( self):
        return "ERROR"


class _InfoEvent(_Event):

    """Info.

    :param  reason:
            Ursache des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   reason: (int, str)

    :param  source:
            Quelle des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   source: (int, str)

    Modul/File:
        alerting/.py.

    **Usage**:

        ::

            tbus.Emit(
                defs4tbus.Event4Alarm(
                    _alarm=alerting.AlarmInfo(
                        reason=(0, "Changed opera mode to MANU"),
                        source=(0, self.__class__.__name__)
                    )
                )
            )
    """

    def __init__( self, reason, source):
        _Event.__init__( self, reason, source, self._SEVERITY_INFO)
        return

    def severity_text( self):
        return "INFO"


class DequeWithLock(deque):

    def __init__( self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.__lock = threading.Lock()
        return

    def __getitem__( self, *args):
        with self.__lock:
            return super().__getitem__( *args)

    def __iter__( self, *args):
        with self.__lock:
            return super().__iter__( *args)

    def append( self, elem):
        with self.__lock:
            super().append( elem)

        return self

    def clear( self):
        with self.__lock:
            super().clear()

        return self

    def extend( self, elems):
        with self.__lock:
            super().extend( elems)

        return self


class _WarningEvent(_Event):

    """Warning.

    :param  reason:
            Ursache des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   reason: (int, str)

    :param  source:
            Quelle des Alarms.
            Hier sollten die entsprechenden, im Modul
            definierten Konstanten benützt werden.

    :type   source: (int, str)

    Modul/File:
        alerting/.py.

    **Usage**:

        ::

            tbus.Emit(
                defs4tbus.Event4Alarm(
                    _alarm=alerting.AlarmWarning(
                        reason=(0, "Changed opera mode to ERROR"),
                        source=(0, self.__class__.__name__)
                    )
                )
            )
    """

    def __init__( self, reason, source):
        _Event.__init__( self, reason, source, self._SEVERITY_WARNING)
        return

    def severity_text( self):
        return "WARNING"


class _EventLog(metaclass=Singleton):

    """Basisklasse für die beiden Event-Logs ``SysEventLog`` und ``UsrEventLog``.
    """


    def __init__( self, id4usr):
        from tau4.sweng import PublisherChannel

        self.__id4usr = id4usr

        self.__tau4p_on_changes = PublisherChannel.Synch( self)

        self.__errors = DequeWithLock( maxlen=10000)
        self.__infos = DequeWithLock( maxlen=10000)
        self.__warnings = DequeWithLock( maxlen=10000)

        self.__events = []

        self.__is_errors_on = True
        self.__is_infos_on = True
        self.__is_warnings_on = True

        self.__lock = threading.RLock()
        return

    def clear( self):
        """
        """
        with self.__lock:
            self.__errors[:] = []
            self.__infos[:] = []
            self.__warnings[:] = []

            self._events_clear_()

        return self

    def errors_off( self):
        """
        """
        self.__is_errors_on = False
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def errors_on( self):
        """
        """
        self.__is_errors_on = True
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def event( self, i):
        """
        """
        with self.__lock:
            try:
                return self._events_()[ i]

            except IndentationError:
                return None

    def id4usr( self):
        return self.__id4usr

    def infos_off( self):
        """
        """
        self.__is_infos_on = False
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def infos_on( self):
        """
        """
        self.__is_infos_on = True
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def log_error( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        with self.__lock:
            event = _ErrorEvent( (reason_ident, reason_text), (source_ident, source_name))
            self.__errors.append( event)
            self._event_add_( event)
            print( str( event), file=sys.stderr)
            return self

    def log_info( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        with self.__lock:
            event = _InfoEvent( (reason_ident, reason_text), (source_ident, source_name))
            self.__infos.append( event)
            self._event_add_( event)
            return self

    def log_warning( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        with self.__lock:
            event = _WarningEvent( (reason_ident, reason_text), (source_ident, source_name))
            self.__warnings.append( event)
            self._event_add_( event)
            print( str( event), file=sys.stderr)
            return self

    def num_events( self):
        """
        """
        with self.__lock:
            return len( self._events_())

    def register_tau4s_on_changes( self, tau4s):
        """
        """
        self.__tau4p_on_changes += tau4s
        return self

    def store( self):
        try:
            f = open( self.id4usr() + ".txt", "wb")
            for event in self._events_():
                f.write( str( event))
                f.write( "\n")

            f.close()

        except (IOError, OSError) as e:
            pass

        return self

    def warnings_off( self):
        """
        """
        self.__is_warnings_on = False
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def warnings_on( self):
        """
        """
        self.__is_warnings_on = True
        with self.__lock:
            self._events_clear_()
                                            # Force recreation of events list
        return self

    def _event_add_( self, event):
        """
        """
        self.__events[:] = []
                                        # Das führt dazu, dass die Liste
                                        #   self.__events bei der nächsten
                                        #   Ausführung von self._events_()
                                        #   neu aufgebaut wird.
        self.__tau4p_on_changes()
        return self

    def _events_( self):
        """
        """
        if not self.__events:
            if self.__is_errors_on:
                self.__events.extend( self.__errors)
            if self.__is_infos_on:
                self.__events.extend( self.__infos)
            if self.__is_warnings_on:
                self.__events.extend( self.__warnings)

            self._events_sort_()

        return self.__events

    def _events_clear_( self):
        """
        """
        self.__events[:] = []
        self.__tau4p_on_changes()
        return self

    def _events_sort_( self):
        self.__events.sort( key=lambda event: event.timestamp())
        self.__events.reverse()
        return self


class SysEventLog(_EventLog):

    """
    """

    def __init__( self):
        _EventLog.__init__( self, "log-for-sys-events")
        return


class UsrEventLog(_EventLog):

    """
    """

    def __init__( self):
        _EventLog.__init__( self, "log-for-usr-events")
        return

    def log_error( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        _EventLog.log_error( self, reason_text, source_name, reason_ident, source_ident)
        SysEventLog().log_error( reason_text, source_name, reason_ident, source_ident)
        return self

    def log_info( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        _EventLog.log_info( self, reason_text, source_name, reason_ident, source_ident)
        SysEventLog().log_info( reason_text, source_name, reason_ident, source_ident)
        return self

    def log_warning( self, reason_text, source_name="n.a.", reason_ident=0, source_ident=0):
        """
        """
        _EventLog.log_warning( self, reason_text, source_name, reason_ident, source_ident)
        SysEventLog().log_warning( reason_text, source_name, reason_ident, source_ident)
        return self


def PyLogger( module_name, logging_level=logging.DEBUG, pathname=None):
    pathname = "log_" + module_name.replace( ".", "-") + ".log" if not pathname else pathname

    logger = logging.getLogger( module_name)
    hdlr = handlers.RotatingFileHandler( pathname, "a", 10000000, 100)
    formatter = logging.Formatter( "[%(asctime)s %(process)d %(thread)d %(levelname)10s %(name)40s] %(message)s")
    hdlr.setFormatter( formatter)
    logger.addHandler( hdlr)
    logger.setLevel( logging_level)
    return logger


class PyLoggers(metaclass=Singleton):

    def __init__( self):
        self.__loggers = {}
        return

    def logger_add( self, logger, key):
        self.__loggers[ key] = logger
        return

    def logger( self, key):
        return self.__loggers[ key]


def RootLoggerInit( appname, logginglevel):
    logger = logging.getLogger()
    logger.setLevel( logginglevel)
    hdlr = handlers.RotatingFileHandler( "./%s.log" % appname, "a", 10000000, 10)
    formatter = logging.Formatter( "%(asctime)s %(process)d %(thread)d %(levelname)10s %(message)s")
    hdlr.setFormatter( formatter)
    hdlr.setLevel( logginglevel)
    logger.addHandler( hdlr)
    return

def RootLogger() -> logging.RootLogger:
    return logging.getLogger()


import multiprocessing as mp
Logging = None


class DefaultListenerLoggerConfiger:

    """
    """

    def __init__( self, pathname_filehandler_rotating, logginglevel):
        self.__pathname_filehandler_rotating = pathname_filehandler_rotating
        self.__logginglevel = logginglevel
        return

    def __call__( self):
        config_listener = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'detailed': {
                    'class': 'logging.Formatter',
###                    'format': '[%(asctime)s] %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
##                    'format': '[%(asctime)s] Logger.%(name)-15s %(levelname)-8s %(threadName)-10s in %(processName)-10s %(funcName)s(): %(message)s'
#                    'format': '[%(asctime)s] %(levelname)-8s %(processName)s.%(threadName)s.???.%(funcName)s(): %(message)s'
                    'format': '[%(asctime)s] %(levelname)-8s %(processName)s.%(threadName)s.%(module)s.py(%(lineno)d): %(message)s'
                },
                'basic': {
                    'class': 'logging.Formatter',
                    'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
#                    'formatter': 'basic',
                    'formatter': 'detailed',
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'filename': self.__pathname_filehandler_rotating,
                    'mode': 'a',
                    'maxBytes': 10000000,
                    'backupCount': 10,
                    'formatter': 'detailed',
                },
                'foofile': {
                    'class': 'logging.FileHandler',
                    'filename': 'mplog-foo.log',
                    'mode': 'w',
                    'formatter': 'detailed',
                },
                'errors': {
                    'class': 'logging.FileHandler',
                    'filename': 'mplog-errors.log',
                    'mode': 'w',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                },
            },
            'loggers': {
                'foo': {
                    'handlers': ['foofile']
                }
            },
            'root': {
                'level': self.__logginglevel,
                'handlers': ['console', 'file', 'errors']
            },
        }
        logging.config.dictConfig( config_listener)
        return


class DefaultMainProcessLoggerConfiger:

    """Configurator fpr the Main Process, that is main().
    """

    def __init__( self, logginglevel, pathname_filehandler_rotating):
        self.__logginglevel = logginglevel
        self.__pathname_filehandler_rotating = pathname_filehandler_rotating
        return

    def __call__( self):
        self.execute()
        return
    
    def execute( self):
        config_initial = {
           'version': 1,
           'formatters': {
               'detailed': {
                   'class': 'logging.Formatter',
                   'format': '[[%(asctime)s]] Logger.%(name)-15s %(levelname)-8s %(processName)-10s %(threadName)-10s %(funcName)s(): %(message)s'
               } # Wird nicht wirksam, was mir locgisch erescheint. Aber warum wird er dann hier definiert?
           },
           'handlers': {
               'console': {
                   'class': 'logging.StreamHandler',
#                   'level': 'INFO',
                   'level': self.__logginglevel,
               },
           },
           'root': {
               'level': 'DEBUG',
               'handlers': ['console']
           },
        }
        logging.config.dictConfig( config_initial)
        return
    
    def logginglevel( self):
        return self.__logginglevel
    
    def pathname_filehandler_rotating( self):
        return self.__pathname_filehandler_rotating


class DefaultProcessLoggerConfiger:

    """
    """

    def __init__( self, queue, logginglevel):
        self.__queue = queue
        self.__logginglevel = logginglevel
        return

    def __call__( self):
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': 'logging.handlers.QueueHandler',
                    'queue': self.__queue,
                },
            },
            'root': {
                'level': self.__logginglevel,
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig( config_worker)
        return


class ListenerProcess(mp.Process):

    """Prozess, der an der Queue wartet, in die alle Prozesse loggen.
    """

    def __init__( self, configer, queue, stopevent):
        super().__init__()

        self.__configer = configer
        self.__queue = queue
        self.__stopevent = stopevent

        self.__configer()
        return

    @overrides( mp.Process)
    def run( self):
        listener = logging.handlers.QueueListener( self.__queue, LoggingEventHandler())
        listener.start()
#        if os.name == 'posix':
#            # On POSIX, the setup logger will have been configured in the
#            # parent process, but should have been disabled following the
#            # dictConfig call.
#            # On Windows, since fork isn't used, the setup logger won't
#            # exist in the child, so it would be created and the message
#            # would appear - hence the "if posix" clause.
#            logger = logging.getLogger('setup')
#            logger.critical('Should not appear, because of disabled logger ...')

        self.__stopevent.wait()
        listener.stop()
        return


class LoggingEventHandler:

    def handle( self, record):
        logger = logging.getLogger( record.name)
#        record.processName = '%s (for %s)' % (mp.current_process().name, record.processName)
        logger.handle( record)
        return


class _Logging:

    """

    \note
        Aus Gründen der Performance keine SUbclass des Singleton
    """

    def __init__( self, configer: DefaultMainProcessLoggerConfiger):
        configer.execute()
        
        self.__logginglevel = configer.logginglevel()

        logger = logging.getLogger( 'setup')
        logger.info( "Main logging configured.")

        self.__queue = mp.Queue( -1)
        self.__stopevent = mp.Event()
        self.__listener = ListenerProcess( DefaultListenerLoggerConfiger( configer.pathname_filehandler_rotating(), self.__logginglevel), self.__queue, self.__stopevent)
        self.__listener.start()
        logger.info( "Listener process started.")

        return

    def __call__( self):
        return self

    def logger( self):
        """DEPRECATED, simply use logging.
        """
        return logging.getLogger( mp.current_process().name)
    
    def logginglevel( self):
        return self.__logginglevel

    def processloggerqueue( self):
        return self.__queue


def Init( configer: DefaultMainProcessLoggerConfiger):
    global Logging
    Logging = _Logging( configer)
    return
