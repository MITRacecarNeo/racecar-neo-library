"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: display_real.py
File Description: Contains the Display module of the racecar_core library
"""
import cv2 as cv
import numpy as np
import os
from nptyping import NDArray

from display import Display

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT


class DisplayReal(Display):
    __WINDOW_NAME: str = "RACECAR display window"
    __DISPLAY: str = ":0"

    def __init__(self, isHeadless):
        Display.__init__(self, isHeadless)
        self.__display_found = \
            self.__DISPLAY in os.popen('cd /tmp/.X11-unix && for x in X*; do echo ":${x#X}"; done ').read()

        if self.__display_found:
            os.environ["DISPLAY"] = self.__DISPLAY
        else:
            print(f"Display {self.__DISPLAY} not found.")

        # Create matrix device
        try:
            serial = spi(port=0, device=0, gpio=noop())
            self.device = max7219(
                serial,
                cascaded=3,
                block_orientation=-90,
                rotate=0,
                blocks_arranged_in_reverse_order=False
            )
            print("matrix display successfully initialized")
        except Exception as e:
            print(f"matrix display initialization failed. Reason: {e}")

        self.__matrix = np.zeros((8, 24), dtype=np.uint8)  # Create starting dot matrix design of all zeroes

    def create_window(self) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.namedWindow(self.__WINDOW_NAME)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)

    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        self.__matrix = matrix
        with canvas(self.device) as draw:
            for x in range(0, self.device.width):
                for y in range(0, self.device.height):
                    if matrix[y][x]:
                        draw.point((x, y), fill="white")

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def set_matrix_intensity(self, intensity: float) -> None:
        assert (
            0.0 <= intensity <= 1.0
        ), f"intensity [{intensity}] must be between 0.0 and 1.0 inclusive."

        contrast = int(intensity * 255)
        self.device.contrast(contrast)
