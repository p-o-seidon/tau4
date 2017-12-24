#   -*- coding: utf8 -*-
#
#   Copyright (C) by DATEC Datentechnik GmbH, A-6890 LUSTENAU, 1998 - 2016
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


"""\package app4pgt Leistungsschau tau4.
"""

import abc
import sys

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import \
    QApplication, \
    QLabel, \
    QPushButton, \
    QTabWidget, \
    QToolTip, \
    QWidget
from PyQt5.QtGui import QFont


class BaseTeachPoints:

    def __init__( self):
        self.__org_coords = []
        self.__x_coords = []
        self.__xy_coords = []

        self.__pathname = "./cteacher.baseteachpoints.dat"
        return

    def restore( self):
        try:
            with open( self.__pathname, "r") as f:
                for line in f:
                    self.__org_coords = eval( line.strip())
                    self.__x_coords = eval( line.strip())
                    self.__xy_coords = eval( line.strip())

        except FileNotFoundError as e:
            pass

        return self

    def store( self):
        with open( self.__pathname, "w") as f:
            f.write( self.__org_coords + "\n")
            f.write( self.__x_coords + "\n")
            f.write( self.__xy_coords)

        return

    def org_coords( self, coords=None):
        if coords is None:
            return self.__org_coords

        self.__org_coords[ :] = coords
        return self

    def x_coords( self, coords=None):
        if coords is None:
            return self.__x_coords

        self.__x_coords[ :] = coords
        return self

    def xy_coords( self, coords=None):
        if coords is None:
            return self.__xy_coords

        self.__xy_coords[ :] = coords
        return self


class ButtonIds:

    _BID_BASE = "_BID_BASE"
    _BID_CONTOUR = "_BID_CONTOUR"
    _BID_OK = "_BID_OK"
    _BID_CANCEL = "_BID_CANCEL"
    _BID_TRANSFER = "_BID_TRANSFER"


class StateNames:

    _IDLE = "idle"

    _BASE_TEACHING_AWAITS_ORG = "_BASE_TEACHING_AWAITS_ORG"
    _BASE_TEACHING_AWAITS_X = "_BASE_TEACHING_AWAITS_X"
    _BASE_TEACHING_AWAITS_XY = "_BASE_TEACHING_AWAITS_XY"


