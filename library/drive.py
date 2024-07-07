"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: drive.py
File Description: Defines the interface of the Drive module of the racecar_core library.
"""

import abc


class Drive(abc.ABC):
    @abc.abstractmethod
    def set_speed_angle(self, speed: float, angle: float) -> None:
        """
        Sets the throttle applied to the back wheels and the angle of the front wheels.

        Args:
            speed: The amount of throttle (torque) applied to the back wheels from -1.0
                (full backward) to 1.0 (full forward).
            angle: The amount to turn the front wheels from -1.0 (full left) to 1.0
                (full right).

        Note:
            The speed and angle arguments are unitless ratios.

        Example::

            if counter < 1:
                # Drive straight forward at full speed
                rc.drive.set_speed_angle(1, 0)
            elif counter < 2:
                # Drive reverse at full speed with the wheels pointing fully to the left
                rc.drive.set_speed_angle(-1, -1)
            else:
                # Drive 70% to the right at half speed forward
                rc.drive.set_speed_angle(0.5, 0.7)
        """
        pass

    def stop(self) -> None:
        """
        Brings the car to a stop and points the front wheels forward.

        Note:
            stop is equivalent to rc.drive.set_speed_angle(0, 0)

        Example::

            # Stops the car if the counter is greater than 5
            if counter > 5:
                rc.drive.stop()
        """
        self.set_speed_angle(0, 0)

    @abc.abstractmethod
    def set_max_speed(self, max_speed: float = 0.25) -> None:
        """
        Sets the maximum throttle in the forward and backward direction.

        Args:
            max_speed: The scale factor applied to speed inputs, ranging from
                0.0 to 1.0.

        Warning:
            The RACECAR contains expensive and fragile equipment.  Please only increase
            the max speed if you are in a safe environment without the potential for
            hard collisions.

        Example::

            # Update the max speed to 0.5
            rc.set_max_speed(0.5)
        """
        pass
