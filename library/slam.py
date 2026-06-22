"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: slam.py
File Description: Defines the interface for the Slam module of the racecar_core library.
"""

import abc
from typing import List, Tuple

import numpy as np


class Slam(abc.ABC):
    """
    Builds and localizes against an occupancy-grid map of the car's surroundings.

    The same interface is available in simulation and on the physical car, so a
    single mapping or navigation program runs unchanged in both. On the real car
    it is backed by slam_toolbox; in the simulator by the in-browser SLAM core.
    """

    @abc.abstractmethod
    def update(self, scan: np.ndarray) -> Tuple[float, float, float]:
        """
        Folds the latest LIDAR scan into the map and returns the corrected pose.

        Args:
            scan: The current LIDAR scan in cm, as returned by
                rc.lidar.get_samples().

        Returns:
            The corrected (x, y, heading) pose in meters and radians, with heading
            normalized to the range [-pi, pi].

        Note:
            On the physical car the SLAM backend ingests the LIDAR stream
            directly, so scan is accepted for simulator parity but the map
            advances on its own; the call still returns the latest pose.

        Example::

            scan = rc.lidar.get_samples()
            x, y, heading = rc.slam.update(scan)
        """
        pass

    @abc.abstractmethod
    def get_pose(self) -> Tuple[float, float, float]:
        """
        Returns the car's current pose within the map.

        Returns:
            The (x, y, heading) pose in meters and radians.

        Example::

            x, y, heading = rc.slam.get_pose()
        """
        pass

    @abc.abstractmethod
    def get_map(self) -> Tuple[int, int, float, List[int]]:
        """
        Returns the current occupancy grid.

        Returns:
            A tuple (width, height, cell_size_m, grid), where grid is a row-major
            list of occupancy values: -1 unknown, 0 free, and 100 occupied.

        Example::

            width, height, cell_m, grid = rc.slam.get_map()

            # Occupancy of the cell at grid column col, row row
            value = grid[row * width + col]
        """
        pass

    @abc.abstractmethod
    def reset(self) -> None:
        """
        Clears the map and pose so the next scan starts a fresh map.

        Example::

            rc.slam.reset()
        """
        pass

    @abc.abstractmethod
    def save_map(self, name: str) -> None:
        """
        Saves the current map under name so it can be reloaded later.

        Real hardware writes the map into ~/.neoracer/maps.

        Example::

            # After driving manually around the track
            rc.slam.save_map("my_track")
        """
        pass

    @abc.abstractmethod
    def load_map(self, name: str) -> bool:
        """
        Loads a previously saved map.

        Returns:
            True if a map named name was found and loaded, False otherwise.

        Example::

            if not rc.slam.load_map("my_track"):
                print("No saved map found; run the mapping program first.")
        """
        pass
