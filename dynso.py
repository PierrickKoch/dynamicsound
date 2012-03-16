#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py

1. take webcam image
2. cut image in 2 (left / right)
3. detect moves
    * get a coef for left and one for right (%)
4. set speakers volume 
    * left_volume *= left_moves_coef
    * right_volum *= right_moves_coef

once this is ok, to it with 4 chanel, cut image NW, NE, SW, SE
find 5.1 ALSA bindings ? a way to tune separatly 4 audio channel ?

sudo apt-get install python-opencv python-alsaaudio

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/basic_structures.html#iplimage
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
  * http://pyalsaaudio.sourceforge.net/libalsaaudio.html#alsaaudio.Mixer.setvolume
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * libsdl ? ossaudiodev.openmixer ? ncurses
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#namedwindow
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#waitkey
  * https://www.google.com/search?q=usb+5.1&tbm=shop
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://en.wikipedia.org/wiki/MP3_Surround
  * http://en.wikipedia.org/wiki/Surround_sound
  * http://wiki.python.org/moin/PythonInMusic

API usage: 0.0 < weight < 1.0
DynamicSound.weight = {
    "up": {
        "left": 0,
        "right": 0
    },
    "down": {
        "left": 0,
        "right": 0
    }
}

"""

import os
import wx
import sys
import time
import cv2.cv as cv
import alsaaudio

class DynamicSound(object):
    weight = {
        "up": {
            "left": 0,
            "right": 0
        },
        "down": {
            "left": 0,
            "right": 0
        }
    }
    def __init__(self):
        self._image = None # IPL Image
        self._mixer = alsaaudio.Mixer() # 'Master', 0
        self._volume = self._mixer.getvolume()
        # CV / V4L Camera ID
        self._capture = cv.CaptureFromCAM(-1)
    def __del__(self):
        # close stuff ?
        self._mixer.close()

    def setvolume(self, volume, channel=alsaaudio.MIXER_CHANNEL_ALL):
        self._mixer.setvolume(volume, channel)

    def capture(self):
        img = cv.QueryFrame(self._capture)
        imgsize = (img.width, img.height)
        imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
        cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
        velx = cv.CreateImage(imgsize, cv.IPL_DEPTH_32F, 1)
        vely = cv.CreateImage(imgsize, cv.IPL_DEPTH_32F, 1)
        winsize = (5, 5)
        cv.WaitKey(10)
        while 1:
            imgprev = imgcurr
            img = cv.QueryFrame(self._capture)
            imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
            cv.CalcOpticalFlowLK(imgprev, imgcurr, winsize, velx, vely)
            cv.ShowImage("x", velx)
            cv.ShowImage("y", vely)
            key = cv.WaitKey(10) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == wx.WXK_ESCAPE:
                break

def main(args):
    import this # The Zen of Python, by Tim Peters

    if "h" in ''.join(args):
        sys.stderr.write(__doc__)
        return 1

    dynso = DynamicSound()
    print("get ready! ( WIP :)")
    dynso.setvolume(10)
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))