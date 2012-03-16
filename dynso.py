#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py

http://creativecommons.org/licenses/by/2.0/

1. take webcam image
2. cut image in 2 (left / right)
3. detect moves
    * get a coef for left and one for right (%)
4. set speakers volume 
    * left_volume *= left_moves_coef
    * right_volum *= right_moves_coef

once this is ok, do it with 4 chanels, cut image NW, NE, SW, SE
find 5.1 ALSA bindings ? a way to tune separatly 4 audio channels ?
see: ossaudiodev.openmixer ? ncurses

sudo apt-get install python-opencv python-pygame

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/basic_structures.html#iplimage
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
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

import wx
import sys
import cv2.cv as cv
import pygame

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
        pygame.mixer.init(channels=2)
        self._sound = None
        self._channel = None
        # CV / V4L Camera ID
        self._capture = cv.CaptureFromCAM(-1)
    def __del__(self):
        # close stuff ?
        pygame.mixer.quit()

    def setvolume(self, volume, right=None):
        if right:
            self._channel.set_volume(volume, right)
        else:
            self._channel.set_volume(volume)

    def play(self, path):
        self._sound = pygame.mixer.Sound(path)
        self._channel = self._sound.play()

    def capture(self):
        img = cv.QueryFrame(self._capture)
        imgsize = (img.width, img.height)
        imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
        cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
        velx = cv.CreateImage(imgsize, cv.IPL_DEPTH_32F, 1)
        vely = cv.CreateImage(imgsize, cv.IPL_DEPTH_32F, 1)
        winsize = (7, 7)
        cv.WaitKey(10)
        while 1:
            imgprev = imgcurr
            img = cv.QueryFrame(self._capture)
            imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
            cv.CalcOpticalFlowLK(imgprev, imgcurr, winsize, velx, vely)
            cv.ShowImage("x", velx)
            cv.ShowImage("y", vely)
            # TODO add x+y / 4 sum %
            self.flow_to_weight(velx, vely)
            key = cv.WaitKey(10) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == wx.WXK_ESCAPE:
                break

    def flow_to_weight(self, velx, vely):
        dst = cv.CreateImage((velx.width, velx.height), cv.IPL_DEPTH_32F, 1)
        cv.And(velx, vely, dst)
        cv.ShowImage("and", dst)

def main(args):
    import this # The Zen of Python, by Tim Peters

    if "h" in ''.join(args):
        sys.stderr.write(__doc__)
        return 1

    p = "/media/data/media/music/Yoshimi Battles the Pink Robots [5.1]/06 Ego Tripping at the Gates of Hell.ogg"
    dynso = DynamicSound()
    print("get ready! ( WIP :)")
    dynso.play(p)
    print("opencv is magic!")
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))