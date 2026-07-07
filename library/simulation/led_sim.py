"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: led_sim.py
File Description: Contains the Led module of the racecar_core library for the
simulator. The Unity sim has no RGB strip yet, so this keeps a local buffer and
is otherwise a no-op; the same student code runs unchanged in sim and on the car.
"""

from typing import List, Tuple

from led import Led

Color = Tuple[int, int, int]


class LedSim(Led):
    __NUM_PIXELS: int = 84

    def __init__(self, racecar=None):
        self.__pixels: List[Color] = [(0, 0, 0)] * self.__NUM_PIXELS

    def get_num_pixels(self) -> int:
        return self.__NUM_PIXELS

    def set_pixel(self, index: int, color: Color) -> None:
        if 0 <= index < self.__NUM_PIXELS:
            self.__pixels[index] = tuple(color)

    def set_color(self, color: Color) -> None:
        self.__pixels = [tuple(color)] * self.__NUM_PIXELS

    def set_pixels(self, colors: List[Color]) -> None:
        for i, color in enumerate(colors):
            if i >= self.__NUM_PIXELS:
                break
            self.__pixels[i] = tuple(color)

    def clear(self) -> None:
        self.__pixels = [(0, 0, 0)] * self.__NUM_PIXELS

    def get_pixels(self) -> List[Color]:
        return list(self.__pixels)
