#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py soundupleft soundupright sounddownleft sounddownright

    file type {.ogg|.wav}

http://opensource.org/licenses/BSD-3-Clause
http://pierriko.com/dynamicsound/

TIPS: encode from MP3 to OGG

    ffmpeg -i src.mp3 -vn -acodec libvorbis -ab 192k dst.ogg 

TODO: playlist
"""

import os
import sys
import array
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

UP_LEFT = 0
UP_RIGHT = 1
DOWN_LEFT = 2
DOWN_RIGHT = 3

class DynamicSound(object):
    def __init__(self):
        self._sound = [None] * 4
        self._channel = [None] * 4
        self._capture = cv.CaptureFromCAM(-1)
        pygame.mixer.init(frequency=44100, channels=2, buffer=2048)
        self.capturing = False
        self._weight = [0.0] * 4
        self.filter = None
        self.midx = 0
        self.midy = 0
    def __del__(self):
        pygame.mixer.fadeout(800)
        # close mixer
        pygame.mixer.quit()

    def setvolume(self, volume):
        for i in xrange(4):
            self._channel[i].set_volume(volume[i])
        print(self)

    def play(self, sounds):
        """ play 4 sounds
        :param sounds: list of 4 path to sound {.wav|.ogg}
                       soundupleft, soundupright, sounddownleft, sounddownright
        """
        for i in xrange(4):
            if not os.path.isfile(sounds[i]):
                print("warning: not a file: "+sounds[i])
                return
            # load all in memory, slow!
            self._sound[i] = pygame.mixer.Sound(sounds[i])
        print("debug: 4 sounds loaded")
        for i in xrange(4):
            self._channel[i] = self._sound[i].play(loops=-1)
            self._channel[i].set_volume(0.1)
        print("debug: 4 sounds playing")

    def capture(self):
        self.capturing = True
        image = cv.QueryFrame(self._capture)
        imagesize = (image.width, image.height)
        imagecurr = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        cv.CvtColor(image, imagecurr, cv.CV_RGB2GRAY)
        self.midx = image.width // 2
        self.midy = image.height // 2
        del image
        # init windows (for debug)
        def init_window(name, x, y):
            cv.NamedWindow(name)
            cv.MoveWindow(name, x, y)
        init_window("downright", self.midx, self.midy + 20)
        init_window("downleft", 0, self.midy + 20)
        init_window("upright", self.midx, 0)
        init_window("upleft", 0, 0)
        self.init_filter(imagesize)
        while self.capturing:
            imageprev = imagecurr
            image = cv.QueryFrame(self._capture)
            imagecurr = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(image, imagecurr, cv.CV_RGB2GRAY)
            del image
            # image(t) - image(t-10) = moved
            # moved / 4 -> sum -> % -> volume
            self.sub_to_volume(imagecurr, imageprev)
            key = cv.WaitKey(100) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == 27: # aka ESCAPE
                self.capturing = False

    def init_filter(self, imagesize):
        self.filter = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        tmp = cv.CreateImage((7, 7), cv.IPL_DEPTH_8U, 1)
        data = array.array('B', [1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 2, 3, 2, 1, 1,
                                 2, 2, 3, 4, 3, 2, 2,
                                 1, 1, 2, 3, 2, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1])
        cv.SetData(tmp, data)
        cv.Resize(tmp, self.filter, interpolation=cv.CV_INTER_LINEAR)
        self.display_lowintesity8u(self.filter)

    def display_lowintesity8u(self, image, maxintesity=None):
        if not maxintesity:
            (_, maxintesity, _, _) = cv.MinMaxLoc(image)
            # (minVal, maxVal, minLoc, maxLoc)
        display = cv.CloneImage(image)
        cv.Scale(image, display, 255 / maxintesity)
        cv.ShowImage("display", display)

    def sub_image(self, imagecurr, imageprev, divid=True):
        imagesize = (imagecurr.width, imagecurr.height)
        image = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        cv.Sub(imagecurr, imageprev, image)
        # use pyramid/filter to ponderate the weight
        # ie. moves in corners are more important than in the center
        if divid:
            cv.Div(image, self.filter, image)
        cv.Flip(image, flipMode=1) # for webcam
        return image

    def sum_to_weight(self, sums, proportional=False):
        maxsum = max(sums)
        posmax = sums.index(maxsum)
        if proportional: # TODO test real condition with light
            self._weight[posmax] += maxsum / sum(sums)
        else: # more "stable"
            self._weight[posmax] += 1.0
        self._weight = [w / 2.0 for w in self._weight]

    def image_to_weight(self, image):
        # up left ROI
        cv.SetImageROI(image, (0, 0, self.midx, self.midy))
        sum_up_left = cv.Sum(image)
        cv.ShowImage("upleft", image)
        # up right ROI
        cv.SetImageROI(image, (self.midx, 0, image.width, self.midy))
        sum_up_right = cv.Sum(image)
        cv.ShowImage("upright", image)
        # down left ROI
        cv.SetImageROI(image, (0, self.midy, self.midx, image.height))
        sum_down_left = cv.Sum(image)
        cv.ShowImage("downleft", image)
        # down right ROI
        cv.SetImageROI(image, (self.midx, self.midy, image.width, image.height))
        sum_down_right = cv.Sum(image)
        cv.ShowImage("downright", image)
        # sum to weight
        self.sum_to_weight((sum_up_left[0], sum_up_right[0],
                            sum_down_left[0], sum_down_right[0]))

    def sub_to_volume(self, imagecurr, imageprev):
        image = self.sub_image(imagecurr, imageprev)
        self.image_to_weight(image)
        self.setvolume(self._weight)

    @property
    def weight(self):
        # TIPS: use json.dumps(self.weight, indent=1)
        return {
            "up": {
                "left": self._weight[UP_LEFT],
                "right": self._weight[UP_RIGHT]
            },
            "down": {
                "left": self._weight[DOWN_LEFT],
                "right": self._weight[DOWN_RIGHT]
            }
        }
    def __str__(self):
        return " %.2f %.2f %.2f %.2f "%tuple(self._weight)

def main(args):
    if "-h" in args or "--help" in args or len(args) < 4:
        sys.stderr.write(__doc__)
        return 1

    dynso = DynamicSound()
    print("get ready! press ESCAPE to quit.")
    dynso.play(args[1:])
    print("opencv is magic!")
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
