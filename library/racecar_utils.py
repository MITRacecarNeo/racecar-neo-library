"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: racecar_utils.py
File Description: Contains helper functions to support common operations.
"""

import cv2 as cv
import numpy as np
from typing import Any, Optional
from nptyping import NDArray
from enum import Enum, IntEnum


########################################################################################
# General
########################################################################################


class TerminalColor(IntEnum):
    """
    Colors which can be used when printing text to the terminal, with each value
    corresponding to the ASCII code for that color.
    """

    black = 30
    dark_red = 31
    dark_green = 32
    orange = 33
    dark_blue = 34
    purple = 35
    dark_cyan = 36
    light_grey = 37
    dark_grey = 90
    red = 91
    green = 92
    yellow = 93
    blue = 94
    pink = 95
    cyan = 96


def format_colored(text: str, color: TerminalColor) -> str:
    """
    Formats a string so that it is printed to the terminal with a specified color.

    Args:
        text: The text to format.
        color: The color to print the text.

    Example::

        # Prints "Hello World!", where "World" is blue
        print("Hello " + format_colored("World", rc_utils.TerminalColor.blue) + "!")
    """
    return f"\033[{color.value}m{text}\033[00m"


def print_colored(text: str, color: TerminalColor) -> None:
    """
    Prints a line of text to the terminal with a specified color.

    Args:
        text: The text to print to the terminal.
        color: The color to print the text.

    Example::

        rc_utils.print_colored("This will be black", rc_utils.TerminalColor.black)
        rc_utils.print_colored("This will be red", rc_utils.TerminalColor.red)
        rc_utils.print_colored("This will be green", rc_utils.TerminalColor.green)
    """
    print(format_colored(text, color))


def print_error(text: str) -> None:
    """
    Prints a line of text to the terminal in red.

    Args:
        text: The text to print to the terminal.

    Example::

        # This text will be printed to the terminal in red
        rc_utils.print_error("Error: No image detected")
    """
    print_colored(text, TerminalColor.red)


def print_warning(text: str) -> None:
    """
    Prints a line of text to the terminal in yellow.

    Args:
        text: The text to print to the terminal.

    Example::

        # This text will be printed to the terminal in yellow
        rc_utils.print_warning("Warning: Potential collision detected, reducing speed")
    """
    print_colored(text, TerminalColor.yellow)


def clamp(value: float, min: float, max: float) -> float:
    """
    Clamps a value between a minimum and maximum value.

    Args:
        value: The input to clamp.
        min: The minimum allowed value.
        max: The maximum allowed value.

    Returns:
        The value saturated between min and max.

    Example::

        # a will be set to 3
        a = rc_utils.clamp(3, 0, 10)

        # b will be set to 0
        b = rc_utils.clamp(-2, 0, 10)

        # c will be set to 10
        c = rc_utils.clamp(11, 0, 10)
    """
    return min if value < min else max if value > max else value


def remap_range(
    val: float,
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
    saturate: bool = False,
) -> float:
    """
    Remaps a value from one range to another range.

    Args:
        val: A number form the old range to be rescaled.
        old_min: The inclusive 'lower' bound of the old range.
        old_max: The inclusive 'upper' bound of the old range.
        new_min: The inclusive 'lower' bound of the new range.
        new_max: The inclusive 'upper' bound of the new range.
        saturate: If true, the new_min and new_max limits are enforced.

    Note:
        min need not be less than max; flipping the direction will cause the sign of
        the mapping to flip.  val does not have to be between old_min and old_max.

    Example::

        # a will be set to 25
        a = rc_utils.remap_range(5, 0, 10, 0, 50)

        # b will be set to 975
        b = rc_utils.remap_range(5, 0, 20, 1000, 900)

        # c will be set to 30
        c = rc_utils.remap_range(2, 0, 1, -10, 10)

        # d will be set to 10
        d = rc_utils.remap_range(2, 0, 1, -10, 10, True)
    """
    old_span: float = old_max - old_min
    new_span: float = new_max - new_min
    new_val: float = new_min + new_span * (float(val - old_min) / float(old_span))

    # If saturate is true, enforce the new_min and new_max limits
    if saturate:
        if new_min < new_max:
            return clamp(new_val, new_min, new_max)
        else:
            return clamp(new_val, new_max, new_min)

    return new_val


########################################################################################
# Images (General)
########################################################################################


def crop(
    image: NDArray[(Any, ...), Any],
    top_left_inclusive: tuple[float, float],
    bottom_right_exclusive: tuple[float, float],
) -> NDArray[(Any, ...), Any]:
    """
    Crops an image to a rectangle based on the specified pixel points.

    Args:
        image: The color or depth image to crop.
        top_left_inclusive: The (row, column) of the top left pixel
            of the crop rectangle.
        bottom_right_exclusive: The (row, column) of the pixel one
            past the bottom right corner of the crop rectangle.

    Returns:
        A cropped version of the image.

    Note:
        The top_left_inclusive pixel is included in the crop rectangle, but the
        bottom_right_exclusive pixel is not.

        If bottom_right_exclusive exceeds the bottom or right edge of the image, the
        full image is included along that axis.

    Example::

        image = rc.camera.get_color_image()

        # Crop the image to only keep the top half
        cropped_image = rc_utils.crop(
            image, (0, 0), (rc.camera.get_height() // 2, rc.camera.get_width())
        )
    """
    assert (
        0 <= top_left_inclusive[0] < image.shape[0]
    ), f"top_left_inclusive[0] ({top_left_inclusive[0]}) must be a pixel row index in color_image."

    assert (
        0 <= top_left_inclusive[1] < image.shape[1]
    ), f"top_left_inclusive[1] ({top_left_inclusive[1]}) must be a pixel column index in color_image."

    assert (
        bottom_right_exclusive[0] > 0 and bottom_right_exclusive[1] > 0
    ), f"The row and column in bottom_right_exclusive ({bottom_right_exclusive}) must be positive."

    # Extract the minimum and maximum pixel rows and columns from the parameters
    r_min, c_min = top_left_inclusive
    r_max, c_max = bottom_right_exclusive

    # Shorten the array to the specified row and column ranges
    return image[r_min:r_max, c_min:c_max]


def stack_images_horizontal(
    image_0: NDArray[(Any, ...), Any],
    image_1: NDArray[(Any, ...), Any]
) -> NDArray[(Any, ...), Any]:
    """
    Stack two images horizontally.

    Args:
        image_0: The image to place on the left.
        image_1: The image to place on the right.

    Returns:
        An image with the original two images next to each other.

    Note:
        The images must have the same height.

    Example::

        color_image = rc.camera.get_color_image()

        depth_image = rc.camera.get_depth_image()
        depth_image_colormap = rc_utils.colormap_depth_image(depth_image)

        # Create a new image with the color on the left and depth on the right
        new_image = rc_utils.stack_images_horizontally(color_image, depth_image_colormap)
    """
    assert (
        image_0.shape[0] == image_1.shape[0]
    ), f"image_0 height ({image_0.shape[0]}) must be the same as image_1 height ({image_1.shape[0]})."

    return np.hstack((image_0, image_1))


def stack_images_vertical(
    image_0: NDArray[(Any, ...), Any],
    image_1: NDArray[(Any, ...), Any]
) -> NDArray[(Any, ...), Any]:
    """
    Stack two images vertically.

    Args:
        image_0: The image to place on the top.
        image_1: The image to place on the bottom.

    Returns:
        An image with the original two images on top of each other.

    Note:
        The images must have the same width.

    Example::

        color_image = rc.camera.get_color_image()

        depth_image = rc.camera.get_depth_image()
        depth_image_colormap = rc_utils.colormap_depth_image(depth_image)

        # Create a new image with the color on the top and depth on the bottom
        new_image = rc_utils.stack_images_vertically(color_image, depth_image_colormap)
    """
    assert (
        image_0.shape[1] == image_1.shape[1]
    ), f"image_0 width ({image_0.shape[1]}) must be the same as image_1 width ({image_1.shape[1]})."

    return np.vstack((image_0, image_1))


########################################################################################
# Color Images
########################################################################################


class ColorBGR(Enum):
    """
    Common colors defined in the blue-green-red (BGR) format, with each channel
    ranging from 0 to 255 inclusive.
    """

    blue = (255, 0, 0)
    light_blue = (255, 255, 0)
    green = (0, 255, 0)
    dark_green = (0, 127, 0)
    yellow = (0, 255, 255)
    orange = (0, 127, 255)
    red = (0, 0, 255)
    pink = (255, 0, 255)
    purple = (255, 0, 127)
    black = (0, 0, 0)
    dark_gray = (63, 63, 63)
    gray = (127, 127, 127)
    light_gray = (191, 191, 191)
    white = (255, 255, 255)
    brown = (0, 63, 127)


def find_contours(
    color_image: NDArray[(Any, Any, 3), np.uint8],
    hsv_lower: tuple[int, int, int],
    hsv_upper: tuple[int, int, int],
) -> list[NDArray]:
    """
    Finds all contours of the specified color range in the provided image.

    Args:
        color_image: The color image in which to find contours,
            with pixels represented in the bgr (blue-green-red) format.
        hsv_lower: The lower bound for the hue, saturation, and value of colors
            to contour.
        hsv_upper: The upper bound for the hue, saturation, and value of the colors
            to contour.

    Returns:
        A list of contours around the specified color ranges found in color_image.

    Note:
        Each channel in hsv_lower and hsv_upper ranges from 0 to 255.

    Example::

        # Define the lower and upper hsv ranges for the color blue
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)

        # Extract contours around all blue portions of the current image
        contours = rc_utils.find_contours(
            rc.camera.get_color_image(), BLUE_HSV_MIN, BLUE_HSV_MAX
        )
    """
    assert (
        0 <= hsv_lower[0] <= 179 and 0 <= hsv_upper[0] <= 179
    ), f"The hue of hsv_lower ({hsv_lower}) and hsv_upper ({hsv_upper}) must be in the range 0 to 179 inclusive."

    assert (
        0 <= hsv_lower[1] <= 255 and 0 <= hsv_upper[1] <= 255
    ), f"The saturation of hsv_lower ({hsv_lower}) and hsv_upper ({hsv_upper}) must be in the range 0 to 255 inclusive."

    assert (
        0 <= hsv_lower[0] <= 255 and 0 <= hsv_upper[0] <= 255
    ), f"The value of hsv_lower ({hsv_lower}) and hsv_upper ({hsv_upper}) must be in the range 0 to 255 inclusive."

    assert (
        hsv_lower[1] <= hsv_upper[1]
    ), f"The saturation channel of hsv_lower ({hsv_lower}) must be less than that of hsv_upper ({hsv_upper})."

    assert (
        hsv_lower[2] <= hsv_upper[2]
    ), f"The value channel of hsv_lower ({hsv_lower}) must be less than that of of hsv_upper ({hsv_upper})."

    # Convert the image from a blue-green-red pixel representation to a
    # hue-saturation-value representation
    hsv_image = cv.cvtColor(color_image, cv.COLOR_BGR2HSV)

    # Create a mask containing the pixels in the image with hsv values between
    # hsv_lower and hsv_upper.
    mask: NDArray
    if hsv_lower[0] <= hsv_upper[0]:
        mask = cv.inRange(hsv_image, hsv_lower, hsv_upper)

    # If the color range passes the 255-0 boundary, we must create two masks
    # and merge them
    else:
        mask1 = cv.inRange(hsv_image, hsv_lower, (255, hsv_upper[1], hsv_upper[2]))
        mask2 = cv.inRange(hsv_image, (0, hsv_lower[1], hsv_lower[2]), hsv_upper)
        mask = cv.bitwise_or(mask1, mask2)

    # Find and return a list of all contours of this mask
    return cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)[0]


def get_largest_contour(
    contours: list[NDArray],
    min_area: int = 30
) -> Optional[NDArray]:
    """
    Finds the largest contour with size greater than min_area.

    Args:
        contours: A list of contours found in an image.
        min_area: The smallest contour to consider (in number of pixels)

    Returns:
        The largest contour from the list, or None if no contour was larger
        than min_area.

    Example::

        # Extract the blue contours
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)
        contours = rc_utils.find_contours(
            rc.camera.get_color_image(), BLUE_HSV_MIN, BLUE_HSV_MAX
        )

        # Find the largest contour
        largest_contour = rc_utils.get_largest_contour(contours)
    """
    # Check that the list contains at least one contour
    if len(contours) == 0:
        return None

    # Find and return the largest contour if it is larger than min_area
    greatest_contour = max(contours, key=cv.contourArea)
    if cv.contourArea(greatest_contour) < min_area:
        return None

    return greatest_contour


def draw_contour(
    color_image: NDArray[(Any, Any, 3), np.uint8],
    contour: NDArray,
    color: tuple[int, int, int] = ColorBGR.green.value,
) -> None:
    """
    Draws a contour on the provided image.

    Args:
        color_image: The color image on which to draw the contour.
        contour: The contour to draw on the image.
        color: The color to draw the contour, specified as
            blue-green-red channels each ranging from 0 to 255 inclusive.

    Example::

        image = rc.camera.get_color_image()

        # Extract the largest blue contour
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)
        contours = rc_utils.find_contours(image, BLUE_HSV_MIN, BLUE_HSV_MAX)
        largest_contour = rc_utils.get_largest_contour(contours)

        # Draw this contour onto image
        if (largest_contour is not None):
            draw_contour(image, largest_contour)
    """
    for channel in color:
        assert (
            0 <= channel <= 255
        ), f"Each channel in color ({color}) must be in the range 0 to 255 inclusive."

    cv.drawContours(color_image, [contour], 0, color, 3)


def draw_circle(
    color_image: NDArray[(Any, Any, 3), np.uint8],
    center: tuple[int, int],
    color: tuple[int, int, int] = ColorBGR.yellow.value,
    radius: int = 6,
) -> None:
    """
    Draws a circle on the provided image.

    Args:
        color_image: The color image on which to draw the contour.
        center: The pixel (row, column) of the center of the image.
        color: The color to draw the circle, specified as
            blue-green-red channels each ranging from 0 to 255 inclusive.
        radius: The radius of the circle in pixels.

    Example::

        image = rc.camera.get_color_image()

        # Extract the largest blue contour
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)
        contours = rc_utils.find_contours(image, BLUE_HSV_MIN, BLUE_HSV_MAX)
        largest_contour = rc_utils.get_largest_contour(contours)

        # Draw a dot at the center of this contour in red
        if (largest_contour is not None):
            center = get_contour_center(contour)
            draw_circle(image, center, rc_utils.ColorBGR.red.value)
    """
    for channel in color:
        assert (
            0 <= channel <= 255
        ), f"Each channel in color ({color}) must be in the range 0 to 255 inclusive."

    assert (
        0 <= center[0] < color_image.shape[0]
    ), f"center[0] ({center[0]}) must be a pixel row index in color_image."
    assert (
        0 <= center[1] < color_image.shape[1]
    ), f"center[1] ({center[1]}) must be a pixel column index in color_image."
    assert radius > 0, f"radius ({radius}) must be a positive integer."

    # cv.circle expects the center in (column, row) format
    cv.circle(color_image, (center[1], center[0]), radius, color, -1)


def get_contour_center(contour: NDArray) -> Optional[tuple[int, int]]:
    """
    Finds the center of a contour from an image.

    Args:
        contour: The contour of which to find the center.

    Returns:
        The (row, column) of the pixel at the center of the contour, or None if the
        contour is empty.

    Example::

        # Extract the largest blue contour
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)
        contours = rc_utils.find_contours(
            rc.camera.get_color_image(), BLUE_HSV_MIN, BLUE_HSV_MAX
        )
        largest_contour = rc_utils.get_largest_contour(contours)

        # Find the center of this contour if it exists
        if (largest_contour is not None):
            center = rc_utils.get_contour_center(largest_contour)
    """
    M = cv.moments(contour)

    # Check that the contour is not empty
    # (M["m00"] is the number of pixels in the contour)
    if M["m00"] <= 0:
        return None

    # Compute and return the center of mass of the contour
    center_row = round(M["m01"] / M["m00"])
    center_column = round(M["m10"] / M["m00"])
    return center_row, center_column


def get_contour_area(contour: NDArray) -> float:
    """
    Finds the area of a contour from an image.

    Args:
        contour: The contour of which to measure the area.

    Returns:
        The number of pixels contained within the contour

    Example::

        # Extract the largest blue contour
        BLUE_HSV_MIN = (90, 50, 50)
        BLUE_HSV_MAX = (110, 255, 255)
        contours = rc_utils.find_contours(
            rc.camera.get_color_image(), BLUE_HSV_MIN, BLUE_HSV_MAX
        )
        largest_contour = rc_utils.get_largest_contour(contours)

        # Find the area of this contour (will evaluate to 0 if no contour was found)
        area = rc_utils.get_contour_area(contour)
    """
    return cv.contourArea(contour)


def pixelate_image(
    img: NDArray[np.uint8],
    size: tuple[int, int] = (24, 8)
) -> NDArray[np.uint8]:
    """
    "Pixelates" and resizes a grayscale image to a smaller size, useful for
    displaying pictures on the dot matrix.

    Args:
        img: The grayscale image to pixelate.
        size: The smaller width and height to pixelate the image to.
            By default, this resizes the image to the correct size for the
            dot matrix display.

    Returns:
        The pixelated image.

    Example::

        # Load and pixelate a black-and-white image
        img = cv.imread('./frames/bad_apple_080.png', cv.IMREAD_GRAYSCALE)
        pixelated = rc_utils.pixelate_image(img)

        # Display the image on the dot matrix
        rc.display.set_matrix(pixelated)
    """
    w, h = size
    return cv.resize(img, (w, h), interpolation=cv.INTER_LINEAR)


########################################################################################
# Depth Images
########################################################################################


def get_depth_image_center_distance(
    depth_image: NDArray[(Any, Any), np.float32],
    kernel_size: int = 5
) -> float:
    """
    Finds the distance of the center object in a depth image.

    Args:
        depth_image: The depth image to process.
        kernel_size: The size of the area to average around the center.

    Returns:
        The distance in cm of the object in the center of the image.

    Warning:
        kernel_size must be positive and odd.

    Note:
        The larger the kernel_size, the more that the center is averaged
        with the depth of the surrounding pixels.  This helps reduce noise at the cost
        of reduced accuracy.  If kernel_size = 1, no averaging is done.

    Example::

        depth_image = rc.camera.get_depth_image()

        # Find the distance of the object (in cm) the center of depth_image
        center_distance = rc_utils.get_depth_image_center_distance(depth_image)
    """
    assert (
        kernel_size > 0 and kernel_size % 2 == 1
    ), f"kernel_size ({kernel_size}) must positive and odd."

    # Calculate the center pixel
    center_coords = (depth_image.shape[0] // 2, depth_image.shape[1] // 2)

    # Use get_average_distance to average the distance around this center pixel
    return get_pixel_average_distance(depth_image, center_coords, kernel_size)


def get_pixel_average_distance(
    depth_image: NDArray[(Any, Any), np.float32],
    pix_coord: tuple[int, int],
    kernel_size: int = 5,
) -> float:
    """
    Finds the distance of a pixel averaged with its neighbors in a depth image.

    Args:
        depth_image: The depth image to process.
        pix_coord: The (row, column) of the pixel to measure.
        kernel_size: The size of the area to average around the pixel.

    Returns:
        The distance in cm of the object at the provided pixel.

    Warning:
        kernel_size must be positive and odd.

    Note:
        The larger the kernel_size, the more that the requested pixel is averaged
        with the distances of the surrounding pixels.  This helps reduce noise at the
        cost of reduced accuracy.

    Example::

        depth_image = rc.camera.get_depth_image()

        # Find the distance of the object (in cm) at the pixel (100, 20) of depth_image
        average_distance = rc_utils.get_average_distance(depth_image, 100, 20)
    """
    (pix_row, pix_col) = pix_coord
    assert (
        0 <= pix_row < depth_image.shape[0]
    ), f"pix_coord[0] ({pix_coord[0]}) must be a pixel row index within depth_image."
    assert (
        0 <= pix_col < depth_image.shape[1]
    ), f"pix_coord[1] ({pix_coord[1]}) must be a pixel column index within depth_image."
    assert (
        kernel_size > 0 and kernel_size % 2 == 1
    ), f"kernel_size ({kernel_size}) must positive and odd."

    kernel_width: int = kernel_size
    kernel_height: int = kernel_size

    # If the kernel extends past the top or bottom row, decrease kernel_height
    if kernel_height // 2 > pix_row:
        kernel_height = 2 * pix_row + 1
    elif pix_row + kernel_height // 2 >= depth_image.shape[0]:
        kernel_height = 2 * (depth_image.shape[0] - pix_row - 1) + 1

    # If the kernel extends past the first or last column, decrease kernel_width
    if kernel_width // 2 > pix_col:
        kernel_width = 2 * pix_col + 1
    elif pix_col + kernel_width // 2 >= depth_image.shape[1]:
        kernel_width = 2 * (depth_image.shape[1] - pix_col - 1) + 1

    # Crop out a kernel around the requested pixel
    cropped_center = crop(
        depth_image,
        (pix_row - kernel_height // 2, pix_col - kernel_width // 2),
        (pix_row + kernel_height // 2 + 1, pix_col + kernel_width // 2 + 1),
    )

    # Apply a Gaussian blur to the cropped depth image to average the surrounding
    # pixel depths
    blurred_center = cv.GaussianBlur(cropped_center, (kernel_width, kernel_height), 0)

    # Return the depth at the center of the kernel
    return blurred_center[kernel_height // 2, kernel_width // 2]


def get_closest_pixel(
    depth_image: NDArray[(Any, Any), np.float32],
    kernel_size: int = 5
) -> tuple[int, int]:
    """
    Finds the closest pixel in a depth image.

    Args:
        depth_image: The depth image to process.
        kernel_size: The size of the area to average around each pixel.

    Returns:
        The (row, column) of the pixel which is closest to the car.

    Warning:
        kernel_size be positive and odd.
        It is highly recommended that you crop off the bottom of the image, or else
        this function will likely return the ground directly in front of the car.

    Note:
        The larger the kernel_size, the more that the depth of each pixel is averaged
        with the distances of the surrounding pixels.  This helps reduce noise at the
        cost of reduced accuracy.

    Example::

        depth_image = rc.camera.get_depth_image()

        # Crop off the ground directly in front of the car
        cropped_image = rc_utils.crop(
            image, (0, 0), (int(rc.camera.get_height() * 0.66), rc.camera.get_width())
        )

        # Find the closest pixel
        closest_pixel = rc_utils.get_closest_pixel(depth_image)
    """
    assert (
        kernel_size > 0 and kernel_size % 2 == 1
    ), f"kernel_size ({kernel_size}) must positive and odd."

    # Shift 0.0 values to 10,000 so they are not considered for the closest pixel
    depth_image = (depth_image - 0.01) % 10000

    # Apply a Gaussian blur to reduce noise
    if kernel_size > 1:
        blurred_image = cv.GaussianBlur(depth_image, (kernel_size, kernel_size), 0)

    # Find the pixel location of the minimum depth
    (_, _, minLoc, _) = cv.minMaxLoc(blurred_image)

    # minLoc is formatted as (column, row), so we flip the order
    return minLoc[1], minLoc[0]


def colormap_depth_image(
    depth_image: NDArray[(Any, Any), np.float32],
    max_depth: int = 1000,
) -> NDArray[(Any, Any, 3), np.uint8]:
    """
    Converts a depth image to a colored image representing depth.

    Args:
        depth_image: The depth image to convert.
        max_depth: The farthest depth to show in the image in cm.  Anything past
            this depth is shown as the farthest color.

    Returns:
        A color image representation of the provided depth image.

    Note:
        Each color value ranges from 0 to 255.
        The color of each pixel is determined by its distance.

    Example::

        # retrieve a depth image
        depth_image = rc.camera.get_depth_image()

        # get the colormapped depth image
        depth_image_colormap = rc_utils.colormap_depth_image(depth_image)
    """
    # Clip anything above max_depth
    np.clip(depth_image, None, max_depth, depth_image)

    # Shift down slightly so that 0 (no data) becomes the "farthest" color
    depth_image = (depth_image - 0.01) % max_depth

    return cv.applyColorMap(
        -cv.convertScaleAbs(depth_image, alpha=255 / max_depth), cv.COLORMAP_INFERNO
    )


########################################################################################
# LIDAR
########################################################################################


def get_lidar_closest_point(
    scan: NDArray[Any, np.float32],
    window: tuple[float, float] = (0, 360)
) -> tuple[float, float]:
    """
    Finds the closest point from a LIDAR scan.

    Args:
        scan: The samples from a LIDAR scan.
        window: The degree range to consider, expressed as (min_degree, max_degree)

    Returns:
        The (angle, distance) of the point closest to the car within the specified
        degree window. All angles are in degrees, starting at 0 directly in front of the
        car and increasing clockwise. Distance is in cm.

    Warning:
        In areas with glass, mirrors, or large open spaces, there is a high
        likelihood of distance error.

    Note:
        Ignores any samples with a value of 0.0 (no data).

        In order to define a window which passes through the 360-0 degree boundary, it
        is acceptable for window min_degree to be larger than window max_degree.  For
        example, (350, 10) is a 20 degree window in front of the car.

    Example::

        scan = rc.lidar.get_samples()

        # Find the angle and distance of the closest point
        angle, distance = rc_utils.get_lidar_closest_point(scan)

        # Find the closest distance in the 90 degree window behind the car
        _, back_distance = rc_utils.get_lidar_closest_point(scan, (135, 225))

        # Find the closest distance in the 90 degree window in front of the car
        _, front_distance = rc_utils.get_lidar_closest_point(scan, (315, 45))
    """
    # Adjust window angles into the 0 to 360 degree range
    min_angle = window[0] % 360
    max_angle = window[1] % 360

    # If min_angle and max_angle are the same, use the entire scan
    if min_angle == max_angle:
        samples = (scan - 0.01) % 1000000
        min_index = np.argmin(samples)
        return min_index * 360 / scan.shape[0], samples[min_index]

    # Find the indices of the first and last sample in window
    first_sample: int = round(min_angle * len(scan) / 360)
    last_sample: int = round(max_angle * len(scan) / 360) + 1

    # If we pass the 0-360 boundary, we must consider the scan in two pieces
    if first_sample > last_sample:
        left_samples = scan[first_sample:]
        right_samples = scan[: last_sample + 1]

        # Turn 0.0 (no data) into a very large number so it is ignored
        left_samples = (left_samples - 0.01) % 1000000
        right_samples = (right_samples - 0.01) % 1000000

        # Find index and value of min value in each piece
        left_min_index = np.argmin(left_samples)
        left_min = left_samples[left_min_index]
        right_min_index = np.argmin(right_samples)
        right_min = right_samples[right_min_index]

        # Return the degree and angle of the smaller value
        if left_min < right_min:
            return (first_sample + left_min_index) * 360 / scan.shape[0], left_min
        else:
            return right_min_index * 360 / scan.shape[0], right_min

    # Otherwise, use the same approach but for one continuous piece
    samples = (scan[first_sample : last_sample + 1] - 0.01) % 1000000
    min_index = np.argmin(samples)
    return (first_sample + min_index) * 360 / scan.shape[0], samples[min_index]


def get_lidar_average_distance(
    scan: NDArray[Any, np.float32],
    angle: float,
    window_angle: float = 4
) -> float:
    """
    Finds the average distance of the object at a particular angle relative to the car.

    Args:
        scan: The samples from a LIDAR scan
        angle: The angle (in degrees) at which to measure distance, starting at 0
            directly in front of the car and increasing clockwise.
        window_angle: The number of degrees to consider around angle.

    Returns:
        The average distance of the points at angle in cm.

    Note:
        Ignores any samples with a value of 0.0 (no data).
        Increasing window_angle reduces noise at the cost of reduced accuracy.

    Example::

        scan = rc.lidar.get_samples()

        # Find the distance directly behind the car (6:00 position)
        back_distance = rc_utils.get_lidar_average_distance(scan, 180)

        # Find the distance to the forward and right of the car (1:30 position)
        forward_right_distance = rc_utils.get_lidar_average_distance(scan, 45)
    """
    assert (
        0 <= window_angle < 360
    ), f"window_angle ({window_angle}) must be in the range 0 to 360, and reasonably should not exceed 20."

    # Adjust angle into the 0 to 360 degree range
    angle %= 360

    # Calculate the indices at the edges of the requested window
    center_index: int = int(angle * scan.shape[0] / 360)
    num_side_samples: int = int(window_angle / 2 * scan.shape[0] / 360)
    left_index: int = (center_index - num_side_samples) % len(scan)
    right_index: int = (center_index + num_side_samples) % len(scan)

    # Select samples in the window, handling if we cross the edge of the array
    samples: list[float]
    if right_index < left_index:
        samples = scan[left_index:].tolist() + scan[0 : right_index + 1].tolist()
    else:
        samples = scan[left_index : right_index + 1].tolist()

    # Remove samples with no data (0.0)
    samples = [elem for elem in samples if elem > 0]

    # If no valid samples remain, return 0.0
    if len(samples) == 0:
        return 0.0

    return sum(samples) / len(samples)


########################################################################################
# AR Markers
########################################################################################


class Orientation(Enum):
    """
    The orientations which an AR marker can face, with the value indicating the index of
    the corner which is currently oriented in the top-left in the image.
    """

    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3


class ARMarker:
    """
    Encapsulates information about an AR marker detected in a color image.
    """

    def __init__(
        self,
        marker_id: int,
        marker_corners: NDArray[(4, 2), np.int32]
    ) -> None:
        """
        Creates an object representing an AR marker.

        Args:
            marker_id: The integer identification number of the marker pattern.
            marker_corners: The (row, col) coordinates of the four corners of the
                marker, ordered clockwise with the top-left corner of the pattern
                appearing first.

        Example::

            id = 12
            corners = ((0, 0), (0, 10), (10, 10), (10, 0))
            marker = ARMarker(id, corners)
        """
        assert (
            marker_corners.shape[0] == 4
        ), f"corners must contain 4 points, but had [{marker_corners.shape[0]}] points."

        self.__id: int = marker_id
        self.__corners: NDArray[(4, 2), np.int32] = marker_corners
        self.__color: str = "not detected"
        self.__color_area: int = 0

        # Calculate orientation based on corners
        if self.__corners[0][1] > self.__corners[2][1]:
            if self.__corners[0][0] > self.__corners[2][0]:
                self.__orientation = Orientation.DOWN
            else:
                self.__orientation = Orientation.RIGHT
        else:
            if self.__corners[0][0] > self.__corners[2][0]:
                self.__orientation = Orientation.LEFT
            else:
                self.__orientation = Orientation.UP

    def detect_colors(
        self,
        color_image: NDArray[(Any, Any), np.uint8],
        potential_colors: list[tuple[tuple[int, int, int], tuple[int, int, int], str]],
    ) -> None:
        """
        Attempts to detect the provided colors in the border around the AR marker.

        Args:
            color_image: The image in which the marker was detected.
            potential_colors: A list of colors which the marker border may be. Each
                candidate color is formated as (hsv_lower, hsv_upper, color_name).

        Example::

            # Define color candidates in the (hsv_lower, hsv_upper, color_name) format
            BLUE = ((90, 100, 100), (120, 255, 255), "blue")
            RED = ((170, 100, 100), (10, 255, 255), "red")

            # Detect the AR markers in the current color image
            image = rc.camera.get_color_image()
            markers = rc_utils.get_ar_markers(image)

            # Search for the colors RED and BLUE in all of the detected markers
            for marker in markers:
                marker.detect_colors(image, [BLUE, RED])
        """
        assert potential_colors is not None, f"potential_colors cannot be null"

        # Calculate the position and dimensions of the marker in the image
        marker_top, marker_left = self.__corners[self.__orientation.value]
        marker_bottom, marker_right = self.__corners[(self.__orientation.value + 2) % 4]
        half_marker_height: int = (marker_bottom - marker_top) // 2
        half_marker_width: int = (marker_right - marker_left) // 2

        # Crop to an area twice as large as the marker, centered about the marker
        crop_top_left = (
            max(0, marker_top - half_marker_height),
            max(0, marker_left - half_marker_width),
        )
        crop_bottom_right = (
            min(color_image.shape[0], marker_bottom + half_marker_height) + 1,
            min(color_image.shape[1], marker_right + half_marker_width) + 1,
        )
        cropped_image = crop(color_image, crop_top_left, crop_bottom_right)

        # Attempt to find each color in the cropped area, and choose the color of which
        # we see the most
        for (hsv_lower, hsv_upper, color_name) in potential_colors:
            contours = find_contours(cropped_image, hsv_lower, hsv_upper)
            largest_contour = get_largest_contour(contours)
            if largest_contour is not None:
                contour_area = get_contour_area(largest_contour)
                if contour_area > self.__color_area:
                    self.__color_area = contour_area
                    self.__color = color_name

    def get_id(self) -> int:
        """
        Returns the integer identification number of the marker pattern.
        """
        return self.__id

    def get_corners(self) -> NDArray[(4, 2), np.int32]:
        """
        Returns the (row, col) coordinates of the four corners of the marker.

        Note:
            The corners are ordered clockwise with the top-left corner of the pattern
            appearing first.
        """
        return self.__corners

    def get_corners_aruco_format(self) -> NDArray[(1, 4, 2), np.float32]:
        """
        Returns the corners of the AR marker formatted as needed by the ArUco library.
        """
        output = self.__corners.astype(np.float32).reshape(1, 4, 2)
        for i in range(4):
            row = output[0][i][0]
            output[0][i][0] = output[0][i][1]
            output[0][i][1] = row
        return output

    def get_orientation(self) -> Orientation:
        """
        Returns the orientation of the marker.
        """
        return self.__orientation

    def get_color(self) -> str:
        """
        Returns the color of the marker if it was successfully detected.
        """
        return self.__color

    def __str__(self) -> str:
        """
        Returns a printable message summarizing the key information of the marker.
        """
        output = f"ID: {self.__id}\nCorners: {self.__corners}\nOrientation: {self.__orientation}\nColor: "
        color_lower = str.lower(self.__color)
        if color_lower in TerminalColor.__members__:
            return output + format_colored(self.__color, TerminalColor[color_lower])
        return output + self.__color


def get_ar_markers(
    color_image: NDArray[(Any, Any, 3), np.uint8],
    potential_colors: list[
        tuple[tuple[int, int, int], tuple[int, int, int], str]
    ] = None,
    marker_type: int = cv.aruco.DICT_6X6_250
) -> list[ARMarker]:
    """
    Finds AR markers in an image.

    Args:
        color_image: The color image in which to search for AR markers.
        potential_colors: The potential colors of the AR marker, each represented as
            (hsv_min, hsv_max, color_name)
        marker_type: The type of ArUco marker to look for. By default, this function looks
            for 6x6 markers.

    Warning:
        By default, this function looks for 6x6 AR markers which are used in the racecar sim.
        To track the 5x5 markers used in-person, pass `cv.aruco.DICT_5X5_250` to `type`.

    Returns:
        A list of each AR marker's four corners clockwise and an array of the AR marker ids.

    Example::

        # Detect 6x6 ArUco markers in the current color image.
        image = rc.camera.get_color_image()
        markers = racecar_utils.get_ar_markers(image)

        # Or, detect 5x5 markers instead:
        markers = racecar_utils.get_ar_markers(image, marker_type=cv.aruco.DICT_5X5_250)

        # Print information detected for the zeroth marker
        if len(markers) >= 1:
            print(markers[0])
    """
    # Use ArUco to find the raw corner and id information
    dictionary = cv.aruco.getPredefinedDictionary(marker_type)
    params = cv.aruco.DetectorParameters()

    detector = cv.aruco.ArucoDetector(dictionary, params)
    corners, ids, _ = detector.detectMarkers(color_image)

    # Create an ARMarker object for each detected marker
    markers: list[ARMarker] = []
    for i in range(len(corners)):
        # Rearrange each corner point into the (row, col) format
        corners_formatted = corners[i][0].astype(np.int32)
        for j in range(corners_formatted.shape[0]):
            col = corners_formatted[j][0]
            corners_formatted[j][0] = corners_formatted[j][1]
            corners_formatted[j][1] = col

        marker = ARMarker(ids[i][0], corners_formatted)

        # Detect potential colors, if provided
        if potential_colors is not None and len(potential_colors) > 0:
            marker.detect_colors(color_image, potential_colors)

        markers.append(marker)
    return markers


def draw_ar_markers(
    color_image: NDArray[(Any, Any, 3), np.uint8],
    markers: list[ARMarker],
    color: tuple[int, int, int] = ColorBGR.green.value,
) -> NDArray[(Any, Any, 3), np.uint8]:
    """
    Draws annotations on the AR markers in an image.

    Args:
        color_image: The color image in which the AR markers were detected.
        markers: The AR markers detected in the image.
        color: The color used to outline each AR marker, represented in the BGR format.

    Warning:
        This modifies the provided image. If you accessed the image with
        rc.camera.get_color_image_no_copy(), you must manually create a copy of the
        image first with copy.deepcopy().

    Example::

        # Detect the AR markers in the current color image
        image = rc.camera.get_color_image()
        markers = rc_utils.get_ar_markers(image)

        # Draw the detected markers on the image and display it
        rc_utils.draw_ar_markers(image, markers)
        rc.display.show_color_image(color_image)
    """
    ids = np.zeros((len(markers), 1), np.int32)
    corners = []
    for i in range(len(markers)):
        ids[i][0] = markers[i].get_id()
        corners.append(markers[i].get_corners_aruco_format())
    return cv.aruco.drawDetectedMarkers(color_image, corners, ids, color)
