"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: physics.py
File Description: Defines the interface of the Physics module of the racecar_core library
"""

import abc
import numpy as np
from nptyping import NDArray


class Physics(abc.ABC):
    """
    Returns the linear acceleration and angular velocity measured by the IMU.
    """

    @abc.abstractmethod
    def get_linear_acceleration(self) -> NDArray[3, np.float32]:
        """
        Returns a 3D vector containing the car's linear acceleration.

        Returns:
            The average linear acceleration of the car along the (x, y, z) axes during
            the last frame in m/s^2.

        Note:
            --- In the Simulator ---
            The x-axis points out of the right of the car.
            The y-axis points directly up (perpendicular to the ground).
            The z-axis points out of the front of the car.

            --- In the Physical RACECAR ---
            The x-axis points out of the front of the car.
            The y-axis points out of the right of the car.
            The z-axis points directly up (perpendicular to the ground).

        Example::

            # accel stores the average acceleration over the previous frame
            accel = rc.physics.get_linear_acceleration()

            # forward accel stores acceleration in the forward direction.  This will be
            # positive when the car accelerates, and negative when it decelerates.
            forward_accel = accel[2]
        """
        pass

    @abc.abstractmethod
    def get_angular_velocity(self) -> NDArray[3, np.float32]:
        """
        Returns a 3D vector containing the car's angular velocity.

        Returns:
            The average angular velocity of the car along the (x, y, z) axes during the
            last frame in rad/s.

        Note:
            --- In the Simulator ---
            The x-axis (pitch) points out of the right of the car.
            The y-axis (yaw) points directly up (perpendicular to the ground).
            The z-axis (roll) points out of the front of the car.
            Rotation sign uses the right hand rule. For example, when the car turns to
            the left, it has a positive angular velocity along the y axis.

            --- In the Physical RACECAR ---
            The x-axis (roll) points out of the front of the car.
            The y-axis (pitch) points out of the right of the car.
            The z-axis (yaw) points directly up (perpendicular to the ground).

        Example::

            # ang_vel stores the average angular velocity over the previous frame
            ang_vel = rc.physics.get_angular_velocity()

            # yaw stores the yaw of the car, which is positive when it turns to the left
            # and negative when it turns to the right.
            yaw = ang_vel[1]
        """
        pass

    @abc.abstractmethod
    def get_magnetic_field(self) -> NDArray[3, np.float32]:
        """
        Returns a 3D vector containing the car's magnetic field measurements.

        Returns:
            The average magnetic field measurements from the magnetometer along the (x, y, z) axis
            during the last frame in Teslas.

        Note:
            --- In the Simulator ---
            This function does not exist.

            --- In the Physcial RACECAR ---
            The x-axis points towards the back of the car.
            The y-axis points towards the right of the car.
            The z-axis points directly up (perpendicular to the ground).
        """
        pass
