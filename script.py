#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import ftrobopy
import numpy
import cv2
import zbarlight

from TxtStyle import *
from PIL import Image

WIDTH=240
HEIGHT=(WIDTH*3/4)
FPS=10

CAM_DEV = os.environ.get('FTC_CAM')
if CAM_DEV == None: CAM_DEV = 0
else:               CAM_DEV = int(CAM_DEV)

class CamWidget(QWidget):
    def __init__(self, parent=None):

        super(CamWidget, self).__init__(parent)

        # initialize camera
        self.cap = cv2.VideoCapture(CAM_DEV)
        if self.cap.isOpened():
            self.cap.set(3,WIDTH)
            self.cap.set(4,HEIGHT)
            self.cap.set(5,FPS)

        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/FPS)

        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def sizeHint(self):
        return QSize(WIDTH,HEIGHT)

    def heightForWidth(self,w):
        return w*3/4

    def grab(self):
        self.frame = self.cap.read()[1]

        # expand/shrink to widget size
        wsize = (self.size().width(), self.size().height())
        self.cvImage = cv2.resize(self.frame, wsize)

        height, width, byteValue = self.cvImage.shape
        bytes_per_line = byteValue * width

        # hsv to rgb
        cv2.cvtColor(self.cvImage, cv2.COLOR_BGR2RGB, self.cvImage)
        self.mQImage = QImage(self.cvImage, width, height,
                              bytes_per_line, QImage.Format_RGB888)

        cv_img = cv2.cvtColor(self.cvImage, cv2.COLOR_RGB2GRAY)
        raw = Image.fromarray(cv_img)

        # extract results and display first code found
        codes = zbarlight.scan_codes('qrcode', raw)
        if codes:
            self.emit(SIGNAL('code(QString)'), codes[0].decode("UTF-8"))

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)

        if not self.cap.isOpened():
            painter.drawText(QRect(QPoint(0,0), self.size()),
                             Qt.AlignCenter, "No camera");
        else:
            self.grab()
            painter.drawImage(0,0,self.mQImage)

        painter.end()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        # create the empty main window
        w = TxtWindow("Fertigung")
        try:
            self.txt = ftrobopy.ftrobopy("localhost", 65000) # connect to TXT's IO controller
        except:
            self.txt = None                                  # set TXT to "None" of connection failed

        if not self.txt:
            # display error of TXT could no be connected
            err_msg = QLabel("Error connecting IO server")   # create the error message label
            err_msg.setWordWrap(True)                        # allow it to wrap over several lines
            err_msg.setAlignment(Qt.AlignCenter)             # center it horizontally
            w.setCentralWidget(err_msg)                      # attach it to the main output area
        else:
            # initialization went fine. So the main gui
            # is being drawn
            button = QPushButton("Switch Ausgang 1")         # create a button labeled "Toggle O1"
            button.clicked.connect(self.on_button_clicked)   # connect button to event handler
            w.setCentralWidget(button)                       # attach it to the main output area

            self.cw = CamWidget()

            vbox = QVBoxLayout()
            vbox.setSpacing(0)
            vbox.setContentsMargins(0,0,0,0)

            vbox.addWidget(self.cw)
            vbox.addStretch()

            self.lbl = QLabel()
            self.lbl.setObjectName("smalllabel")
            self.lbl.setAlignment(Qt.AlignCenter)
            self.lbl.setWordWrap(True)
            vbox.addWidget(self.lbl)


            self.connect( self.cw, SIGNAL("code(QString)"),
                          self.on_code_detected )



        # configure all TXT outputs to normal mode
            M = [ self.txt.C_OUTPUT, self.txt.C_OUTPUT, self.txt.C_OUTPUT, self.txt.C_OUTPUT ]
            I = [ (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ),
                  (self.txt.C_SWITCH, self.txt.C_DIGITAL ) ]
            self.txt.setConfig(M, I)
            self.txt.updateConfig()

        # initially switch light on
            self.light_on = True                             # remember that the light is on
            self.txt.setPwm(0,0)                           # set PWm to 512 (full on)

        w.show()
        self.exec_()

    # an event handler for our button (called a "slot" in qt)
    # it will be called whenever the user clicks the button
    def on_button_clicked(self):
        self.light_on = not self.light_on                   # change state
        if self.light_on:                                   # set output accordingly
            self.txt.setPwm(0,512)                          # PWN=512 means full on
        else:
            self.txt.setPwm(0,0)                            # PWM=0 means off
    def on_code_detected(self,str):
        self.lbl.setText(str)
#        self.hide_timer.start(1000)  # hide after 1 second

    def on_code_timeout(self):
        self.lbl.setText("")

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
