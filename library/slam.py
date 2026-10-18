"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: slam.py
File Description: Defines the interface of the Slam module of the racecar_core
library. Reads the car's position on a lidar map from the driver's autonomy
service, which builds and loads maps (racecar map, or the map viewer on port
8084).
"""

import abc
import math
from typing import Optional, Tuple

import numpy as np


class OccupancyMap:
    """
    A 2D occupancy grid of the space around the car.

    Attributes:
        width: Number of columns.
        height: Number of rows.
        resolution: Size of one cell in meters (0.05 by default).
        origin: (x, y) in meters of the lower-left corner of cell (0, 0) in the
            map frame.
        data: int8 array of shape (height, width): -1 unknown, 0 free, and 100
            wall. Row 0 is at the bottom, so the row index grows with y and the
            column index with x.

    Note:
        To plot the map the right way up with matplotlib, pass origin="lower":
        plt.imshow(m.data, origin="lower").
    """

    UNKNOWN = -1
    FREE = 0
    WALL = 100

    def __init__(
        self,
        width: int,
        height: int,
        resolution: float,
        origin: Tuple[float, float],
        data: np.ndarray,
    ) -> None:
        self.width = width
        self.height = height
        self.resolution = resolution
        self.origin = origin
        self.data = data

    def to_cell(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """
        Returns the cell that holds a point of the map.

        Args:
            x: Map x in meters.
            y: Map y in meters.

        Returns:
            (row, col) of the cell, or None when the point is off the map.

        Example::

            m = rc.slam.get_map()
            x, y, heading = rc.slam.get_pose()
            cell = m.to_cell(x, y)
        """
        col = math.floor((x - self.origin[0]) / self.resolution)
        row = math.floor((y - self.origin[1]) / self.resolution)
        if 0 <= row < self.height and 0 <= col < self.width:
            return row, col
        return None

    def to_point(self, row: int, col: int) -> Tuple[float, float]:
        """
        Returns the map position of a cell's center.

        Args:
            row: Row index; 0 is the bottom row.
            col: Column index; 0 is the left column.

        Returns:
            (x, y) in meters in the map frame.
        """
        return (
            self.origin[0] + (col + 0.5) * self.resolution,
            self.origin[1] + (row + 0.5) * self.resolution,
        )

    def value_at(self, x: float, y: float) -> int:
        """
        Returns the occupancy at a point of the map.

        Args:
            x: Map x in meters.
            y: Map y in meters.

        Returns:
            100 for a wall, 0 for free space, and -1 for unknown space or a
            point off the map.

        Example::

            # True if there is a wall 1 m along the map's x axis from the car
            x, y, heading = rc.slam.get_pose()
            wall_ahead = rc.slam.get_map().value_at(x + 1.0, y) == 100
        """
        cell = self.to_cell(x, y)
        if cell is None:
            return self.UNKNOWN
        return int(self.data[cell[0], cell[1]])

    def __repr__(self) -> str:
        return (
            f"OccupancyMap({self.width} x {self.height} cells, "
            f"{self.resolution:.2f} m, origin ({self.origin[0]:.2f}, {self.origin[1]:.2f}))"
        )


def heading_degrees(qz: float, qw: float) -> float:
    """Return the heading of a planar quaternion in degrees, in [-180, 180)."""
    deg = math.degrees(2.0 * math.atan2(qz, qw))
    return (deg + 180.0) % 360.0 - 180.0


class Slam(abc.ABC):
    """
    Reads the car's position on a lidar map, the map itself, and whether the
    position can be trusted.

    Maps are built and loaded outside the program, with `racecar map` on the
    car or in the map viewer (http://<car>:8084). While mapping, the car's
    position is on the map being built; while localizing, it is on the loaded
    map. With the autonomy service stopped the mode is "off" and there is no
    pose or map.
    """

    @abc.abstractmethod
    def get_mode(self) -> str:
        """
        Returns what the autonomy service is doing.

        Returns:
            "mapping", "localization", or "off".

        Example::

            if rc.slam.get_mode() == "off":
                print("Load a map in the map viewer first")
        """
        pass

    @abc.abstractmethod
    def get_map_name(self) -> str:
        """
        Returns the name of the map being built or used.

        Returns:
            The map name, or "" when the mode is "off".
        """
        pass

    @abc.abstractmethod
    def is_localized(self) -> bool:
        """
        Returns whether the car's pose can be trusted.

        Returns:
            True while mapping with the lidar running, or while localizing with
            a tight pose estimate whose lidar scan fits the map. False when the
            mode is "off".

        Note:
            A car that is picked up and set down elsewhere reads False within a
            few seconds, and stays False until its position is found again (Set
            pose or Find me in the map viewer, then drive slowly).

        Example::

            if rc.slam.is_localized():
                x, y, heading = rc.slam.get_pose()
        """
        pass

    @abc.abstractmethod
    def get_pose(self) -> Optional[Tuple[float, float, float]]:
        """
        Returns the car's position and heading on the map.

        Returns:
            (x, y, heading): x and y in meters in the map frame, heading in
            degrees counterclockwise from the map's x axis, in [-180, 180).
            None when the mode is "off" or no pose has arrived yet.

        Note:
            The position is the point on the floor under the middle of the rear
            axle. Check is_localized() before relying on it.

        Example::

            pose = rc.slam.get_pose()
            if pose is not None:
                x, y, heading = pose
        """
        pass

    @abc.abstractmethod
    def get_pose_async(self) -> Optional[Tuple[float, float, float]]:
        """
        Returns the car's position and heading without the car in "go" mode.

        Returns:
            The same as get_pose(), read from the newest message rather than
            once per frame.

        Warning:
            This function breaks the start-update paradigm and should only be
            used in Jupyter Notebook.
        """
        pass

    @abc.abstractmethod
    def get_map(self) -> Optional[OccupancyMap]:
        """
        Returns the newest map.

        Returns:
            An OccupancyMap, or None when the mode is "off" or no map has arrived
            yet. While mapping it grows about every 5 seconds; while localizing
            it does not change.

        Example::

            m = rc.slam.get_map()
            if m is not None:
                walls = (m.data == 100).sum()
        """
        pass

    @abc.abstractmethod
    def save_map(self) -> None:
        """
        Saves the map being built; returns at once.

        Note:
            Only while mapping. Follow the result with get_save_status(). The
            map is also saved every 60 seconds and when mapping stops.

        Example::

            if rc.controller.was_pressed(rc.controller.Button.A):
                rc.slam.save_map()
        """
        pass

    @abc.abstractmethod
    def get_save_status(self) -> str:
        """
        Returns the result of the last save_map() call.

        Returns:
            "" before any save, "saving" while it runs, "saved" when the files
            are written, or "failed: <reason>".

        Example::

            status = rc.slam.get_save_status()
            if status.startswith("failed"):
                print(status)
        """
        pass
