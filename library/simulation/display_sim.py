import numpy as np
import cv2 as cv
from nptyping import NDArray
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
import threading
import time

from display import Display

# Simple 7x5 font + 1 pixel padding (6 pixels wide total)
# Each character is a list of 5 hexadecimal integers representing columns of 7 bits.
# Each bit in an integer corresponds to a pixel in a column.
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


class DisplaySim(Display):
    __WINDOW_NAME: str = "RacecarSim display window"

    def __init__(self, isHeadless) -> None:
        Display.__init__(self, isHeadless)
        self.__matrix = np.zeros((8, 24), dtype=np.uint8)
        self.__intensity = 1.0  # Default intensity
        self._console = Console()
        self._live = None
        # Threading attributes for text scrolling animation
        self.__text_thread = None
        self.__text_stop_event = None

    def create_window(self) -> None:
        if not self._Display__isHeadless:
            cv.namedWindow(self.__WINDOW_NAME, cv.WINDOW_NORMAL)

    def show_color_image(self, image: NDArray) -> None:
        if not self._Display__isHeadless:
            cv.imshow(self.__WINDOW_NAME, image)
            cv.waitKey(1)

    def _start_live(self) -> None:
        if not self._Display__isHeadless and self._live is None:
            self._live = Live(
                self._render_matrix(), console=self._console, refresh_per_second=10
            )
            self._live.start()

    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        arr = np.array(matrix, dtype=np.uint8)
        if arr.shape != (8, 24):
            print("WARNING: Matrix must be of shape (8, 24). Reshaping to fit.")
            arr = arr.reshape((8, 24))
        self.__matrix = arr
        self._draw_matrix()

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def show_text(
        self,
        text: str,
        scroll_speed: float = 2.2,
    ) -> None:
        """
        Displays text on the 8x24 matrix. If the text is too long, it scrolls.

        Args:
            text: The string to display.
            scroll_speed: The scrolling speed in characters per second.
        """
        # Stop any existing scrolling animation before starting a new one
        self._stop_scrolling()

        # Create the full text matrix by converting each character into a bitmap
        char_matrices = []
        for char in text.upper():
            if char in FONT:
                # Create an 8x6 matrix for each character (7x5 font + 1px padding)
                char_matrix = np.zeros((8, 6), dtype=np.uint8)
                font_char = FONT[char]
                # Iterate through each of the 5 columns of the character's font data
                for c in range(5):
                    # Iterate through the 7 bits of the column data to draw pixels
                    for r in range(7):
                        # If the bit is 1, draw a pixel
                        if (font_char[c] >> r) & 1:
                            # Center the 6-pixel high font in the 8-pixel matrix
                            char_matrix[r + 1, c] = 1
                char_matrices.append(char_matrix)

        if not char_matrices:
            self.set_matrix(np.zeros((8, 24), dtype=np.uint8))
            return

        # Combine all character matrices into a single wide matrix
        full_matrix = np.concatenate(char_matrices, axis=1)
        full_width = full_matrix.shape[1]

        # If the text fits on the display, center it
        if full_width <= 24:
            # Center the text if it fits
            pad_left = (24 - full_width) // 2
            pad_right = 24 - full_width - pad_left
            display_matrix = np.pad(
                full_matrix, ((0, 0), (pad_left, pad_right)), "constant"
            )
            self.set_matrix(display_matrix)
        # If the text is too long, scroll it
        else:
            # Start scrolling animation in a new thread to avoid blocking the main program
            self.__text_stop_event = threading.Event()
            self.__text_thread = threading.Thread(
                target=self._scroll_text,
                args=(full_matrix, scroll_speed, self.__text_stop_event),
            )
            self.__text_thread.daemon = True
            self.__text_thread.start()

    def _stop_scrolling(self) -> None:
        """Stops any active text scrolling animation by setting an event and joining the thread."""
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
        # Pad with blank space for a smooth scrolling effect on and off the screen
        padded_matrix = np.pad(full_matrix, ((0, 0), (24, 24)), "constant")

        start_pos = 0
        end_pos = full_width + 24

        # Loop through the padded matrix, showing one 24-pixel frame at a time
        for i in range(start_pos, end_pos):
            # Exit the thread if the stop event is set
            if stop_event.is_set():
                return

            # Extract the current 8x24 frame to display
            frame = padded_matrix[:, i : i + 24]
            self.set_matrix(frame)

            # Pause to control the scrolling speed
            # scroll_speed is in characters/sec, each char is 6px wide
            time.sleep(1.0 / (scroll_speed * 6))

        # After scrolling, clear the display
        self.set_matrix(np.zeros((8, 24), dtype=np.uint8))

    def set_matrix_intensity(self, intensity: float) -> None:
        self.__intensity = intensity

    def _draw_matrix(self) -> None:
        if self._Display__isHeadless:
            return
        if self._live is None:
            self._start_live()
        self._live.update(self._render_matrix())

    def _render_matrix(self) -> Panel:
        table = Table(
            show_header=False,
            pad_edge=False,
            padding=(0, 0),
            border_style="white",
            show_lines=True,
        )
        for _ in range(24):
            table.add_column(no_wrap=True)
        color = int(self.__intensity * 255)
        for y in range(8):
            row = []
            for x in range(24):
                if self.__matrix[y, x]:
                    # "On" cell: red with thin white border
                    row.append(f"[bold red on rgb({color},{0},{0})]  [/]")
                else:
                    # "Off" cell: black with thin white border
                    row.append("  ")
            table.add_row(*row)
        return Panel(table, title="Dot Matrix Display", border_style="black")
