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
import threading
import time


# Simple 5x7 font + 1 pixel padding (6 pixels wide total)
# Each character is a list of 5 integers representing columns of 7 bits
FONT = {
    'A': [0x7e, 0x09, 0x09, 0x09, 0x7e], 'B': [0x7f, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3e, 0x41, 0x41, 0x41, 0x22], 'D': [0x7f, 0x41, 0x41, 0x22, 0x1c],
    'E': [0x7f, 0x49, 0x49, 0x49, 0x41], 'F': [0x7f, 0x09, 0x09, 0x01, 0x01],
    'G': [0x3e, 0x41, 0x41, 0x51, 0x32], 'H': [0x7f, 0x08, 0x08, 0x08, 0x7f],
    'I': [0x00, 0x41, 0x7f, 0x41, 0x00], 'J': [0x20, 0x40, 0x41, 0x3f, 0x01],
    'K': [0x7f, 0x08, 0x14, 0x22, 0x41], 'L': [0x7f, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7f, 0x02, 0x04, 0x02, 0x7f], 'N': [0x7f, 0x04, 0x08, 0x10, 0x7f],
    'O': [0x3e, 0x41, 0x41, 0x41, 0x3e], 'P': [0x7f, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3e, 0x41, 0x51, 0x21, 0x5e], 'R': [0x7f, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31], 'T': [0x01, 0x01, 0x7f, 0x01, 0x01],
    'U': [0x3f, 0x40, 0x40, 0x40, 0x3f], 'V': [0x1f, 0x20, 0x40, 0x20, 0x1f],
    'W': [0x3f, 0x40, 0x38, 0x40, 0x3f], 'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07], 'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    '0': [0x3e, 0x51, 0x49, 0x45, 0x3e], '1': [0x00, 0x42, 0x7f, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46], '3': [0x21, 0x41, 0x45, 0x4b, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7f, 0x10], '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3c, 0x4a, 0x49, 0x49, 0x30], '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36], '9': [0x06, 0x49, 0x49, 0x29, 0x1e],
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00], ',': [0x00, 0x40, 0x40, 0x30, 0x00],
    '!': [0x00, 0x00, 0x5f, 0x00, 0x00], '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00], ';': [0x00, 0x56, 0x36, 0x00, 0x00],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08], '_': [0x80, 0x80, 0x80, 0x80, 0x80],
}


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
        self.__text_thread = None
        self.__text_stop_event = None

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
        with canvas(self.device) as draw:
            for x in range(0, self.device.width):
                for y in range(0, self.device.height):
                    if self.__matrix[y][x]:
                        draw.point((x, y), fill="white")

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def show_text(
        self,
        text: str,
        scroll_speed: float = 2.0,
    ) -> None:
        self._stop_scrolling()

        # Create the full text matrix
        char_matrices = []
        for char in text.upper():
            if char in FONT:
                char_matrix = np.zeros((8, 6), dtype=np.uint8)
                font_char = FONT[char]
                for c in range(5):
                    for r in range(7):
                        if (font_char[c] >> r) & 1:
                            char_matrix[r, c] = 1
                char_matrices.append(char_matrix)

        if not char_matrices:
            self.set_matrix(np.zeros((8, 24), dtype=np.uint8))
            return

        full_matrix = np.concatenate(char_matrices, axis=1)
        full_width = full_matrix.shape[1]

        if full_width <= 24:
            # Center the text if it fits
            pad_left = (24 - full_width) // 2
            pad_right = 24 - full_width - pad_left
            display_matrix = np.pad(full_matrix, ((0, 0), (pad_left, pad_right)), 'constant')
            self.set_matrix(display_matrix)
        else:
            # Start scrolling animation in a new thread
            self.__text_stop_event = threading.Event()
            self.__text_thread = threading.Thread(
                target=self._scroll_text,
                args=(full_matrix, scroll_speed, self.__text_stop_event),
            )
            self.__text_thread.daemon = True
            self.__text_thread.start()

    def _stop_scrolling(self) -> None:
        """Stops any active text scrolling animation."""
        if self.__text_stop_event:
            self.__text_stop_event.set()
        if self.__text_thread:
            self.__text_thread.join()
        self.__text_stop_event = None
        self.__text_thread = None

    def _scroll_text(
        self,
        full_matrix: np.ndarray,
        scroll_speed: float,
        stop_event: threading.Event,
    ) -> None:
        """The thread function that handles scrolling the text."""
        full_width = full_matrix.shape[1]
        # Pad with blank space for continuous scrolling effect
        padded_matrix = np.pad(full_matrix, ((0, 0), (24, 24)), 'constant')

        start_pos = 0
        end_pos = full_width + 24

        for i in range(start_pos, end_pos):
            if stop_event.is_set():
                return

            frame = padded_matrix[:, i : i + 24]
            self.set_matrix(frame)

            # scroll_speed is in characters/sec, each char is 6px wide
            time.sleep(1.0 / (scroll_speed * 6))

        # After scrolling, show blank
        self.set_matrix(np.zeros((8, 24), dtype=np.uint8))

    def set_matrix_intensity(self, intensity: float) -> None:
        assert (
            0.0 <= intensity <= 1.0
        ), f"intensity [{intensity}] must be between 0.0 and 1.0 inclusive."

        contrast = int(intensity * 255)
        self.device.contrast(contrast)