class MainWindow(qtw.QMainWindow):

    def __init__( self):
        super().__init__()

        self.__statename = StateNames._IDLE

        self.__baseteachpoints = BaseTeachPoints().restore()
        self.__navsys = None

        self.__button_id = None

        self._build_()
        return

    def _build_( self):
        QToolTip.setFont( QFont('SansSerif', 10))

        self.__texts = [ "Ready."]

        ### Layout
        #
        window = qtw.QWidget()
        layout_main = qtw.QVBoxLayout()
        self.setCentralWidget( window)
        window.setLayout( layout_main)

        ### Statusbar
        #
        self.__clock = _Clock( self)
        self.__statusbar = qtw.QStatusBar()
        self.setStatusBar( self.__statusbar)
        self.__statusbar.addWidget( qtw.QLabel( self.__clock.caption4gui()))
        self.__statusbar.addWidget( self.__clock)

        ### Text Output
        #
        self.__qtTE = qtTE = qtw.QTextEdit( self)
        self.__qtTE.setText( self.__texts[ 0])
        layout_main.addWidget( qtTE)

        ### Buttons
        #
        qtB = qtw.QPushButton( "BASE", self)
        qtB.clicked.connect( self._on_button_BASE_)
        layout_main.addWidget( qtB)

        qtB = qtw.QPushButton( "CONTOUR", self)
        qtB.clicked.connect( self._on_button_CONTOUR_)
        layout_main.addWidget( qtB)

        qtB = qtw.QPushButton( "CANCEL", self)
        qtB.clicked.connect( self._on_button_CANCEL_)
        layout_main.addWidget( qtB)

        qtB = qtw.QPushButton( "OK", self)
        qtB.clicked.connect( self._on_button_OK_)
        layout_main.addWidget( qtB)

        qtB = qtw.QPushButton( "TRANSFER", self)
        qtB.clicked.connect( self._on_button_TRANSFER_)
        layout_main.addWidget( qtB)
        return

    def clock( self):
        return self.__clock

    def _handle_button_( self, buttonid):
        if self.__statename == StateNames._IDLE:
            if buttonid == ButtonIds._BID_BASE:
                self.__texts.append( "BASE pressed. Go to the origin of the new base and press OK!")
                self.__qtTE.setText( "\n".join( self.__texts))

                self.__statename = StateNames._BASE_TEACHING_AWAITS_ORG

        elif self.__statename == StateNames._BASE_TEACHING_AWAITS_ORG:
            if buttonid == ButtonIds._BID_OK:
                x, y, z = self.__navsys.actuals().wP()
                self.__baseteachpoints.org_coords( (x, y, z))

                self.__texts.append( "ORG prog'ed. Go to a point on the x-axis of the new base and press OK. ")
                self.__qtTE.setText( "\n".join( self.__texts))

                self.__statename = StateNames._BASE_TEACHING_AWAITS_X

        elif self.__statename == StateNames._BASE_TEACHING_AWAITS_X:
            if buttonid == ButtonIds._BID_OK:
                x, y, z = self.__navsys.actuals().wP()
                self.__baseteachpoints.x_coords( (x, y, z))

                self.__texts.append( "X prog'ed. Got to a point in the xy-plane of the new base and press OK. ")
                self.__qtTE.setText( "\n".join( self.__texts))

                self.__statename = StateNames._BASE_TEACHING_AWAITS_XY

        elif self.__statename == StateNames._BASE_TEACHING_AWAITS_XY:
            if buttonid == ButtonIds._BID_OK:
                x, y, z = self.__navsys.actuals().wP()
                self.__baseteachpoints.xy_coords( (x, y, z))

                self.__baseteachpoints.store()

                self.__texts.append( "XY prog'ed, BASE prog'ing finished. ")
                self.__texts.append( "Ready. ")
                self.__qtTE.setText( "\n".join( self.__texts))

                self.__statename = StateNames._IDLE

            elif buttonid == ButtonIds._BID_CANCEL:
                self.__texts.append( "Teaching new base cancelled. ")
                self.__texts.append( "Ready. ")
                self.__qtTE.setText( "\n".join( self.__texts))

                self.__statename = StateNames._IDLE
        return

    def _on_button_BASE_( self):
        """Start des Teachens der BASE.
        """
        self._handle_button_( ButtonIds._BID_BASE)
        return

    def _on_button_CONTOUR_( self):
        self._handle_button_( ButtonIds._BID_CONTOUR)
        return

    def _on_button_CANCEL_( self):
        self._handle_button_( ButtonIds._BID_CANCEL)
        return

    def _on_button_OK_( self):
        self._handle_button_( ButtonIds._BID_OK)
        return

    def _on_button_TRANSFER_( self):
        self._handle_button_( ButtonIds._BID_TRANSFER)
        return


class _Clock(qtw.QLabel):

    qS_on_2400 = qtc.pyqtSignal()


    def __init__( self, parent):
        super().__init__( parent)

        self.__timer = qtc.QBasicTimer()
        self.__timer.start( 1000, self)

#        self.__date = IssueDate.Today()
        return

    def caption4gui( self):
        return "Actual time: "

    def timerEvent( self, qE):
        qT = qtc.QTime.currentTime()
        self.setText( qT.toString( "hh:mm:ss"))
#        is_2400 = IssueDate.Today() > self.__date
#        if is_2400:
#            self.__date = IssueDate.Today()
#            self.qS_on_2400.emit()

        return


def main():
    app = QApplication( sys.argv)
    w = MainWindow()
    w.show()
    sys.exit( app.exec_())
    return

if __name__ == '__main__':
    main()
