import cv2 as cv
import numpy as np
from nptyping import NDArray

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

from display import Display


class DisplaySim(Display):
    __WINDOW_NAME: str = "RacecarSim display window"

    def __init__(self, isHeadless) -> None:
        Display.__init__(self, isHeadless)

        self.__matrix = np.zeros((8, 24), dtype=np.uint8)
        self.__intensity = 1.0  # Default intensity
        self._console = Console()
        self._live = None

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
            print("WARNING: Array is not properly formatted.")
            arr = arr.reshape((8, 24))
        self.__matrix = arr
        self._draw_matrix()

    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        return self.__matrix

    def set_matrix_intensity(self, intensity: float) -> None:
        self.__intensity = intensity

    def _draw_matrix(self) -> None:
        if self._Display__isHeadless:
            return
        if self._live is None:
            self._start_live()
        self._live.update(self._render_matrix())

    def _render_matrix(self) -> Panel:
        table = Table(show_header=False, pad_edge=False, padding=(0,0), border_style="white", show_lines=True)
        for _ in range(24):
            table.add_column(no_wrap=True)
        color = int(self.__intensity * 255)
        for y in range(8):
            row = []
            for x in range(24):
                if self.__matrix[y, x]:
                    row.append(f"[bold red on rgb({color},{0},{0})] [/]")
                else:
                    row.append(" ")
            table.add_row(*row)
        return Panel(table, title=self.__WINDOW_NAME)
