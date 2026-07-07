"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: led_real.py
File Description: Contains the Led module of the racecar_core library.
Publishes per-LED RGB to the driver's /led/pixels topic; pit_node forwards it
to the Teensy, which drives the WS2812B strip. When no command is sent the
Teensy shows its own battery-voltage indicator.
"""

from typing import List, Tuple

from led import Led

import rclpy as ros2
from std_msgs.msg import UInt8MultiArray

Color = Tuple[int, int, int]


class LedReal(Led):
    __TOPIC: str = "/led/pixels"

    # WS2812B strip length on the NEO-PIT board (matches firmware num_leds).
    __NUM_PIXELS: int = 84

    def __init__(self):
        self.node = ros2.create_node("led_pub")
        self.__pub = self.node.create_publisher(
            UInt8MultiArray, self.__TOPIC, qos_profile=1
        )
        self.__pixels: List[Color] = [(0, 0, 0)] * self.__NUM_PIXELS
        # pit_node forwards the LED frame only while it is fresher than its
        # display_timeout (0.5 s); a single set_* would blank after that and the
        # Teensy would fall back to its battery indicator. Once the student has
        # set the strip, keep the current frame fresh so it persists (the dot
        # matrix stays lit the same way, via dotmatrix_node's steady republish).
        self.__active = False
        self.node.create_timer(0.2, self.__keepalive)

    def __keepalive(self) -> None:
        if self.__active:
            self.__publish()

    @staticmethod
    def __clamp(v: int) -> int:
        return 0 if v < 0 else 255 if v > 255 else int(v)

    def __publish(self) -> None:
        self.__active = True
        data = []
        for r, g, b in self.__pixels:
            data.extend((self.__clamp(r), self.__clamp(g), self.__clamp(b)))
        msg = UInt8MultiArray()
        msg.data = data
        self.__pub.publish(msg)

    def get_num_pixels(self) -> int:
        return self.__NUM_PIXELS

    def set_pixel(self, index: int, color: Color) -> None:
        if not 0 <= index < self.__NUM_PIXELS:
            raise IndexError(
                f"LED index {index} out of range [0, {self.__NUM_PIXELS - 1}]"
            )
        self.__pixels[index] = tuple(color)
        self.__publish()

    def set_color(self, color: Color) -> None:
        self.__pixels = [tuple(color)] * self.__NUM_PIXELS
        self.__publish()

    def set_pixels(self, colors: List[Color]) -> None:
        for i, color in enumerate(colors):
            if i >= self.__NUM_PIXELS:
                break
            self.__pixels[i] = tuple(color)
        self.__publish()

    def clear(self) -> None:
        self.__pixels = [(0, 0, 0)] * self.__NUM_PIXELS
        self.__publish()

    def get_pixels(self) -> List[Color]:
        return list(self.__pixels)
