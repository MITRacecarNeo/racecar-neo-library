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

import rclpy as ros2
from std_msgs.msg import String

from display import Display


class DisplayReal(Display):
    __WINDOW_NAME: str = "RACECAR display window"
    __DISPLAY: str = ":0"
    __LED_MATRIX_TOPIC: str = "/led_matrix/command"

    def __init__(self, isHeadless):
        Display.__init__(self, isHeadless)
        self.__display_found = \
            self.__DISPLAY in os.popen('cd /tmp/.X11-unix && for x in X*; do echo ":${x#X}"; done ').read()

        if self.__display_found:
            os.environ["DISPLAY"] = self.__DISPLAY
        else:
            print(f"Display {self.__DISPLAY} not found.")

        # Dot matrix is an 8x8 panel driven by a serial firmware that accepts
        # text only (see neoracer_ros2_driver/led_matrix.py). show_text()
        # publishes to /led_matrix/command; set_matrix()/get_matrix() operate
        # on an in-memory placeholder since raw-pixel control is not exposed.
        self.node = ros2.create_node("display_node")
        self.__matrix_pub = self.node.create_publisher(
            String, self.__LED_MATRIX_TOPIC, qos_profile=1
        )
        self.__matrix = np.zeros((8, 24), dtype=np.uint8)

    def create_window(self) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.namedWindow(self.__WINDOW_NAME)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)

    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        arr = np.array(matrix, dtype=np.uint8)
        if arr.shape != (8, 24):
            print("WARNING: Matrix must be of shape (8, 24). Reshaping to fit.")
            arr = arr.reshape((8, 24))
        self.__matrix = arr

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def show_text(self, text: str, scroll_speed: float = 2.0) -> None:
        # The firmware ignores scroll_speed; it scrolls automatically when the
        # rendered text exceeds the 8-pixel panel width.
        msg = String()
        msg.data = text
        self.__matrix_pub.publish(msg)

    def set_matrix_intensity(self, intensity: float) -> None:
        assert (
            0.0 <= intensity <= 1.0
        ), f"intensity [{intensity}] must be between 0.0 and 1.0 inclusive."
