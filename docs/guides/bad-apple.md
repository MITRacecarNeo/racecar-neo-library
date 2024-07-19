# Generalized Bad Apple

With the advent of style points for creative usages of the dot matrix display during labs going forward, I've decided to make a very thorough guide to running arbitrary videos / animations on the racecar.

If you don't understand everything in this guide, that's ok! Some of this guide (especially the OpenCV image processing section) is very advanced and exists only to "wet your feet", so to speak, on image processing and other interesting topics. Some other stuff is somewhat tangential and only included because I thought it was cool.

Finally, some disclaimers about the dot matrix:
- Due to the LED display / driver we are using, the dot matrix can only show binary images; each pixel is either on or off.
- The resolution of the dot matrix display is 8x24.

Therefore, consider *before* going through all of this hassle whether the animation you want to play would become unrecognizable if you turned it into a solid plane of black and white, or if you compressed it down to 8x24, or if you squeezed it into a 3:1 aspect ratio.

That being said, after you've found a cool and compatible animation to play, we can get started with step 1:

### Step 1 — Generating a frameset

First, we'll need a collection of frames for the animation we want to play. Sometimes, you can find readily-available framesets online; for bad apple, I downloaded [this frameset from the Internet Archive](https://archive.org/details/bad_apple_is.7z).

Otherwise, we'll need to create a frameset ourselves:

#### GIFs

