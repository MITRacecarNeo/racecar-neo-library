"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: led_sim.py
File Description: Contains the Led module of the racecar_core library for the
simulator. Colors go to the LED strip in RacecarSim's light band: inside
start/update the frame is sent once when the call returns; anywhere else
(Jupyter) at once.
"""

import struct
from typing import List, Tuple

from led import Led

Color = Tuple[int, int, int]


class LedSim(Led):
    __NUM_PIXELS: int = 84

    def __init__(self, racecar) -> None:
        self.__racecar = racecar
        self.__pixels: List[Color] = [(0, 0, 0)] * self.__NUM_PIXELS
        self.__dirty = False

    def get_num_pixels(self) -> int:
        return self.__NUM_PIXELS

    def set_pixel(self, index: int, color: Color) -> None:
        if not 0 <= index < self.__NUM_PIXELS:
            raise IndexError(
                f"LED index {index} out of range [0, {self.__NUM_PIXELS - 1}]"
            )
        self.__pixels[index] = tuple(color)
        self.__changed()

    def set_color(self, color: Color) -> None:
        self.__pixels = [tuple(color)] * self.__NUM_PIXELS
        self.__changed()

    def set_pixels(self, colors: List[Color]) -> None:
        for i, color in enumerate(colors):
            if i >= self.__NUM_PIXELS:
                break
            self.__pixels[i] = tuple(color)
        self.__changed()

    def clear(self) -> None:
        self.__pixels = [(0, 0, 0)] * self.__NUM_PIXELS
        self.__changed()

    def get_pixels(self) -> List[Color]:
        return list(self.__pixels)

    def __changed(self) -> None:
        self.__dirty = True
        if not self.__racecar._RacecarSim__in_call:
            self.__flush()

    def __flush(self) -> None:
        """
        Sends the frame if it changed since the last send. RacecarSim calls this
        after start and after each update.
        """
        if not self.__dirty:
            return
        self.__dirty = False
        data = bytes(
            max(0, min(255, int(channel)))
            for color in self.__pixels
            for channel in color
        )
        is_async = not self.__racecar._RacecarSim__in_call
        self.__racecar._RacecarSim__send_data(
            struct.pack("B", self.__racecar.Header.led_set_pixels) + data, is_async
        )
