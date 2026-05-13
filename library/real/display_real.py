"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: display_real.py
File Description: Contains the Display module of the racecar_core library.
Publishes to the driver's /dotmatrix/* topics rather than touching the SPI
bus directly, so we cooperate with dotmatrix_node instead of fighting it for
the MAX7219 device.
"""

import os

import cv2 as cv
import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

from display import Display

import rclpy as ros2
from std_msgs.msg import String, UInt8MultiArray


class DisplayReal(Display):
    __WINDOW_NAME: str = "RACECAR display window"
    __DISPLAY: str = ":0"

    # Driver-side dotmatrix topics. Pixels takes priority over text in the
    # node's render cascade and re-asserts itself within pixels_timeout_sec
    # (5 s by default), so set_matrix overrides any active text scroll.
    __TEXT_TOPIC: str = "/dotmatrix/text"
    __PIXELS_TOPIC: str = "/dotmatrix/pixels"

    # Dotmatrix viewport is 8 rows by 24 columns (3 cascaded MAX7219s)
    __MATRIX_ROWS: int = 8
    __MATRIX_COLS: int = 24

    def __init__(self, isHeadless):
        Display.__init__(self, isHeadless)
        self.__display_found = (
            self.__DISPLAY in os.popen(
                'cd /tmp/.X11-unix && for x in X*; do echo ":${x#X}"; done '
            ).read()
        )

        if self.__display_found:
            os.environ["DISPLAY"] = self.__DISPLAY
        else:
            print(f"Display {self.__DISPLAY} not found.")

        # Dotmatrix publishers. dotmatrix_node owns the SPI bus; we only
        # publish messages.
        self.node = ros2.create_node("display_pub")
        self.__text_pub = self.node.create_publisher(
            String, self.__TEXT_TOPIC, qos_profile=1
        )
        self.__pixels_pub = self.node.create_publisher(
            UInt8MultiArray, self.__PIXELS_TOPIC, qos_profile=1
        )

        self.__matrix = np.zeros(
            (self.__MATRIX_ROWS, self.__MATRIX_COLS), dtype=np.uint8
        )

    def create_window(self) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.namedWindow(self.__WINDOW_NAME)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless and self.__display_found:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)

    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        arr = np.array(matrix, dtype=np.uint8)
        if arr.shape != (self.__MATRIX_ROWS, self.__MATRIX_COLS):
            print(
                f"WARNING: Matrix must be of shape "
                f"({self.__MATRIX_ROWS}, {self.__MATRIX_COLS}). Reshaping to fit."
            )
            arr = arr.reshape((self.__MATRIX_ROWS, self.__MATRIX_COLS))
        self.__matrix = arr

        msg = UInt8MultiArray()
        # dotmatrix_node treats any non-zero byte as "on", so we can publish
        # 0/1 directly without expanding to 0/255.
        msg.data = arr.flatten().tolist()
        self.__pixels_pub.publish(msg)

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def show_text(self, text: str, scroll_speed: float = 2.0) -> None:
        """
        Publishes text to the dotmatrix node, which handles font rendering
        and scrolling. The scroll_speed argument is accepted for API
        compatibility but the driver controls the actual scroll rate via its
        scroll_period_sec parameter.
        """
        msg = String()
        msg.data = text
        self.__text_pub.publish(msg)

    def set_matrix_intensity(self, intensity: float) -> None:
        """
        Intensity control lives on dotmatrix_node and is not exposed as a
        topic in the current driver. Kept as a no-op (with a one-shot
        warning) so existing labs don't crash.
        """
        assert (
            0.0 <= intensity <= 1.0
        ), f"intensity [{intensity}] must be between 0.0 and 1.0 inclusive."

        if not getattr(self, "_DisplayReal__intensity_warned", False):
            print(
                "[WARNING] rc.display.set_matrix_intensity() is a no-op on the "
                "v2 RACECAR; matrix contrast is fixed by dotmatrix_node's "
                "'contrast' parameter."
            )
            self.__intensity_warned = True
