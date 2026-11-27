"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: nav_sim.py
File Description: Contains the Nav module of the racecar_core library for the
simulator. RacecarSim has no navigator, so every call reports "off"; the first
call prints a warning.
"""

from typing import List, Optional, Tuple

import racecar_utils as rc_utils
from nav import Nav


class NavSim(Nav):
    def __init__(self) -> None:
        self.__warned = False

    def __warn(self) -> None:
        if not self.__warned:
            rc_utils.print_warning("rc.nav works only on the car.")
            self.__warned = True

    def go_to(self, x: float, y: float, heading: Optional[float] = None) -> bool:
        self.__warn()
        return False

    def move(self, distance: float) -> bool:
        self.__warn()
        return False

    def run_mission(self, name: str) -> bool:
        self.__warn()
        return False

    def get_missions(self) -> List[str]:
        self.__warn()
        return []

    def cancel(self) -> None:
        self.__warn()

    def is_active(self) -> bool:
        self.__warn()
        return False

    def get_status(self) -> str:
        self.__warn()
        return Nav.OFF

    def get_distance_left(self) -> Optional[float]:
        self.__warn()
        return None

    def get_path(self) -> List[Tuple[float, float]]:
        self.__warn()
        return []

    def wait(self, timeout: Optional[float] = None) -> str:
        self.__warn()
        return Nav.OFF
