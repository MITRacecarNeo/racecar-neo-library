"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: telemetry.py
File Description: Defines the interface of the Telemetry module of the racecar_core library
"""

import abc
import numpy as np
from nptyping import NDArray


class Telemetry(abc.ABC):
    """
    Records and visualizes real time sensor data and internal states
    """
    @abc.abstractmethod
    def declare_variables(self, *names: str) -> None:
        """
        Declare a list of variables that will be recorded by telemetry

        Args:
            names: name of each variable to be declared

        Note:
            This function should only be called once, and all subsequent calls will have no effect.
            In addition to the variables declared here, when a data point is pushed into
            Telemetry, its timestamp will also be recorded

        Example::

            # Declare variables speed and angle to be recorded
            rc.telemetry.declare_variables("speed", "angle")

            # Push a data point containing a speed value and an angle value into Telemetry
            rc.telemetry.record(1, 0.5)
        """

    @abc.abstractmethod
    def record(self, *values: any) -> None:
        """
        Record a data point, which should contain a value for each declared variable 

        Args:
            values: value of each declared variable, should be in the same order as the declaration

        Note:
            declare_variables must be called before this function.
            If too few / too many values are provided, an exception will be thrown

        Example::

            # Declare variables speed and angle to be recorded
            rc.telemetry.declare_variables("speed", "angle")

            # Push a data point containing a speed value and an angle value into Telemetry
            rc.telemetry.push(1, 0.5)
        """

    def visualize() -> None:
        """
        Generate and save a time-series graph of the recorded data points

        Note:
            This function does not need to be manually called, as it should be
            called automatically when the user program exits.
            If some variables look squished on the line graph, consider normalizing
            your variables so they have similar magnitude.
        """


