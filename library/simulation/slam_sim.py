"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: slam_sim.py
File Description: Contains the Slam module of the racecar_core library for the
simulator. RacecarSim reports no map pose, so the mode is always "off"; the
first call prints a warning.
"""

from typing import Optional, Tuple

import racecar_utils as rc_utils
from slam import OccupancyMap, Slam


class SlamSim(Slam):
    def __init__(self) -> None:
        self.__warned = False

    def get_mode(self) -> str:
        self.__warn()
        return "off"

    def get_map_name(self) -> str:
        self.__warn()
        return ""

    def is_localized(self) -> bool:
        self.__warn()
        return False

    def get_pose(self) -> Optional[Tuple[float, float, float]]:
        self.__warn()
        return None

    def get_pose_async(self) -> Optional[Tuple[float, float, float]]:
        self.__warn()
        return None

    def get_map(self) -> Optional[OccupancyMap]:
        self.__warn()
        return None

    def save_map(self) -> None:
        self.__warn()

    def get_save_status(self) -> str:
        self.__warn()
        return "failed: not available in RacecarSim"

    def __warn(self) -> None:
        if not self.__warned:
            self.__warned = True
            rc_utils.print_warning(
                "RacecarSim has no SLAM; rc.slam reports mode \"off\" and no pose or map."
            )
