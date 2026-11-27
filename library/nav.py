"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: nav.py
File Description: Defines the interface of the Nav module of the racecar_core
library. Sends the car to points on the loaded map with the driver's
navigator (Nav2), as `racecar nav` and the Planner (port 8090) do.
"""

import abc
from typing import List, Optional, Tuple


class Nav(abc.ABC):
    """
    Drives the car to points on the loaded map.

    A goal holds the car's driving, not the program: update() goes on as
    usual, and rc.drive calls are ignored until the goal ends. Positions are
    map meters and headings degrees, as in rc.slam.

    Status words (get_status):
        "off": no navigation (no map loaded, the simulator, or no driver).
        "idle": this program has no goal.
        "navigating": driving to a waypoint.
        "waiting": at a mission waypoint, during its wait.
        "lost": localization lost. The car stops and goes on once localized.
        "paused": paused from the Planner; goes on at Resume.
        "arrived", "failed", "stalled", "canceled": how the last goal ended,
        until the next goal.
    """

    OFF = "off"
    IDLE = "idle"
    NAVIGATING = "navigating"
    WAITING = "waiting"
    LOST = "lost"
    PAUSED = "paused"
    ARRIVED = "arrived"
    FAILED = "failed"
    STALLED = "stalled"
    CANCELED = "canceled"

    @abc.abstractmethod
    def go_to(self, x: float, y: float, heading: Optional[float] = None) -> bool:
        """
        Drives to a point on the loaded map.

        Args:
            x: Map x in meters.
            y: Map y in meters.
            heading: The heading to face there in degrees, or None for any.

        Returns:
            True when the goal started. False when it was refused (another goal
            or mission runs, something else drives, no map, not localized, or
            stalled). The reason is printed once.

        Example::

            # Drive to (2, 1) when A is pressed
            if rc.controller.was_pressed(rc.controller.Button.A):
                rc.nav.go_to(2.0, 1.0)
        """
        pass

    @abc.abstractmethod
    def move(self, distance: float) -> bool:
        """
        Drives a distance along the car's heading.

        Args:
            distance: Meters ahead; negative backs up.

        Returns:
            True when the goal started, else False (see go_to).
        """
        pass

    @abc.abstractmethod
    def run_mission(self, name: str) -> bool:
        """
        Runs a mission saved in the Planner for the loaded map.

        Args:
            name: The mission's name (see get_missions).

        Returns:
            True when the mission started, else False (see go_to).

        Note:
            A mission run from a program does not record; recording is the
            Planner's.
        """
        pass

    @abc.abstractmethod
    def get_missions(self) -> List[str]:
        """
        Returns the names of the missions saved for the loaded map, [] without a map.
        """
        pass

    @abc.abstractmethod
    def cancel(self) -> None:
        """
        Stops this program's goal or mission; the car stops.

        Note:
            BACK and the end of the program cancel it too. A goal or mission
            started elsewhere (the Planner, racecar nav) is left alone.
        """
        pass

    @abc.abstractmethod
    def is_active(self) -> bool:
        """
        Returns True while this program's goal or mission holds the driving:
        navigating, waiting, lost or paused.
        """
        pass

    @abc.abstractmethod
    def get_status(self) -> str:
        """
        Returns the status word (see the class description).

        Example::

            if rc.nav.get_status() == rc.nav.ARRIVED:
                print("Made it")
        """
        pass

    @abc.abstractmethod
    def get_distance_left(self) -> Optional[float]:
        """
        Returns the meters left to the current waypoint, or None without a goal.
        """
        pass

    @abc.abstractmethod
    def get_path(self) -> List[Tuple[float, float]]:
        """
        Returns the path Nav2 planned to the current waypoint as (x, y) points,
        [] without a goal. Compare it with a path your own planner finds.
        """
        pass

    @abc.abstractmethod
    def wait(self, timeout: Optional[float] = None) -> str:
        """
        Blocks until the goal ends or timeout seconds pass. For notebooks only.
        Do not call it in update().

        Returns:
            The status word.
        """
        pass
