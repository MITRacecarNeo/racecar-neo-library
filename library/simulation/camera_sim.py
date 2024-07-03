import sys
import numpy as np
import cv2 as cv
from nptyping import NDArray

from camera import Camera


class CameraSim(Camera):
    def __init__(self, racecar) -> None:
        self.__racecar = racecar
        self.__color_image: NDArray[(480, 640, 3), np.uint8] = None
        self.__is_color_image_current: bool = False
        self.__depth_image: NDArray[(480, 640), np.float32] = None
        self.__is_depth_image_current: bool = False

        self._MAX_DEPTH_WIDTH: int = self._WIDTH // 8
        self._MAX_DEPTH_HEIGHT: int = self._HEIGHT // 8

    def get_color_image_no_copy(self) -> NDArray[(480, 640, 3), np.uint8]:
        if not self.__is_color_image_current:
            self.__color_image = self.__request_color_image(False)
            self.__is_color_image_current = True

        return self.__color_image

    def get_color_image_async(self) -> NDArray[(480, 640, 3), np.uint8]:
        return self.__request_color_image(True)

    def get_depth_image(self) -> NDArray[(480, 640), np.float32]:
        if not self.__is_depth_image_current:
            self.__depth_image = self.__request_depth_image(False)
            self.__is_depth_image_current = False

        return self.__depth_image

    def get_depth_image_async(self) -> NDArray[(480, 640), np.float32]:
        return self.__request_depth_image(True)

    def __update(self) -> None:
        self.__is_color_image_current = False
        self.__is_depth_image_current = False

    def __request_color_image(self, isAsync: bool) -> NDArray[(480, 640), np.uint8]:
        # Ask for a the current color image
        self.__racecar._RacecarSim__send_header(
            self.__racecar.Header.camera_get_color_image, isAsync
        )

        # Read the color image as 32 packets
        raw_bytes = self.__racecar._RacecarSim__receive_fragmented(
            32, self._WIDTH * self._HEIGHT * 4, isAsync
        )
        color_image = np.frombuffer(raw_bytes, dtype=np.uint8)
        color_image = np.reshape(color_image, (self._HEIGHT, self._WIDTH, 4), "C")

        color_image = cv.cvtColor(color_image, cv.COLOR_RGB2BGR)
        return color_image

    def __request_depth_image(self, isAsync: bool) -> NDArray[(480, 640), np.float32]:
        self.__racecar._RacecarSim__send_header(
            self.__racecar.Header.camera_get_depth_image, isAsync
        )
        raw_bytes: bytes = self.__racecar._RacecarSim__receive_data(
            self._MAX_DEPTH_WIDTH * self._MAX_DEPTH_HEIGHT * 4
        )
        depth_image = np.frombuffer(raw_bytes, dtype=np.float32)

        # Calculate received height and width
        n: int = (len(depth_image) // 300).bit_length() // 2
        depth_width: int = 20 * 1 << n
        depth_height: int = 15 * 1 << n

        # Reshape and resize to full resolution
        depth_image = np.reshape(depth_image, (depth_height, depth_width), "C")
        depth_image = cv.resize(
            depth_image, (self._WIDTH, self._HEIGHT), interpolation=cv.INTER_AREA
        )
        return depth_image
