Dynamic Sound
=============

  1. `init`
    * capture from cam
    * play 4 sounds
  2. `while 1`
    * query frame (from cam)
    * sub: image(t) - image(t-10) = moved
    * weight each 4 quart of the frame (0.0 < weight < 1.0)
      * moved / 4 quarter images -> sum each quarter px -> % -> volume
    * apply weight as channel volume

[![youtube](https://i2.ytimg.com/vi/KJYo7oxTgus/sddefault.jpg "youtube")](http://youtube.com/embed/KJYo7oxTgus?rel=0)

`sudo apt-get install python-opencv python-pygame`

  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#capturefromcam
  * http://opencv.willowgarage.com/documentation/python/reading_and_writing_images_and_video.html#queryframe
  * http://opencv.willowgarage.com/documentation/python/video_motion_analysis_and_object_tracking.html#calcopticalflowlk
  * http://opencv.willowgarage.com/documentation/python/core_operations_on_arrays.html#sub
  * http://pygame.org/docs/ref/mixer.html#Channel.set_volume
  * http://en.wikipedia.org/wiki/Surround_sound
  * http://en.wikipedia.org/wiki/DVD-Audio
  * http://en.wikipedia.org/wiki/Category:Albums_in_5.1
  * http://wiki.python.org/moin/PythonInMusic
  * http://www.libsdl.org/projects/SDL_mixer/
    * https://www.google.com/search?q=python+site:libsdl.org
  * http://connect.creativelabs.com/openal
    * https://www.google.com/search?q=python+site:opensource.creative.com%2Fpipermail%2Fopenal
  * libsdl ? ossaudiodev.openmixer ? ncurses
  * http://en.store.creative.com/sound-blaster/sound-blaster-x-fi-surround-5-1-pro/1-20055.aspx
  * http://usa.yamaha.com/products/audio-visual/av-receivers-amps/rx
  * http://hg.pygame.org/pygame/src/d1cbb8c9d94b/test/playwave.py#cl-181
  * http://hg.pygame.org/pygame/src/9c6aa550da25/doc/src/openal_constants.rst#cl-69
  * https://bitbucket.org/pygame/pygame/issue/113
  * http://crystalspace3d.org "3D sounds" !
  * http://pysonic.sourceforge.net ! (based on closed src lib :/ )
    * http://fmod.org/products/fmodex.html
    * https://www.google.com/search?q=3d+sound+python
  * http://cgit.freedesktop.org/gstreamer/gst-python

---

API usage: `0.0` < `weight` < `1.0`
-----------------------------------

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

