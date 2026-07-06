"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: nav.py
File Description: Defines the interface for the Nav module of the racecar_core library.
"""

import abc
from typing import List, Optional, Tuple


class Nav(abc.ABC):
    """
    Plans paths over the SLAM map and follows them to a goal.

    Works alongside rc.slam: rc.slam builds the map and tracks the pose, rc.nav
    plans a route to a goal on that map and turns it into drive commands. The
    same interface is available in simulation and on the physical car, so one
    navigation program runs unchanged in both. On the real car it is backed by
    Nav2; in the simulator by the in-browser planner.
    """

    @abc.abstractmethod
    def set_goal(self, x: float, y: float, heading: Optional[float] = None) -> None:
        """
        Sets the navigation goal in map coordinates.

        Args:
            x: Goal x in meters (map frame).
            y: Goal y in meters (map frame).
            heading: Optional target heading in radians. If omitted, only the
                position is enforced.

        Example::

            rc.nav.set_goal(2.0, 1.0)
        """
        pass

    @abc.abstractmethod
    def get_goal(self) -> Optional[Tuple[float, float]]:
        """
        Returns the active goal position, or None if no goal is set.

        Example::

            goal = rc.nav.get_goal()
        """
        pass

    @abc.abstractmethod
    def get_goal_heading(self) -> Optional[float]:
        """
        Returns the active goal heading in radians, or None if none was set.

        Example::

            heading = rc.nav.get_goal_heading()
        """
        pass

    @abc.abstractmethod
    def clear_goal(self) -> None:
        """
        Clears the active goal and any planned path.

        Example::

            rc.nav.clear_goal()
        """
        pass

    @abc.abstractmethod
    def plan(
        self, goal_x: Optional[float] = None, goal_y: Optional[float] = None
    ) -> List[Tuple[float, float]]:
        """
        Plans a path from the current pose to the goal.

        Args:
            goal_x: Optional goal x in meters; if given, also sets the goal.
            goal_y: Optional goal y in meters.

        Returns:
            The path as a list of (x, y) waypoints in meters (map frame). Empty
            if no goal is set or no path was found.

        Example::

            path = rc.nav.plan(2.0, 1.0)
        """
        pass

    @abc.abstractmethod
    def plan_hybrid(
        self,
        goal_x: Optional[float] = None,
        goal_y: Optional[float] = None,
        goal_heading: Optional[float] = None,
    ) -> List[Tuple[float, float, float, int]]:
        """
        Plans a kinematically-feasible path from the current pose to the goal.

        Args:
            goal_x: Optional goal x in meters; if given, also sets the goal.
            goal_y: Optional goal y in meters.
            goal_heading: Optional target heading in radians.

        Returns:
            The path as a list of (x, y, theta, direction) waypoints, where
            direction is +1 for forward segments and -1 for reverse.

        Example::

            path = rc.nav.plan_hybrid(2.0, 1.0, 0.0)
        """
        pass

    @abc.abstractmethod
    def invalidate(self) -> None:
        """
        Discards the cached path so the next follow call replans.

        Example::

            rc.nav.invalidate()
        """
        pass

    @abc.abstractmethod
    def follow_goal(self, speed: float = 0.5) -> Tuple[float, float, str]:
        """
        Returns one frame of drive commands toward the goal along the plan.

        Args:
            speed: Forward speed in the range [0, 1] while driving.

        Returns:
            A tuple (speed, angle, status). speed and angle are in [-1, 1] for
            rc.drive.set_speed_angle; status is one of "no_goal", "no_path",
            "driving", or "arrived".

        Example::

            speed, angle, status = rc.nav.follow_goal()
            rc.drive.set_speed_angle(speed, angle)
        """
        pass

    @abc.abstractmethod
    def follow_hybrid_goal(self, speed: float = 0.3) -> Tuple[float, float, str]:
        """
        Follows a kinematic path to the goal, with reverse and switchbacks.

        Args:
            speed: Forward speed in the range [0, 1].

        Returns:
            A tuple (speed, angle, status). status is one of "no_goal",
            "no_path", "driving", "reversing", "switchback", or "arrived".

        Example::

            speed, angle, status = rc.nav.follow_hybrid_goal()
            rc.drive.set_speed_angle(speed, angle)
        """
        pass
