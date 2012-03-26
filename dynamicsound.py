#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py [MUSIC{.ogg|.wav}]

    soundupleft, soundupright, sounddownleft, sounddownright

http://opensource.org/licenses/BSD-3-Clause
http://pierriko.com/dynamicsound/
"""

import os
import sys
import array
import urllib

try:
    import cv
except ImportError:
    print("install opencv: sudo apt-get install python-opencv")
    sys.exit(1)
try:
    import gst
except ImportError:
    print("install gstream: sudo apt-get install python-gst0.10")
    sys.exit(1)

UP_LEFT = 0
UP_RIGHT = 1
DOWN_LEFT = 2
DOWN_RIGHT = 3

class GstPlayer(object):
    def __init__(self, player="player"):
        self.player = gst.element_factory_make("playbin", player)
        self.bus = self.player.get_bus()
    def play(self, song):
        if not os.path.exists(song):
            sys.stderr.write("song path does not exists: " + song)
            return
        fileuri = "file://" + urllib.pathname2url(song)
        if not gst.uri_is_valid(fileuri):
            sys.stderr.write("song uri is not valid: " + fileuri)
            return
        self.player.set_property("uri", fileuri)
        self.player.set_state(gst.STATE_PLAYING)
    def stop(self):
        self.player.set_state(gst.STATE_NULL)
    def volume(self, volume):
        self.player.set_property('volume', volume)

class DynamicSound(object):
    def __init__(self):
        self._players = [GstPlayer("player%i"%i) for i in xrange(4)]
        self._capture = cv.CaptureFromCAM(-1)
        self.capturing = False
        self._weight = [0.0] * 4
        self.cone = None
    def __del__(self):
        # stop playing
        for player in self._players:
            player.stop()

    def setvolume(self, volume):
        for i in xrange(4):
            self._players[i].volume(volume[i])
        print(self)

    def play(self, sounds):
        """ play 4 sounds
        :param sounds: list of 4 path to sound {.wav|.ogg}
                       soundupleft, soundupright, sounddownleft, sounddownright
        """
        for i in xrange(4):
            self._players[i].play(sounds[i])
            self._players[i].volume(0.1)
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
        self.init_cone(imagesize)
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

    def init_cone(self, imagesize):
        self.cone = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        tmp = cv.CreateImage((7, 7), cv.IPL_DEPTH_8U, 1)
        data = array.array('B', [1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 2, 3, 2, 1, 1,
                                 2, 2, 3, 4, 3, 2, 2,
                                 1, 1, 2, 3, 2, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1,
                                 1, 1, 1, 2, 1, 1, 1])
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
        # use pyramid/cone to ponderate the weight
        # ie. moves in corners are more important than in the center
        if divid:
            cv.Div(image, self.cone, image)
        cv.Flip(image, flipMode=1) # for webcam
        return image

    def sum_to_weight(self, sums):
        maxsum = max(sums)
        posmax = sums.index(maxsum)
        self._weight[posmax] += 1.0 # maxsum / sum(sums)
        self._weight = [w / 2.0 for w in self._weight]

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
    def __str__(self):
        return " %.2f %.2f %.2f %.2f "%tuple(self._weight)

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