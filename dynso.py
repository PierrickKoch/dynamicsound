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
  * http://pyalsaaudio.sourceforge.net/libalsaaudio.html#alsaaudio.Mixer.setvolume
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * libsdl ?
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#namedwindow
  * http://opencv.willowgarage.com/documentation/python/user_interface.html#waitkey
  * http://wxpython.org/docs/api/wx.KeyEvent-class.html
  * https://www.google.com/search?q=usb+5.1&tbm=shop
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://en.wikipedia.org/wiki/MP3_Surround

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
            cv.ShowImage(__file__, img)
            key = cv.WaitKey(10)
            if key == wx.WXK_ESCAPE:
                """
                unicode bug: returns 1048603
                unichr(1048603) = u'\U0010001b'
                chr(wx.WXK_ESCAPE) = chr(27) = '\x1b'
                unichr doesn't help:
                    unichr(27) = u'\x1b' ord(unichr(27)) = 27
                ? see : http://qt-project.org/doc/qt-4.8/qt.html#Key-enum ?
                """
                break

def main(args):
    import this

    if "h" in ''.join(args):
        sys.stderr.write(__doc__)
        return 1

    dynso = DynamicSound()
    print("get ready! ( WIP :)")
    dynso.setvolume(100)
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))