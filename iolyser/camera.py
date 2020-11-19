import numpy
import cv2
import sys
import os
import time

from TouchStyle import *


#camera section
WIDTH=320
HEIGHT=(WIDTH*3/4)
FPS=10

class CamWidget(QWidget):
    def __init__(self, parent=None):

        super(CamWidget, self).__init__(parent)
        # initialize camera
        self.lastTimer = 0
        self.openCam()

        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/FPS)



        qsp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        qsp.setHeightForWidth(True)
        self.setSizePolicy(qsp)

    def openCam(self):
        if time.time() - self.lastTimer > 1:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(3,WIDTH)
                self.cap.set(4,HEIGHT)
                self.cap.set(5,FPS)
            self.lastTimer = time.time()
        else:
            pass

    def sizeHint(self):
        return QSize(WIDTH, HEIGHT)

    def heightForWidth(self,w):
        return w*3/4

    def grab(self):
        self.frame = self.cap.read()[1]

        # expand/shrink to widget size
        wsize = (self.size().width(), self.size().height())
        self.cvImage = cv2.resize(self.frame, wsize)

        height, width, byteValue = self.cvImage.shape
        bytes_per_line = byteValue * width

        cv2.cvtColor(self.cvImage, cv2.COLOR_BGR2RGB, self.cvImage)
        self.mQImage = QImage(self.cvImage, width, height,
                              bytes_per_line, QImage.Format_RGB888)


    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)

        if self.cap == None or not self.cap.isOpened():
            if round(self.lastTimer) %2:
                text = "No camera.\n Scanning..."
            else:
                text = "No camera.\n Scanning.  "

            painter.drawText(QRect(QPoint(0,0), self.size()), Qt.AlignCenter, text)
            self.openCam()
        else:
            try:
                self.grab()
                painter.drawImage(0,0,self.mQImage)
            except cv2.error:
                self.cap = None
                self.lastTimer = time.time()

        painter.end()
