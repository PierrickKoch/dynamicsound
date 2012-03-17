Dynamic Sound
=============

  1. `init`
    * capture from cam
    * play sound (music)
  2. `while 1`
    * query frame (from cam)
    * calc optical flow lk (or some other magic, ideally object reco/tracking)
    * weight each 4 quart of the frame (0.0 < weight < 1.0)
    * apply weight as channel volume (see 5.1)

[![youtube](https://i2.ytimg.com/vi/S1fjLfp3Gb8/sddefault.jpg "youtube")](http://youtube.com/embed/S1fjLfp3Gb8?rel=0)

### sudo apt-get install python-opencv python-pygame

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * http://en.wikipedia.org/wiki/Surround_sound
  * http://wiki.python.org/moin/PythonInMusic
  * http://www.libsdl.org/projects/SDL_mixer/
  * http://connect.creativelabs.com/openal
  * libsdl ? ossaudiodev.openmixer ? ncurses

_TODO_ find 5.1 python volume mixer (found stereo, not surround)

_TODO_ test with usb 5.1 or hdmi digital output + hdmi surround hifi

  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://usa.yamaha.com/products/audio-visual/av-receivers-amps/rx
  * http://hg.pygame.org/pygame/src/d1cbb8c9d94b/test/playwave.py#cl-181
  * http://hg.pygame.org/pygame/src/9c6aa550da25/doc/src/openal_constants.rst#cl-69
  * https://bitbucket.org/pygame/pygame/issue/113
  * http://crystalspace3d.org "3D sounds" !


## API usage: `0.0` < `weight` < `1.0`

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

