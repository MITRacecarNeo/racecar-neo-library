"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: racecar_core.py
File Description: Contains the Racecar class, the top level of the racecar_core library
"""

import abc
import sys
from typing import Callable, Optional

import camera
import controller
import display
import drive
import lidar
import physics
import telemetry

import racecar_utils as rc_utils


class Racecar(abc.ABC):
    """
    The top level racecar module containing several submodules which interface
    with and control the different pieces of the RACECAR hardware.
    """

    def __init__(self) -> None:
        self.camera: camera.Camera
        self.controller: controller.Controller
        self.display: display.Display
        self.drive: drive.Drive
        self.lidar: lidar.Lidar
        self.physics: physics.Physics
        self.telemetry: telemetry.Telemetry

    @abc.abstractmethod
    def go(self) -> None:
        """
        Starts the RACECAR, beginning in default drive mode.

        Note:
            go idles blocks execution until the program is exited when START + END are
            pressed simultaneously.
        """
        pass

    @abc.abstractmethod
    def set_start_update(
        self,
        start: Callable[[], None],
        update: Callable[[], None],
        update_slow: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Sets the start and update functions used in user program mode.

        Args:
            start: A function called once when the car enters user program mode.
            update: A function called every frame in user program mode. Approximately
                60 frames occur per second.
            update_slow: A function called once per fixed time interval in user
                program mode (by default once per second).

        Note:
            The provided functions should not take any parameters.

        Example::

            # Create a racecar object
            rc = Racecar()

            # Define a start function
            def start():
                print("This function is called once")

            # Define an update function
            def update():
                print("This function is called every frame")

            # Provide the racecar with the start and update functions
            rc.set_start_update(start, update)

            # Tell the racecar to run until the program is exited
            rc.go()
        """
        pass

    @abc.abstractmethod
    def get_delta_time(self) -> float:
        """
        Returns the number of seconds elapsed in the previous frame.

        Returns:
            The number of seconds between the start of the previous frame and
            the start of the current frame.

        Example::

            # Increases counter by the number of seconds elapsed in the previous frame
            counter += rc.get_delta_time()
        """
        pass

    @abc.abstractmethod
    def set_update_slow_time(self, time: float = 1.0) -> None:
        """
        Changes the time between calls to update_slow.

        Args:
            time: The time in seconds between calls to update_slow.

        Example::

            # Sets the time between calls to update_slow to 2 seconds
            rc.set_update_slow_time(2)
        """
        pass


def create_racecar(isSimulation: Optional[bool] = None) -> Racecar:
    """
    Generates a racecar object based on the isSimulation argument or execution flags.

    Args:
        isSimulation: If True, create a RacecarSim, if False, create a RacecarReal,
            if None, decide based on the command line arguments

    Returns:
        A RacecarSim object (for use with the Unity simulation) or a RacecarReal object
        (for use on the physical car).

    Note:
        If isSimulation is None, this function will return a RacecarSim if the program
        was executed with the "-s" flag and a RacecarReal otherwise.

        If the program was executed with the "-d" flag, a display window is created.

        If the program was executed with the "-h" flag, it is run in headless mode,
        which disables the display module.
    """
    library_path: str = __file__.replace("racecar_core.py", "")
    is_headless: bool = "-h" in sys.argv
    initialize_display: bool = "-d" in sys.argv

    # If isSimulation was not specified, set it to True if the user ran the program with
    # the -s flag and false otherwise
    if isSimulation is None:
        isSimulation = "-s" in sys.argv

    racecar: Racecar
    if isSimulation:
        sys.path.insert(1, library_path + "simulation")
        from racecar_core_sim import RacecarSim

        racecar = RacecarSim(is_headless)
    else:
        sys.path.insert(1, library_path + "real")
        from racecar_core_real import RacecarReal

        racecar = RacecarReal(is_headless)

    if initialize_display:
        racecar.display.create_window()

    rc_utils.print_colored(
        ">> Racecar created with the following options:"
        + f"\n    Simulation (-s): [{isSimulation}]"
        + f"\n    Headless (-h): [{is_headless}]"
        + f"\n    Initialize with display (-d): [{initialize_display}]",
        rc_utils.TerminalColor.pink,
    )

    return racecar
