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

once this is ok, do it with 4 channels, cut image NW, NE, SW, SE
find 5.1 ALSA bindings ? a way to tune separatly 4 audio channels ?
see: ossaudiodev.openmixer ? ncurses

sudo apt-get install python-opencv python-pygame

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * libsdl ? ossaudiodev.openmixer ? ncurses
  * https://www.google.com/search?q=usb+5.1&tbm=shop
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
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
try:
    import cv2.cv as cv
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
        # close stuff ?
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
        cv.WaitKey(10)
        while 1:
            imgprev = imgcurr
            img = cv.QueryFrame(self._capture)
            imgcurr = cv.CreateImage(imgsize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(img, imgcurr, cv.CV_RGB2GRAY)
            cv.CalcOpticalFlowLK(imgprev, imgcurr, winsize, velx, vely)
            # x*y / 2 sum -> %
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
        def get_volume(value):
            if highest > 1:
                tmp = value / highest
                return round(tmp, 4) if tmp > 0.1 else 0.1
            else:
                return 1.0
        self.weight['up']['left'] = get_volume(up_left)
        self.weight['up']['right'] = get_volume(up_right)
        self.weight['down']['left'] = get_volume(down_left)
        self.weight['down']['right'] = get_volume(down_right)

    def image_to_weight(self, image):
        midx = image.width // 2
        midy = image.height // 2
        # up left ROI
        cv.SetImageROI(image, (0, 0, midx, midy))
        sum_up_left = cv.Sum(image)
        cv.ShowImage("up left", image)
        # up right ROI
        cv.SetImageROI(image, (midx, 0, image.width, midy))
        sum_up_right = cv.Sum(image)
        cv.ShowImage("up right", image)
        # down left ROI
        cv.SetImageROI(image, (0, midy, midx, image.height))
        sum_down_left = cv.Sum(image)
        cv.ShowImage("down left", image)
        # down right ROI
        cv.SetImageROI(image, (midx, midy, image.width, image.height))
        sum_down_right = cv.Sum(image)
        cv.ShowImage("down right", image)
        self.sum_to_weight(sum_up_left[0], sum_up_right[0], 
                           sum_down_left[0], sum_down_right[0])

    def weighted_volume(self):
        vleft = self.weight['up']['left'] + self.weight['down']['left']
        vright = self.weight['up']['right'] + self.weight['down']['right']
        highest = max(vleft, vright)
        vleft = round(vleft/highest, 2)
        vright = round(vright/highest, 2)
        self.setvolume(vleft, vright)

    def flow_to_volume(self, velx, vely):
        image = self.flow_xy_to_image(velx, vely)
        self.image_to_weight(image)
        self.weighted_volume()

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