If your animation is a GIF, creating a frameset is as simple as extracting the frames from your GIF (in an oversimplified sense, a GIF file is just a collection of images; you can read more about the GIF file format [here](https://en.wikipedia.org/wiki/GIF#File_format)).

We can do this using any image processing software. Photoshop would likely work, though for an online free alternative we can also use [Photopea](https://www.photopea.com/):

![image](https://gist.github.com/user-attachments/assets/1001966f-d8af-45bf-8925-84ac0aba1128)

Open your GIF in Photopea, then select **File > Export Layers**. Uncheck the option to only export layers starting with `-e-` and click export to download a ZIP of your frames.

![image](https://gist.github.com/user-attachments/assets/9873dba5-c6d1-4fac-83d6-703bda578bc3)

#### YouTube videos

If your animation is a YouTube video, the process is a little more complex. You'll first need to download your video as an MP4; if you have YouTube premium, you can download it directly from the website!

Otherwise, you'll need to make use of one of several [sketchy YouTube to MP4 sites](https://ytmp3.plus/CXIv/) online (necessarily sketchy because [downloading videos through non-YouTube channels is against YouTube ToS](https://www.youtube.com/t/terms#c3e2907ca8)). Half of these sites are broken and filled with SEO soup; tread carefully!

Assuming you've downloaded your video successfully, you can safely proceed to the next subsection.

#### MP4s

If your animation is an MP4 or other common video format, you can use a site like [Ezgif](https://ezgif.com/video-to-jpg) to convert it to a frameset:

![image](https://gist.github.com/user-attachments/assets/ab7b33b3-2411-4657-8dd9-2caedb51ff37)

![image](https://gist.github.com/user-attachments/assets/3c4a90b7-36b7-45f0-a1d0-dc9339f6986f)

### Step 2 — Pixelation and masking

Now that we have a folder of image files to play, we'll need to preprocess them so that they're ready for the racecar. In the racecar library, there *is* a [utility function that lets you pixelate images for the dot matrix](https://mitracecarneo.github.io/racecar-neo-library/docs/utils.html#racecar_utils.pixelate_image); however, uploading your raw frameset to the racecar is inefficient and sometimes prohibitively so (for bad apple, the raw 6562 frames took up a combined ~500 MB).

Instead, we'll want to squish our images to 8x24 *before* copying them to the pi. The following python script will traverse all files in the folder specified by `INPUT_PATH`, pixelating them and dumping them in `OUTPUT_PATH`. 
```py
import os
import cv2


INPUT_PATH = './image_sequence'
OUTPUT_PATH = './processed'

files = os.listdir(INPUT_PATH)

# If the output directory doesn't exist yet, create it.
if not os.path.exists(OUTPUT_PATH):
    os.mkdir(OUTPUT_PATH)

for f in files:
    # Read in the frame image, resize it to 8x24, and write it to the output directory under the same name.
    img = cv2.imread(f'{INPUT_PATH}/{f}')
    out = cv2.resize(img, (24, 8), interpolation=cv2.INTER_LINEAR)

    cv2.imwrite(f'{OUTPUT_PATH}/{f}', out)
    print(f)
```
(for comparison, bad apple's 6562 frames only took up 1 MB of disk space after squishing.)

Note that using `cv2.resize` for pixelation will stretch your image into the required 3:1 aspect ratio. If you don't want your frames to be stretched, you could consider cropping your frames to 3:1 *before* pixelizing them; you could also use cropping to "zoom in" on a subsection of a frame if the resizing process results in the loss of too many details. Because OpenCV images are just numpy arrays, you can [crop an image using numpy array slicing](https://stackoverflow.com/a/16823104):
```py
img = ...

top_left = (0, 100)
bottom_right = (300, 400)
cropped = img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
```

If your frames were already in black and white (like the frames of bad apple), this is likely all the preprocessing you need to do.

Otherwise, if your frames have color or differing grayscale values, you'll probably want to convert it to a binary image as well. The easiest way to accomplish this is via masking: [`cv2.inRange(img, low, high)` may be very helpful here](https://docs.opencv.org/3.4/da/d97/tutorial_threshold_inRange.html).

If you'd like to test your image transform before applying it to all your frames, you can create a simple test script like so:
```py
import cv2


FRAME_PATH = '...'  # Fill this in with the path to the frame you want to test with!
cv2.namedWindow('out', cv2.WINDOW_NORMAL)

img = cv2.imread(FRAME_PATH)
cv2.imshow('out', img)
cv2.waitKey()

# Do something with `img` here

cv2.imshow('out', img)
cv2.waitKey()
```
This script will show your original frame, then after a keypress show the result of the transformation on that frame. If you want to show them side by side, you can create multiple windows and remove the first `cv2.waitKey()` so that both windows are opened simultaneously.

Another function to familiarize yourself with is [`cv2.cvtColor(img, conversion)`](https://docs.opencv.org/3.4/d8/d01/group__imgproc__color__conversions.html#ga397ae87e1288a81d2363b61574eb8cab), which converts an image from one colorspace to another. By default, OpenCV images are in the BGR colorspace (ie. each pixel is a size-3 tuple corresponding to its Blue, Green, and Red values). When thresholding with `cv2.inRange`, you may want to convert your image to HSV first via
```py
img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
```
so you can specify ranges in HSV instead. If interested, you can read more about the internal calculations behind colorspace conversions [here](https://docs.opencv.org/3.4/de/d25/imgproc_color_conversions.html).

Here's an example of everything together in the test script:
```py
import numpy as np
import cv2


FRAME_PATH = './frames/ezgif-frame-050.jpg'
cv2.namedWindow('out', cv2.WINDOW_NORMAL)

img = cv2.imread(FRAME_PATH)
cv2.imshow('out', img)
cv2.waitKey()

img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Keep pixels around this color
target = np.array([35, 20, 225])
mask = cv2.inRange(img, target - 10, target + 10)

cv2.imshow('out', mask)
cv2.waitKey()
```

![image](https://gist.github.com/user-attachments/assets/6c84032d-cd1f-4cc2-ba2d-205c1c17dc39)

![image](https://gist.github.com/user-attachments/assets/9e317df0-3e58-41d6-b4d6-21ad79efe94d)

(ignore the details of this particular mask, somehow my original video frames became [artifacted](https://en.wikipedia.org/wiki/Compression_artifact) beyond recognition).

Then, you can place your mask transform in the original pixelation script to generate your final processed frames.

### Step 3 — Play it on the racecar!

Now that we have a collection of labelled, pixelated, black-and-white frames, we can finally play our animation on the racecar! Remember that we can copy our frames over to the racecar using
```bash
scp -r ./{folder name}/ racecar@192.168.1.{team number}:~/{remote location}
```
ex.
```bash
scp -r ./processed/ racecar@192.168.1.106:~/jupyter_ws/student/labs
```

Then, you can run the animation using a script like so
```py
import sys

import cv2

# If this file is nested inside a folder in the labs folder, the relative path should
# be [1, ../../library] instead.
sys.path.insert(0, '../../library')
import racecar_core

rc = racecar_core.create_racecar()

TOTAL_FRAMES = 6562
FRAMES_PER_SECOND = 30

frames = []
time = 0

# Load all frames on startup
for i in range(TOTAL_FRAMES):
    img = cv2.imread(f'./processed/...', cv2.IMREAD_GRAYSCALE)  # Replace with your frame naming conventions
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    frames.append(img)


# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    global time
    time = 0


# [FUNCTION] After start() is run, this function is run once every frame (ideally at
# 60 frames per second or slower depending on processing speed) until the back button
# is pressed
def update():
    global time
    time += rc.get_delta_time()

    # Play `FRAMES_PER_SECOND` frames per second, looping around at the end of the animation.
    curr_frame = int(time * FRAMES_PER_SECOND) % TOTAL_FRAMES
    rc.display.set_matrix(frames[curr_frame])


# [FUNCTION] update_slow() is similar to update() but is called once per second by
# default. It is especially useful for printing debug messages, since printing a
# message every frame in update is computationally expensive and creates clutter
def update_slow():
    pass


if __name__ == "__main__":
    rc.set_start_update(start, update, update_slow)
    rc.go()
```
replacing the `TOTAL_FRAMES` and `FRAMES_PER_SECOND` constants with your animation's values and updating the frame initialization code to account for however your processed frames are named.

Run the script, then press start to play your cool animation!
