"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: nav_real.py
File Description: Contains the Nav module of the racecar_core library. Talks
to the driver's navigator (nav_server_node) through its nav_link: a goal is a
mission of one waypoint, driven under this program's hold on the car. Nothing
is created before the first call: no node, subscription or timer. Without the
driver installed, every call reports "off".
"""

import math
import os
import threading
import time
from typing import List, Optional, Tuple

from nav import Nav
import racecar_utils as rc_utils

import rclpy as ros2

# The navigator's states, as status words.
STATUS = {
    "running": Nav.NAVIGATING,
    "dwelling": Nav.WAITING,
    "relocalizing": Nav.LOST,
    "paused": Nav.PAUSED,
    "arrived": Nav.ARRIVED,
    "failed": Nav.FAILED,
    "stalled": Nav.STALLED,
    "stopped": Nav.CANCELED,
}
HOLDING = (Nav.NAVIGATING, Nav.WAITING, Nav.LOST, Nav.PAUSED)
CONNECT_SEC = 1.5  # the navigator's state arrives 5 times a second
ALIVE_SEC = 0.2  # the navigator stops a goal 0.5 s after the last one


def driver_modules():
    """Return (NavLink, missions) from the driver, or None without it."""
    try:
        from racecar_neo_ros2_driver import missions
        from racecar_neo_ros2_driver.nav_link import NavLink
    except ImportError:
        return None
    return NavLink, missions


class NavReal(Nav):
    def __init__(self, drive, slam, modules=driver_modules, executor=None):
        self.node = None
        self.__drive = drive
        self.__slam = slam
        self.__modules = modules
        self.__executor = executor
        self.__lock = threading.Lock()
        self.__started = False
        self.__off = False
        self.__link = None
        self.__missions = None
        self.__owner = f"program-{os.getpid()}"
        self.__active = False  # this program's goal holds the driving
        self.__sending = False
        self.__ending = ""
        self.__said = ""
        self.__path: List[Tuple[float, float]] = []

    # -- setup on the first call --

    def __start(self) -> bool:
        """Connect on the first call; return False when navigation is off."""
        if self.__started:
            return not self.__off
        self.__started = True
        found = self.__modules()
        if found is None:
            self.__off = True
            rc_utils.print_warning("rc.nav works only on the car.")
            return False
        link_class, self.__missions = found
        self.node = ros2.create_node("nav_client")
        executor = self.__executor or ros2.get_global_executor()
        executor.add_node(self.node)
        self.__link = link_class(self.node)
        from nav_msgs.msg import Path

        self.node.create_subscription(Path, "/plan", self.__on_plan, 10)
        self.node.create_timer(ALIVE_SEC, self.__tick)
        deadline = time.monotonic() + CONNECT_SEC
        while not self.__link.alive and time.monotonic() < deadline:
            time.sleep(0.05)
        return True

    def __on_plan(self, msg) -> None:
        points = [(p.pose.position.x, p.pose.position.y) for p in msg.poses]
        with self.__lock:
            self.__path = points

    def __tick(self) -> None:
        """Keep this program's goal alive, and notice when it ends."""
        with self.__lock:
            if not self.__active:
                return
            view = self.__link.view()
            mine = self.__link.alive and view["owner"] == self.__owner
            if mine and view["state"] in ("running", "dwelling", "relocalizing", "paused"):
                self.__link.notify("alive", owner=self.__owner)
                return
            self.__ending = STATUS.get(view["state"], Nav.CANCELED) if mine else Nav.CANCELED
            self.__end()

    def __end(self) -> None:
        """The caller holds the lock."""
        self.__active = False
        self.__path = []
        self.__drive._nav_drives(False)

    def __say(self, text: str) -> None:
        """Print a refusal once, until it changes or a goal starts."""
        if text != self.__said:
            print(f">> {text}")
            self.__said = text

    # -- goals --

    def __send(self, mission) -> bool:
        if not self.__start():
            return False
        # The answer arrives on the executor's thread, so no lock is held while waiting.
        with self.__lock:
            if self.__active or self.__sending:
                self.__say("rc.nav is already driving. Cancel it first.")
                return False
            if not self.__link.alive:
                self.__say("Load a map first.")
                return False
            self.__sending = True
            self.__drive._nav_drives(True)
        try:
            ok, message = self.__link.command(
                "start", owner=self.__owner, name="Program", pid=os.getpid(),
                heartbeat=True, mission=mission,
            )
        finally:
            self.__sending = False
        with self.__lock:
            if not ok:
                self.__drive._nav_drives(False)
                self.__say(message)
                return False
            self.__active, self.__ending, self.__said, self.__path = True, "", "", []
            return True

    def __goal(self, x: float, y: float, heading: Optional[float]):
        return self.__missions.parse({"waypoints": [{"x": x, "y": y, "heading_deg": heading}]})

    def go_to(self, x: float, y: float, heading: Optional[float] = None) -> bool:
        if not self.__start():
            return False
        try:
            mission = self.__goal(x, y, heading)
        except (TypeError, ValueError) as exc:
            self.__say(f"Not a goal: {exc}")
            return False
        return self.__send(mission)

    def move(self, distance: float) -> bool:
        if not self.__start():
            return False
        pose = self.__slam.get_pose_async()
        if pose is None:
            self.__say("The car has no pose on the map. Load a map first.")
            return False
        x, y, heading = pose
        rad = math.radians(heading)
        return self.go_to(x + distance * math.cos(rad), y + distance * math.sin(rad), heading)

    def run_mission(self, name: str) -> bool:
        if not self.__start():
            return False
        map_name = self.__slam.get_map_name()
        if not map_name:
            self.__say("Load a map first.")
            return False
        try:
            mission = self.__missions.load(map_name, name)
        except (OSError, ValueError, KeyError):
            self.__say(f"No mission {name} for {map_name}.")
            return False
        mission["record"]["on"] = False  # recording is the Planner's
        return self.__send(mission)

    def get_missions(self) -> List[str]:
        if not self.__start():
            return []
        map_name = self.__slam.get_map_name()
        return [m["name"] for m in self.__missions.listing(map_name)] if map_name else []

    def cancel(self) -> None:
        if not self.__started or self.__off:
            return
        with self.__lock:
            if not self.__active:
                return
        self.__link.command("stop")
        with self.__lock:
            if self.__active:
                self.__ending = Nav.CANCELED
                self.__end()

    # -- state --

    def get_status(self) -> str:
        if not self.__start():
            return Nav.OFF
        with self.__lock:
            if not self.__link.alive:
                return Nav.OFF
            if not self.__active:
                return self.__ending or Nav.IDLE
            view = self.__link.view()
            if view["state"] == "paused" and view["reason"] in ("failed", "stalled"):
                return view["reason"]  # for a moment, before the navigator ends it
            word = STATUS.get(view["state"], Nav.IDLE) if view["owner"] == self.__owner else Nav.CANCELED
            if word not in HOLDING:
                # Ended: rc.drive drives again from this call on, not from the next tick.
                self.__ending = word
                self.__end()
            return word

    def is_active(self) -> bool:
        return self.get_status() in HOLDING

    def get_distance_left(self) -> Optional[float]:
        if not self.is_active():
            return None
        return self.__link.view()["left"]

    def get_path(self) -> List[Tuple[float, float]]:
        if not self.is_active():
            return []
        with self.__lock:
            return list(self.__path)

    def wait(self, timeout: Optional[float] = None) -> str:
        end = None if timeout is None else time.monotonic() + timeout
        while self.is_active() and (end is None or time.monotonic() < end):
            time.sleep(0.05)
        return self.get_status()

    def _stop(self) -> None:
        """BACK and the end of the program: cancel this program's goal."""
        self.cancel()
