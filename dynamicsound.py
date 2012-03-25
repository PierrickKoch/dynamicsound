#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py [MUSIC{.ogg|.wav}]

    soundupleft, soundupright, sounddownleft, sounddownright

http://opensource.org/licenses/BSD-3-Clause
"""

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
        pygame.mixer.init(channels=2) # 1 <= channels <= 2
        self.capturing = False
        self._weight = [0.0] * 4
        self.pyramid = None
        self.cone = None
    def __del__(self):
        pygame.mixer.fadeout(800)
        # close mixer
        pygame.mixer.quit()

    def setvolume(self, volume):
        for i in xrange(4):
            self._channel[i].set_volume(volume[i])
        print(" %.2f %.2f %.2f %.2f "%tuple(volume))

    def play(self, sounds):
        """ play 4 sounds
        :param sounds: list of 4 path to sound {.wav|.ogg}
                       soundupleft, soundupright, sounddownleft, sounddownright
        """
        for i in xrange(4):
            self._sound[i] = pygame.mixer.Sound(sounds[i])
        print("debug: 4 sounds loaded")
        for i in xrange(4):
            self._channel[i] = self._sound[i].play()
            self._channel[i].set_volume(0.1)
        print("debug: 4 sounds playing")

    def capture(self):
        self.capturing = True
        image = cv.QueryFrame(self._capture)
        imagesize = (image.width, image.height)
        imagecurr = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        cv.CvtColor(image, imagecurr, cv.CV_RGB2GRAY)
        midx = image.width // 2
        midy = image.height // 2
        del image
        # init windows (for debug)
        cv.NamedWindow("downright")
        cv.NamedWindow("downleft")
        cv.NamedWindow("upright")
        cv.NamedWindow("upleft")
        cv.MoveWindow("downright", midx, midy + 20)
        cv.MoveWindow("downleft", 0, midy + 20)
        cv.MoveWindow("upright", midx, 0)
        cv.MoveWindow("upleft", 0, 0)
        #self.init_pyramid(imagesize)
        self.init_cone(imagesize)
        while self.capturing:
            imageprev = imagecurr
            image = cv.QueryFrame(self._capture)
            imagecurr = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(image, imagecurr, cv.CV_RGB2GRAY)
            del image
            # image(t) - image(t-10) = moved
            # moved / 4 -> sum -> %
            self.sub_to_volume(imagecurr, imageprev)
            key = cv.WaitKey(100) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == 27: # aka ESCAPE
                self.capturing = False

    def init_pyramid(self, imagesize):
        self.pyramid = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        tmp = cv.CreateImage((5, 5), cv.IPL_DEPTH_8U, 1)
        data = array.array('B', [1, 1, 1, 1, 1,
                                 1, 2, 2, 2, 1,
                                 1, 2, 3, 2, 1,
                                 1, 2, 2, 2, 1,
                                 1, 1, 1, 1, 1])
        cv.SetData(tmp, data)
        cv.Resize(tmp, self.pyramid)

    def init_cone(self, imagesize):
        self.cone = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        tmp = cv.CreateImage((5, 5), cv.IPL_DEPTH_8U, 1)
        data = array.array('B', [1, 1, 2, 1, 1,
                                 1, 2, 3, 2, 1,
                                 2, 3, 4, 3, 2,
                                 1, 2, 3, 2, 1,
                                 1, 1, 2, 1, 1])
        cv.SetData(tmp, data)
        cv.Resize(tmp, self.cone, interpolation=cv.CV_INTER_LINEAR)
        self.display_lowintesity8u(self.cone)

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
        # use pyramid to ponderate the weight
        # ie. moves in corners are more important than in the center
        if divid:
            cv.Div(image, self.cone, image)
        cv.Flip(image, flipMode=1) # for webcam
        return image

    def sum_to_weight(self, sums):
        posmax = sums.index(max(sums))
        self._weight[posmax] += 1
        self._weight = [w / 2 for w in self._weight]

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

def main(args):
    if "-h" in args:
        sys.stderr.write(__doc__)
        return 1

    if len(args) > 1:
        sounds = args[1:]
    else:
        # TODO TMP DEBUG
        path = "/media/data/media/music/Yoshimi Battles the Pink Robots [5.1]/"
        sounds = [path+"04 Yoshimi Battles the Pink Robots (Part 2).ogg",
                  path+"05 In the Morning of the Magicians.ogg",
                  path+"06 Ego Tripping at the Gates of Hell.ogg",
                  path+"07 Are You a Hypnotist.ogg"]

    dynso = DynamicSound()
    print("get ready!")
    dynso.play(sounds)
    print("opencv is magic!")
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))