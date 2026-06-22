"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: display.py
File Description: Defines the interface of the Display module of the racecar_core library.
"""

import abc
import numpy as np
import math
from typing import Any
from nptyping import NDArray

import racecar_utils as rc_utils


class Display(abc.ABC):
    """
    Allows the user to print images to the screen.
    """

    # The radii dots used to indicate points
    __BIG_DOT_RADIUS = 8
    __SMALL_DOT_RADIUS = 4
    __LIDAR_CAR_RADIUS = 2

    def __init__(self, isHeadless: bool) -> None:
        self.__isHeadless = isHeadless

    @abc.abstractmethod
    def create_window(self) -> None:
        """
        Creates an empty window into which images will be displayed.

        Note:
            It is not necessary to call create_window before any of the other display
            methods (show_color_image, show_depth_image, etc.).  These methods will
            automatically create a new window if one was not already created.

        Example::

            # Creates a window
            rc.camera.create_window()

            # Display an image in this window
            image = rc.camera.get_color_image()
            rc.display.show_color_image(image)
        """
        pass

    @abc.abstractmethod
    def show_color_image(self, image: NDArray) -> None:
        """
        Displays a color image in a window.

        Args:
            image: The color image to display to the screen.

        Example::

            image = rc.camera.get_color_image()

            # Show the image captured by the camera
            rc.display.show_color_image(image)
        """
        pass

    def show_depth_image(
        self,
        image: NDArray[(Any, Any), np.float32],
        max_depth: int = 1000,
        points: list[tuple[int, int]] = [],
    ) -> None:
        """
        Displays a depth image in grayscale in a window.

        Args:
            image: The depth image to display to the screen.
            max_depth: The farthest depth to show in the image in cm. Anything past
                this depth is shown as black.
            points: A list of points in (pixel row, pixel column) format to show on
                the image as colored dots.

        Example::

            depth_image = rc.camera.get_depth_image()

            # Show the depth_image captured by the camera.
            rc.display.show_depth_image(depth_image)

            # Show anything that is at most 500 cm away, and show a black cross at
            # row 3, column 5
            rc.display.show_depth_image(depth_image, 500, [(3, 5)])
        """
        if self.__isHeadless:
            return

        assert max_depth > 0, "max_depth must be positive."
        for point in points:
            assert (
                0 <= point[0] < image.shape[0] and 0 <= point[1] < image.shape[1]
            ), f"The point [{point}] is not a valid pixel row and column within image."

        color_image = rc_utils.colormap_depth_image(image, max_depth)

        # Draw a dot at each point in points
        for point in points:
            rc_utils.draw_circle(
                color_image,
                point,
                rc_utils.ColorBGR.green.value,
                radius=self.__BIG_DOT_RADIUS,
            )
            rc_utils.draw_circle(
                color_image,
                point,
                rc_utils.ColorBGR.blue.value,
                radius=self.__SMALL_DOT_RADIUS,
            )

        self.show_color_image(color_image)

    def show_lidar(
        self,
        samples: NDArray[Any, np.float32],
        radius: int = 128,
        max_range: int = 1000,
        highlighted_samples: list[tuple[float, float]] = [],
    ) -> None:
        """
        Displays a set of LIDAR samples.

        Args:
            samples: A complete LIDAR scan.
            radius: Half of the width or height (in pixels) of the generated image.
            max_range: The farthest depth to show in the image in cm.  Anything past
                this depth is shown as black.
            highlighted_samples: A list of samples in (angle, distance) format to show
                as light blue dots.  Angle must be in degrees from straight ahead
                (clockwise), and distance must be in cm.

        Note:
            Each sample in samples is shown as a red pixel.  Each sample in
            highlighted_samples is shown as a blue pixel.  The car is shown as a green
            dot at the center of the visualization.

        Warning:
            samples must be a complete LIDAR scan.  This function assumes that each
            sample is equal angle apart, and that samples spans the entire 360 degrees.
            If this is not the case, the visualization will be inaccurate.

        Example::

            lidar_scan = rc.lidar.get_samples()

            # Show the lidar scan
            rc.display.show_lidar(lidar_scan)

            # Show the lidar scan out to 500 cm with the closest point highlighted
            closest_point = rc_utils.get_lidar_closest_point(lidar_scan)
            rc.display.show_lidar(lidar_scan, 500, [closest_point])
        """
        assert radius > 0, "radius must be positive."
        assert max_range > 0, "max_range must be positive."

        if self.__isHeadless:
            return

        # Create a square black image with the requested radius
        image = np.zeros((2 * radius, 2 * radius, 3), np.uint8, "C")
        num_samples: int = len(samples)

        # Draw a red pixel for each non-zero sample less than max_range
        for i in range(num_samples):
            if 0 < samples[i] < max_range:
                angle: float = 2 * math.pi * i / num_samples
                length: float = radius * samples[i] / max_range
                r: int = int(radius - length * math.cos(angle))
                c: int = int(radius + length * math.sin(angle))
                image[r][c][2] = 255

        # Draw a green dot to denote the car
        rc_utils.draw_circle(
            image,
            (radius, radius),
            rc_utils.ColorBGR.green.value,
            self.__LIDAR_CAR_RADIUS,
        )

        # Draw a light blue pixel for each point in highlighted_samples
        for (angle, distance) in highlighted_samples:
            if 0 < distance < max_range:
                angle_rad = angle * math.pi / 180
                length: float = radius * distance / max_range
                r: int = int(radius - length * math.cos(angle_rad))
                c: int = int(radius + length * math.sin(angle_rad))
                image[r][c][0] = 255
                image[r][c][1] = 255
                image[r][c][2] = 0

        self.show_color_image(image)

    @abc.abstractmethod
    def set_matrix(self, matrix: NDArray[(8, 24), np.uint8]) -> None:
        """
        Sets the dot matrix display module to the pattern in the argument (2D matrix).

        Args:
            matrix: The 8x24 NumPy array with the pattern to be displayed on the dot
                matrix display module.

        Note:
            A 1 in the matrix indicates an LED that is on, while a 0 in the
            matrix indicates an LED that is off.

        Example::

            dot_matrix = np.ones((8, 24), dtype=np.uint8)

            # Turn all the LEDs on the dot matrix module on
            rc.display.set_matrix(dot_matrix)

        """
        pass

    @abc.abstractmethod
    def show_text(
        self,
        text: str,
        scroll_speed: float = 2.0
    ) -> None:
        """
        Displays text on the 8x24 matrix. If the text is too long, it scrolls.

        Args:
            text: The string to display.
            scroll_speed: The scrolling speed in characters per second.

        Example::

            # Display a message on the LED matrix
            rc.display.show_text("Hello, Racecar!")

            # Display a long message that will scroll
            rc.display.show_text("This message is too long to fit and will scroll", scroll_speed=3)
        """
        pass


    @abc.abstractmethod
    def get_matrix(self) -> NDArray[(8, 24), np.uint8]:
        """
        Returns the current configuration of the dot matrix display module.

        Returns:
            An 8x24 NumPy array (data type: np.uint8) representing the current
            configuration of the dot matrix display module.

        Note:
            A 1 in the matrix indicates an LED that is on, while a 0 in the
            matrix indicates an LED that is off.

        Example::

            # Gets current configuration values of the dot matrix module
            dot_matrix = rc.display.get_matrix()
        """
        pass

    def new_matrix(self) -> NDArray[(8, 24), np.uint8]:
        """
        Returns a new matrix of all zeroes for the dot matrix display module.

        Returns:
            An 8x24 NumPy array (data type: np.uint8) of all zeroes.

        Example::

            # Create a new matrix of all zeroes.
            my_matrix = rc.display.new_matrix()

            # Set the top left pixel to on, then display the matrix on the dot matrix.
            my_matrix[0, 0] = 1
            rc.display.set_matrix(my_matrix)
        """
        return np.zeros((8, 24), dtype=np.uint8)

    @abc.abstractmethod
    def set_matrix_intensity(self, intensity: float) -> None:
        """
        Sets the intensity of the dot matrix display module.

        Args:
            intensity: The LED intensity (between 0.0 and 1.0) to set.

        Note:
            Due to the way the racecar's LED driver works, an intensity of 0.0 does *not*
            correspond to turning the LEDs completely off, and therefore `set_matrix_intensity`
            cannot be used to make a fade-in or fade-out animation.

        Example::

            # Pulse the dot matrix display using a sin wave profile.
            def update():
                global time
                time += rc.get_delta_time()

                intensity = rc_utils.remap_range(math.sin(time), -1.0, 1.0, 0.0, 1.0)
                rc.display.set_matrix_intensity(intensity)
        """
        pass
