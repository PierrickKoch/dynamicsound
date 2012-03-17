#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py

http://opensource.org/licenses/BSD-3-Clause

  1. init:
    * capturefromcam
    * play music
  2. while 1
    * queryframe (from cam)
    * calcopticalflowlk (or some other magic, ideally object reco/tracking)
    * weight each 4 quart of the frame (0.0 < weight < 1.0)
    * apply weight as channel volume (see 5.1)

sudo apt-get install python-opencv python-pygame

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * http://en.wikipedia.org/wiki/Surround_sound
  * http://wiki.python.org/moin/PythonInMusic
  * libsdl ? ossaudiodev.openmixer ? ncurses

TODO find 5.1 python volume mixer (found stereo, not surround)
TODO test with usb 5.1 or hdmi digital output + hdmi surround hifi
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://usa.yamaha.com/products/audio-visual/av-receivers-amps/rx

    #-#-#
    |   |
    | O |
    #---#

http://hg.pygame.org/pygame/src/d1cbb8c9d94b/test/playwave.py#cl-181
http://hg.pygame.org/pygame/src/9c6aa550da25/doc/src/openal_constants.rst#cl-69


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
try:
    import cv
except ImportError:
    print("install opencv: sudo apt-get install python-opencv")
    sys.exit(1)
try:
    import pygame
except ImportError:
    print("install pygame: sudo apt-get install python-pygame")
    sys.exit(1)

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
        self._sound = None
        self._channel = None
        # CV / V4L Camera ID
        self._capture = cv.CaptureFromCAM(-1)
        pygame.mixer.init(channels=2)
    def __del__(self):
        # close stuff
        pygame.mixer.quit()

    def setvolume(self, volume, right=None):
        print(volume, right)
        if not self._channel:
            return # not playing
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
        winsize = (3, 3)
        # init windows (for debug)
        cv.NamedWindow("upleft")
        cv.NamedWindow("upright")
        cv.NamedWindow("downleft")
        cv.NamedWindow("downright")
        cv.MoveWindow("upleft", 0, 0)
        cv.MoveWindow("upright", img.width//2, 0)
        cv.MoveWindow("downleft", 0, img.height//2)
        cv.MoveWindow("downright", img.width//2, img.height//2)
        cv.WaitKey(10)
        while 1:
            imgprev = imgcurr
            img = cv.QueryFrame(self._capture)
            imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
            cv.CalcOpticalFlowLK(imgprev, imgcurr, winsize, velx, vely)
            # x*y / 4 sum -> %
            self.flow_to_volume(velx, vely)
            key = cv.WaitKey(10) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == wx.WXK_ESCAPE:
                break

    def flow_xy_to_image(self, velx, vely):
        imgsize = (velx.width, velx.height)
        velx8u = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
        vely8u = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
        cv.ConvertScaleAbs(velx, velx8u)
        cv.ConvertScaleAbs(vely, vely8u)
        image = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
        cv.AddWeighted(velx8u, 0.5, vely8u, 0.5, 0, image)
        cv.Flip(image, flipMode=1) # for webcam
        return image

    def sum_to_weight(self, up_left, up_right, down_left, down_right):
        highest = max(up_left, up_right, down_left, down_right)
        # max -> 1.0
        def get_weight(value):
            if highest > 1:
                tmp = value / highest
                return round(tmp, 4) if tmp > 0.1 else 0.1
            else:
                return 1.0
        self.weight['up']['left'] = get_weight(up_left)
        self.weight['up']['right'] = get_weight(up_right)
        self.weight['down']['left'] = get_weight(down_left)
        self.weight['down']['right'] = get_weight(down_right)

    def image_to_weight(self, image):
        midx = image.width // 2
        midy = image.height // 2
        # up left ROI
        cv.SetImageROI(image, (0, 0, midx, midy))
        sum_up_left = cv.Sum(image)
        cv.ShowImage("upleft", image)
        # up right ROI
        cv.SetImageROI(image, (midx, 0, image.width, midy))
        sum_up_right = cv.Sum(image)
        cv.ShowImage("upright", image)
        # down left ROI
        cv.SetImageROI(image, (0, midy, midx, image.height))
        sum_down_left = cv.Sum(image)
        cv.ShowImage("downleft", image)
        # down right ROI
        cv.SetImageROI(image, (midx, midy, image.width, image.height))
        sum_down_right = cv.Sum(image)
        cv.ShowImage("downright", image)
        self.sum_to_weight(sum_up_left[0], sum_up_right[0], 
                           sum_down_left[0], sum_down_right[0])

    def weight_to_volume(self):
        vleft = self.weight['up']['left'] + self.weight['down']['left']
        vright = self.weight['up']['right'] + self.weight['down']['right']
        highest = max(vleft, vright)
        vleft = round(vleft/highest, 2)
        vright = round(vright/highest, 2)
        self.setvolume(vleft, vright)

    def flow_to_volume(self, velx, vely):
        image = self.flow_xy_to_image(velx, vely)
        self.image_to_weight(image)
        self.weight_to_volume()

def main(args):
    if "-h" in args:
        sys.stderr.write(__doc__)
        return 1

    path = "/media/data/media/music/Yoshimi Battles the Pink Robots [5.1]/06 Ego Tripping at the Gates of Hell.ogg"
    if len(args) > 1:
        path = args[1]
    dynso = DynamicSound()
    print("get ready!")
    dynso.play(path)
    print("opencv is magic!")
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))