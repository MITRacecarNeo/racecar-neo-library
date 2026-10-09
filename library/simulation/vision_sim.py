"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: vision_sim.py
File Description: Contains the Vision module of the racecar_core library for the
simulator. RacecarSim has no Coral EdgeTPU, so there are never any detections; the
first call prints a warning.
"""

from typing import List

import racecar_utils as rc_utils
from vision import Detection, Vision


class VisionSim(Vision):
    def __init__(self) -> None:
        self.__warned = False

    def get_detections(self) -> List[Detection]:
        self.__warn()
        return []

    def get_detections_async(self) -> List[Detection]:
        self.__warn()
        return []

    def __warn(self) -> None:
        if not self.__warned:
            self.__warned = True
            rc_utils.print_warning(
                "RacecarSim has no EdgeTPU; rc.vision.get_detections() always returns an empty list."
            )
