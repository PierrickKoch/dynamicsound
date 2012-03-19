#!/usr/bin/env python
"""
Dynamic Sound project
usage: python dynso.py [MUSIC{.ogg|.wav}]

http://opensource.org/licenses/BSD-3-Clause
"""

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
        self._sound = {'down': {'right': None, 'left': None}, 
                       'up': {'right': None, 'left': None}}
        self._channel = {'down': {'right': None, 'left': None}, 
                         'up': {'right': None, 'left': None}}
        self._capture = cv.CaptureFromCAM(-1)
        pygame.mixer.init(channels=2) # max channels = 2 :/
        self.capturing = False
    def __del__(self):
        pygame.mixer.fadeout(800)
        # close mixer
        pygame.mixer.quit()

    def setvolume(self, volumeupleft, volumeupright, volumedownleft, volumedownright):
        if not self._channel:
            return # not playing
        self._channel["up"]["left"].set_volume(volumeupleft)
        self._channel["up"]["right"].set_volume(volumeupright)
        self._channel["down"]["left"].set_volume(volumedownleft)
        self._channel["down"]["right"].set_volume(volumedownright)

    def play(self, soundupleft, soundupright, sounddownleft, sounddownright):
        self._sound["up"]["left"] = pygame.mixer.Sound(soundupleft)
        self._sound["up"]["right"] = pygame.mixer.Sound(soundupright)
        self._sound["down"]["left"] = pygame.mixer.Sound(sounddownleft)
        self._sound["down"]["right"] = pygame.mixer.Sound(sounddownright)
        self._channel["up"]["left"] = self._sound["up"]["left"].play()
        self._channel["up"]["right"] = self._sound["up"]["right"].play()
        self._channel["down"]["left"] = self._sound["down"]["left"].play()
        self._channel["down"]["right"] = self._sound["down"]["right"].play()

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
        while self.capturing:
            imageprev = imagecurr
            image = cv.QueryFrame(self._capture)
            imagecurr = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
            cv.CvtColor(image, imagecurr, cv.CV_RGB2GRAY)
            del image
            # TODO image(t) - image(t-10) = moved
            #      moved / 4 sum -> %
            self.sub_to_volume(imagecurr, imageprev)
            key = cv.WaitKey(100) & 255
            # If ESC key pressed Key=0x1B, Key=0x10001B under OpenCV linux
            if key == 27: # aka ESCAPE
                self.capturing = False

    def sub_image(self, imagecurr, imageprev):
        imagesize = (imagecurr.width, imagecurr.height)
        image = cv.CreateImage(imagesize, cv.IPL_DEPTH_8U, 1)
        cv.Sub(imagecurr, imageprev, image)
        # TODO use inverse pyramide to ponderate the weight ?
        # ie. moves in corners are more important than in the center
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
        # sum to weight
        self.sum_to_weight(sum_up_left[0], sum_up_right[0], 
                           sum_down_left[0], sum_down_right[0])

    def weight_to_volume(self):
        # TODO some linearization
        self.setvolume(self.weight['up']['left'],
                       self.weight['up']['right'],
                       self.weight['down']['left'],
                       self.weight['down']['right'])

    def sub_to_volume(self, imagecurr, imageprev):
        image = self.sub_image(imagecurr, imageprev)
        self.image_to_weight(image)
        self.weight_to_volume()

def main(args):
    if "-h" in args:
        sys.stderr.write(__doc__)
        return 1

    path = "/media/data/media/music/Yoshimi Battles the Pink Robots [5.1]/"
    title = ["04 Yoshimi Battles the Pink Robots (Part 2).ogg",
             "05 In the Morning of the Magicians.ogg",
             "06 Ego Tripping at the Gates of Hell.ogg",
             "07 Are You a Hypnotist.ogg"]

    if len(args) > 1:
        soundupleft = args[1]
        soundupright = args[2]
        sounddownleft = args[3]
        sounddownright = args[4]
    else:
        # DEBUG
        soundupleft = path+title.pop()
        soundupright = path+title.pop()
        sounddownleft = path+title.pop()
        sounddownright = path+title.pop()
    dynso = DynamicSound()
    print("get ready!")
    dynso.play(soundupleft, soundupright, sounddownleft, sounddownright)
    print("opencv is magic!")
    dynso.capture()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
