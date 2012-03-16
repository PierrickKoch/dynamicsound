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
  * http://pyalsaaudio.sourceforge.net/libalsaaudio.html#alsaaudio.Mixer.setvolume
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * libsdl ? ossaudiodev.openmixer ? ncurses
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#namedwindow
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#waitkey
  * http://wxpython.org/docs/api/wx.KeyEvent-class.html
  * https://www.google.com/search?q=usb+5.1&tbm=shop
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://en.wikipedia.org/wiki/MP3_Surround
  * http://en.wikipedia.org/wiki/Surround_sound
  * http://wiki.python.org/moin/PythonInMusic

API usage:
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
        cv.NamedWindow(__file__)
        while 1:
            img = cv.QueryFrame(self._capture)
            mono = cv.CreateImage((img.width, img.height), cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(img, mono, cv.CV_RGB2GRAY)
            cv.ShowImage(__file__, mono)
            key = cv.WaitKey(10) & 255
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