"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: physics.py
File Description: Defines the interface of the Physics module of the racecar_core library
"""

import abc
import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls


class Physics(abc.ABC):
    """
    Returns the car's motion and power measurements: IMU (acceleration, angular
    velocity, magnetic field), drive encoder speed, battery voltage and current,
    and the RC transmitter channels.
    """

    @abc.abstractmethod
    def get_linear_acceleration(self) -> NDArray[3, np.float32]:
        """
        Returns a 3D vector containing the car's linear acceleration.

        Returns:
            The average linear acceleration of the car along the (x, y, z) axes during
            the last frame in m/s^2.

        Note:
            The simulator and the physical RACECAR use the same axes (REP-103):
            The x-axis points out of the front of the car.
            The y-axis points out of the left of the car.
            The z-axis points directly up (perpendicular to the ground).

            The accelerometer measures specific force, so a car at rest reads about
            (0, 0, 9.81): gravity appears as an upward acceleration.

        Example::

            # accel stores the average acceleration over the previous frame
            accel = rc.physics.get_linear_acceleration()

            # forward accel stores acceleration in the forward direction.  This will be
            # positive when the car accelerates, and negative when it decelerates.
            forward_accel = accel[0]
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
            The simulator and the physical RACECAR use the same axes (REP-103):
            The x-axis (roll) points out of the front of the car.
            The y-axis (pitch) points out of the left of the car.
            The z-axis (yaw) points directly up (perpendicular to the ground).
            Rotation sign uses the right hand rule. For example, when the car turns to
            the left, it has a positive angular velocity along the z axis.

        Example::

            # ang_vel stores the average angular velocity over the previous frame
            ang_vel = rc.physics.get_angular_velocity()

            # yaw stores the yaw of the car, which is positive when it turns to the left
            # and negative when it turns to the right.
            yaw = ang_vel[2]
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
            The simulator and the physical RACECAR use the same axes (REP-103):
            The x-axis points out of the front of the car.
            The y-axis points out of the left of the car.
            The z-axis points directly up (perpendicular to the ground).

            Earth's field points north and steeply down, so z is negative (about
            -47 uT near Boston). In the simulator magnetic north is the world +Z
            direction of every level.

        Example::

            # heading stores the car's direction in degrees, 0 facing magnetic north and
            # increasing counterclockwise (toward the west) on level ground
            mag = rc.physics.get_magnetic_field()
            heading = math.degrees(math.atan2(-mag[1], mag[0]))
        """
        pass

    @abc.abstractmethod
    def get_encoder_speed(self) -> float:
        """
        Returns the car's forward speed measured by the drive encoder.

        Returns:
            The average forward speed of the car over the last frame in m/s,
            derived from the NEO-PIT hall encoder (the Teensy applies the gear
            ratios and wheel circumference). Positive is forward.

        Note:
            --- In the Simulator ---
            With Realism off, the car's true forward speed. With Realism on, the
            speed of the wheels as the hall encoder measures it, so wheel slip and
            spin show, and readings below about 0.075 m/s drop to 0 between edges.

            --- In the Physical RACECAR ---
            The value comes from the /encoder/speed topic.

        Example::

            # speed stores the car's forward speed in m/s
            speed = rc.physics.get_encoder_speed()
        """
        pass

    @abc.abstractmethod
    def get_battery_voltage(self) -> float:
        """
        Returns the battery bus voltage measured by the NEO-PIT power sensor.

        Returns:
            The bus voltage in volts (INA226 sensor).

        Note:
            --- In the Simulator ---
            A 2S 5000 mAh pack, full (8.4 V) when the level loads, empty at 7.0 V;
            the voltage sags slightly while the car drives.

            --- In the Physical RACECAR ---
            The value comes from the /battery/voltage topic.

        Example::

            # voltage stores the battery voltage in volts
            voltage = rc.physics.get_battery_voltage()
        """
        pass

    @abc.abstractmethod
    def get_battery_current(self) -> float:
        """
        Returns the battery current measured by the NEO-PIT power sensor.

        Returns:
            The current draw in amps (INA226 sensor).

        Note:
            --- In the Simulator ---
            2.5 A while the drive is idle, 5 A to 10 A while it is commanded,
            rising with speed.

            --- In the Physical RACECAR ---
            The value comes from the /battery/current topic.

        Example::

            # current stores the battery draw in amps
            current = rc.physics.get_battery_current()
        """
        pass

    @abc.abstractmethod
    def get_rc_channels(self) -> NDArray[8, np.float32]:
        """
        Returns the eight FlySky RC transmitter channels.

        Returns:
            An array of eight values, each in the range [-1, 1] (0 at the
            channel's center or with no transmitter signal). Channel map on the
            FlySky iA6B (verified on hardware)::

                [0] right stick X (steering)   [4] switch A
                [1] right stick Y              [5] switch B
                [2] left stick Y (throttle)    [6] switch C
                [3] left stick X               [7] switch D

            The firmware drives steering from channel 0 and throttle from
            channel 2.

        Note:
            --- In the Simulator ---
            This function returns eight zeros (there is no RC receiver in
            simulation).

            --- In the Physical RACECAR ---
            The values come from the /rc/channels topic, normalized by the
            firmware pulse widths.

        Example::

            # channels stores the eight RC channels in [-1, 1]
            channels = rc.physics.get_rc_channels()
            steering = channels[0]
        """
        pass
