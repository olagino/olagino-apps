#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import ftrobopy
import numpy
import cv2
import zbarlight
import time

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
                             Qt.AlignCenter, "No camera")
        else:
            self.grab()
            painter.drawImage(0,0,self.mQImage)

        painter.end()

class FtcGuiApplication(TxtApplication):
    def __init__(self, args):
        TxtApplication.__init__(self, args)

        #init Variables

        self.code = 0
        # create the empty main window
        w = TxtWindow("Fertigung")
        try:
            self.txt = ftrobopy.ftrobopy("localhost", 65000) # connect to TXT's IO controller
        except:
            self.txt = None                                  # set TXT to "None" of connection failed

        vbox = QVBoxLayout()
        if not self.txt:
            # display error of TXT could no be connected
            err_msg = QLabel("Error connecting IO server")   # create the error message label
            err_msg.setWordWrap(True)                        # allow it to wrap over several lines
            err_msg.setAlignment(Qt.AlignCenter)             # center it horizontally
            vbox.addWidget(err_msg)                      # attach it to the main output area
        else:
            # initialization went fine. So the main gui
            # is being drawn
            button = QPushButton("Neue Box")         # create a button labeled "Toggle O1"
            button.clicked.connect(self.new_box_clicked)   # connect button to event handler
            vbox.addWidget(button)                       # attach it to the main output area

            self.cw = CamWidget()

            vbox.addWidget(self.cw)

            self.lbl = QLabel()
            self.lbl.setObjectName("smalllabel")
            self.lbl.setAlignment(Qt.AlignCenter)
            self.lbl.setWordWrap(True)
            vbox.addWidget(self.lbl)

            self.connect( self.cw, SIGNAL("code(QString)"), self.on_code_detected )
            print(self.code)

        # configure all TXT outputs to normal mode
            M = [ self.txt.C_MOTOR, self.txt.C_MOTOR, self.txt.C_MOTOR, self.txt.C_OUTPUT ]
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
            #Init Motoren
            self.Motor1 = self.txt.motor(1) #Motor Schieber
            self.Motor2 = self.txt.motor(2) #Motor Arbeitstakte
            self.Motor3 = self.txt.motor(3) #Motor und Ventil 2, je nachdem, wo sich das Werkstück befindet.
            self.Compressor = self.txt.output(7) #Kompressor
            self.Valve1 = self.txt.output(8) #Ventil

            #Init des ersten Schiebers

        w.centralWidget.setLayout(vbox)
        w.show()
        #Modell zurücksetzen
        while not self.txt.input(1).state() == 1:
            self.Motor1.setSpeed(-512)
        self.Motor1.stop()
        while not self.txt.input(3).state() == 1:
            self.Motor2.setSpeed(-512)
        self.Motor2.stop()

        thread = QThread()

        #Timer für die Weitergabe
        self.code = 0
        timer = QTimer(self)
        timer.timeout.connect(self.wait_for_code)
        timer.start(10)
        #Timer Versuch 2
        self.loop_init = 0

        timer_2 = QTimer(self)
        timer.timeout.connect(self.wait_for_loop)
        timer.start(10)

        self.exec_()
        #erste Box ausgeben
        self.new_box_clicked()


    # an event handler for our button (called a "slot" in qt)
    # it will be called whenever the user clicks the button
    def new_box_clicked(self):
        self.loop_init = 1

    def wait_for_loop(self):
        if self.loop_init == 1:
            self.loop_init = 0
            self.code = 0
            #Luft ablassen
            self.Valve1.setLevel(0)
            #Schieber 1 vorfahren
            while not self.txt.input(2).state() == 1:
                self.Motor1.setSpeed(512)
            self.Motor1.stop()
            #Schieber 2 an Startposition fahren
            while not self.txt.input(3).state() == 1:
                self.Motor2.setSpeed(-512)
            self.Motor2.stop()
            self.Compressor.setLevel(512)
            time.sleep(0.1)
            self.Valve1.setLevel(512)
            time.sleep(0.3)
            self.Compressor.setLevel(0)
            #Schieber 1 zurückfahren
            while self.txt.input(1).state() == 0:
                self.Motor1.setSpeed(-512)
            self.Motor1.stop()

    def wait_for_code(self):
        if not self.code == 0:
            while self.txt.input(4).state() == 0:
                self.Motor2.setSpeed(512)
            self.Motor2.stop()
            self.code_temp = self.code
            self.code = 0

            time.sleep(1)

            #Metallkugel ausgeben
            self.Compressor.setLevel(512)
            self.Motor3.setSpeed(-512)
            time.sleep(1)
            self.Motor3.stop()
            self.Compressor.setLevel(0)

            while self.txt.input(5).state() == 1:
                self.Motor2.setSpeed(512)
            self.Motor2.stop()

            self.Valve1.setLevel(0)
            self.Motor2.setSpeed(-512)
            time.sleep(2)
            self.Motor2.stop()




    def on_code_detected(self,str):
        self.code = str
        self.lbl.setText(self.code)


    def on_code_timeout(self):
        self.lbl.setText("-/-")
        self.code = 0

if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
