#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import os
import time
from TxtStyle import *



class FtcGuiApplication(TxtApplication):
	def __init__(self, args):
		TxtApplication.__init__(self, args)

        

if __name__ == "__main__":
	FtcGuiApplication(sys.argv)
