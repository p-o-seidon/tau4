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


import os
import socket
from subprocess import check_output
import threading
import time

from tau4.sweng import PublisherChannel


class MyIpAddress:
    
    """Eigene IP-Adresse herausfinden.
    
    \note
        Das funktioniert nur, wenn eine Internet-Verbindung besteht!
    """

    def __init__( self):
        s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect( ('google.com', 0))
            self.__ipaddr = s.getsockname()[ 0]

        except socket.gaierror:
            self.__ipaddr = "-1.-1.-1.-1"
            
        return

    def as_str( self):
        return str( self.__ipaddr)

    def as_numbers( self):
        return map( int, self.as_str().split( "."))


class Pinger(threading.Thread):

    def __init__( self, ipaddr, portnbr, timeout):
        super().__init__()

        self.__ipaddr = ipaddr
        self.__portnbr = portnbr
        self.__timeout = timeout

        self.__success = False

        self._tau4p_socket_found = PublisherChannel.Synch( self)
        return

    def ipaddr( self):
        return self.__ipaddr

    def portnbr( self):
        return self.__portnbr

    def run_deprecated( self):
        self.__success = False
        print( "Ping '(%s, %d)'. " % (self.__ipaddr, self.__portnbr))
        handle = os.popen( "ping -c 1 -W 1 " + self.__ipaddr)
        lines = handle.readlines()
        for j, line in enumerate( lines):
            if line.find( "1 packets transmitted, 1 received, 0% packet loss") >= 0:
                self.__success = True

        handle.close()

        if self.__success:
            sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout( self.__timeout)
            try:
                print( "Try to conect to '(%s, %d)'. " % (self.__ipaddr, self.__portnbr))
                sock.connect( (self.__ipaddr, self.__portnbr))
                print( "####### S u c c e s s ,   w e   a r e   c o n n e c t e d   to (%s, %s). socket.getpeername() == %s. ########" % (self.__ipaddr, self.__portnbr, sock.getpeername()))

            except (ConnectionRefusedError, OSError) as e:
                print( "ERROR: '%s' (ipaddr = '%s', portnbr = '%d')!" % (e, self.__ipaddr, self.__portnbr))
                sock.close()
                self.__success = False

            finally:
                sock.close()

        return self.__success

    def run( self):
        self.__success = False

        sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout( self.__timeout)
        try:
            print( "Try to connect to '(%s, %d)'. " % (self.__ipaddr, self.__portnbr))
            sock.connect( (self.__ipaddr, self.__portnbr))
            print( "####### S u c c e s s ,   w e   a r e   c o n n e c t e d   to (%s, %s). socket.getpeername() == %s. ########" % (self.__ipaddr, self.__portnbr, sock.getpeername()))
            self.__success = True

        except (ConnectionRefusedError, OSError) as e:
            print( "ERROR: '%s' (ipaddr = '%s', portnbr = '%d')!" % (e, self.__ipaddr, self.__portnbr))
            self.__success = False

        finally:
            sock.close()

        if self.__success:
            self._tau4p_socket_found()

        return self.__success

    def success( self):
        return self.__success


class SocketFinder:

    def __init__( self, ipaddrtuple, portnbr):
        self.__ipaddritems = ipaddrtuple
        self.__portnbr = portnbr

        self.__socketaddritems = (None, None)
        self.__timeout_socket = 5
        self.__is_socket_found = False
        return

    def find( self):
        self.__socketaddritems = (None, None)
        threads = []
        for hostnbr in range( 1, 256):
            if self.__is_socket_found:
                break

            ipaddr = "%d.%d.%d.%d" % (self.__ipaddritems[ :3] + (hostnbr,))
            pinger = Pinger( ipaddr, self.__portnbr, self.__timeout_socket)
            pinger._tau4p_socket_found += self._tau4s_socket_found_
            threads.append( pinger)
            threads[ -1].start()
            print( "Thread '%d' started. " % len( threads))
            time.sleep( 0.100)

        for i, thread in enumerate( threads):
            thread.join()
            print( "Thread '%d' joined. " % i)

        return self.__socketaddritems

    def socket( self, ipaddr, portnbr):
        sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout( self.__timeout_socket)
        try:
            print( "Try to conect to '(%s, %d)'. " % (ipaddr, portnbr))
            sock.connect( (ipaddr, portnbr))
            print( "####### S u c c e s s ,   w e   a r e   c o n n e c t e d   to (%s, %s). socket.getpeername() == %s. ########" % (ipaddr, portnbr, sock.getpeername()))
            return sock

        except (ConnectionRefusedError, OSError) as e:
            print( "ERROR: '%s' (ipaddr = '%s', portnbr = '%d')!" % (e, self.__ipaddr, self.__portnbr))
            sock.close()

        return None

    def socketaddritems( self):
        return self.__socketaddritems

    def _tau4s_socket_found_( self, tau4pc):
        self.__is_socket_found = True
        self.__socketaddritems = (tau4pc.client().ipaddr(), tau4pc.client().portnbr())
        return


def main():
    socketfinder = SocketFinder( (10, 0, 0, 0), 1962)
    socketfinder.find()
    ipaddr, portnbr = socketfinder.socketaddritems()
    if ipaddr:
        print( "Socket found at '%s'. " % ipaddr)
        sock = socketfinder.socket( ipaddr, portnbr)
        sock.close()

    else:
        print( "Socket not found. ")

    return


if __name__ == "__main__":
    main()
    input( "Press any key to exit...")

