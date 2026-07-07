"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: led.py
File Description: Defines the interface of the Led module of the racecar_core library
"""

import abc
from typing import List, Tuple

Color = Tuple[int, int, int]


class Led(abc.ABC):
    """
    Controls the addressable RGB LED strip on the NEO-PIT board.

    Each LED is individually controllable. Colors are (red, green, blue)
    tuples with each channel in the range [0, 255].
    """

    @abc.abstractmethod
    def get_num_pixels(self) -> int:
        """
        Returns the number of LEDs on the strip.

        Example::

            n = rc.led.get_num_pixels()
        """
        pass

    @abc.abstractmethod
    def set_pixel(self, index: int, color: Color) -> None:
        """
        Sets a single LED to a color.

        Args:
            index: The LED to set, from 0 to get_num_pixels() - 1.
            color: An (red, green, blue) tuple, each channel in [0, 255].

        Example::

            # Light the first LED red
            rc.led.set_pixel(0, (255, 0, 0))
        """
        pass

    @abc.abstractmethod
    def set_color(self, color: Color) -> None:
        """
        Sets every LED to the same color.

        Args:
            color: An (red, green, blue) tuple, each channel in [0, 255].

        Example::

            # Light the whole strip green
            rc.led.set_color((0, 255, 0))
        """
        pass

    @abc.abstractmethod
    def set_pixels(self, colors: List[Color]) -> None:
        """
        Sets the strip from a list of colors, one (r, g, b) tuple per LED.

        Args:
            colors: A list of (red, green, blue) tuples. Extra entries are
                ignored; missing entries are left unchanged.

        Example::

            # A red-green gradient
            n = rc.led.get_num_pixels()
            rc.led.set_pixels([(i * 255 // n, 255 - i * 255 // n, 0) for i in range(n)])
        """
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        """
        Turns every LED off (sets the whole strip to black).

        Example::

            rc.led.clear()
        """
        pass

    @abc.abstractmethod
    def get_pixels(self) -> List[Color]:
        """
        Returns the current color of every LED as a list of (r, g, b) tuples.
        """
        pass
