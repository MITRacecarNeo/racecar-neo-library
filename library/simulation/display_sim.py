import struct

import numpy as np
import cv2 as cv
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

from display import Display


class DisplaySim(Display):
    __WINDOW_NAME: str = "RacecarSim display window"
    __ROWS: int = 8
    __COLUMNS: int = 24
    __MAX_TEXT: int = 255

    def __init__(self, racecar, isHeadless) -> None:
        Display.__init__(self, isHeadless)
        self.__racecar = racecar
        self.__matrix = np.zeros((self.__ROWS, self.__COLUMNS), dtype=np.uint8)
        self.__intensity_warned = False

    def create_window(self) -> None:
        if not self._Display__isHeadless:
            cv.namedWindow(self.__WINDOW_NAME, cv.WINDOW_NORMAL)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)

    def __send(self, data: bytes) -> None:
        # Inside start/update the sim reads the sync port; anywhere else (Jupyter)
        # the async port
        is_async = not self.__racecar._RacecarSim__in_call
        self.__racecar._RacecarSim__send_data(data, is_async)

    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        arr = np.array(matrix, dtype=np.uint8)
        if arr.shape != (self.__ROWS, self.__COLUMNS):
            print(f"WARNING: Matrix must be of shape ({self.__ROWS}, {self.__COLUMNS}). Reshaping to fit.")
            arr = arr.reshape((self.__ROWS, self.__COLUMNS))
        self.__matrix = arr
        # One bit per pixel, row-major, most significant bit first; nonzero is on
        bits = np.packbits((arr != 0).flatten())
        self.__send(struct.pack("B", self.__racecar.Header.display_set_matrix) + bits.tobytes())

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def show_text(self, text: str, scroll_speed: float = 2.0) -> None:
        """
        Sends text to RacecarSim, which scrolls text wider than the display
        across it every 4 seconds, as on the car. scroll_speed is not used.
        """
        data = str(text).encode("ascii", errors="replace")[: self.__MAX_TEXT]
        self.__send(struct.pack("BB", self.__racecar.Header.display_show_text, len(data)) + data)

    def set_matrix_intensity(self, intensity: float) -> None:
        """
        A no-op with a one-time warning, as on the car, where the matrix
        contrast is fixed.
        """
        assert (
            0.0 <= intensity <= 1.0
        ), f"intensity [{intensity}] must be between 0.0 and 1.0 inclusive."

        if not self.__intensity_warned:
            print(
                "[WARNING] rc.display.set_matrix_intensity() is a no-op; the "
                "matrix contrast is fixed, as on the v2 RACECAR."
            )
            self.__intensity_warned = True
