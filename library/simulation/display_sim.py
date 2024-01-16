import cv2 as cv
import numpy as np
from nptyping import NDArray

from display import Display


class DisplaySim(Display):
    __WINDOW_NAME: str = "RacecarSim display window"

    def __init__(self, isHeadless) -> None:
        Display.__init__(self, isHeadless)

    def create_window(self) -> None:
        if not self._Display__isHeadless:
            cv.namedWindow(self.__WINDOW_NAME, cv.WINDOW_NORMAL)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)
