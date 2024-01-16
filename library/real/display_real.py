"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: display_real.py
File Description: Contains the Display module of the racecar_core library
"""
import cv2 as cv
import os
from nptyping import NDArray

from display import Display


class DisplayReal(Display):
    __WINDOW_NAME: str = "RACECAR display window"
    __DISPLAY: str = ":0"

    def __init__(self, isHeadless):
        Display.__init__(self, isHeadless)
        self.__display_found = (
            self.__DISPLAY
            in os.popen(
                'cd /tmp/.X11-unix && for x in X*; do echo ":${x#X}"; done '
            ).read()
        )
        if self.__display_found:
            os.environ["DISPLAY"] = self.__DISPLAY
        else:
            print(f"Display {self.__DISPLAY} not found.")

    def create_window(self) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.namedWindow(self.__WINDOW_NAME)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)
