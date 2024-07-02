"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: lidar.py
File Description: Defines the interface for the Lidar module of the racecar_core library.
"""

import abc
import numpy as np
from nptyping import NDArray


class Lidar(abc.ABC):
    """
    Returns the scan data captured by the Lidar.
    """

    # The number of samples in a full Lidar scan.
    _NUM_SAMPLES: int = 720

    @abc.abstractmethod
    def get_samples(self) -> NDArray[720, np.float32]:
        """
        Returns the current LIDAR scan as an array of distance measurements.

        Returns:
            An array of distance measurements in cm.

        Note:
            Samples are in clockwise order, with the 0th sample directly in front of the
            car.  Each sample is an equal angle apart.

        Example::

            # Access the most recent lidar scan.
            scan = rc.lidar.get_samples()

            # Get the distance of the measurement directly in front of the car
            forward_distance = scan[0]
        """
        pass

    @abc.abstractmethod
    def get_samples_async(self) -> NDArray[720, np.float32]:
        """
        Returns the current LIDAR scan without the car in "go" mode.

        Returns:
            An array of distance measurements in cm.

        Note:
            Samples are in clockwise order, with the 0th sample directly in front of the
            car.  Each sample is an equal angle apart.

        Warning:
            This function breaks the start-update paradigm and should only be used in
            Jupyter Notebook.

        Example::

            # Access the most recent lidar scan.
            scan = rc.lidar.get_samples_async()

            # Get the distance of the measurement directly in front of the car
            forward_distance = lidar_ranges[0]
        """
        pass

    def get_num_samples(self) -> int:
        """
        Returns the number of samples in a full LIDAR scan.

        Returns:
            The number of points collected in a complete scan.

        Example::

            scan = rc.lidar.get_samples()

            # Access the sample directly behind the car
            rear_distance = scan[rc.lidar.get_num_samples() // 2]
        """
        return self._NUM_SAMPLES
