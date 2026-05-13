"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: vision.py
File Description: Defines the interface of the Vision module of the
racecar_core library. Exposes Coral EdgeTPU object detections to student
code as a list of Detection objects.
"""

import abc
from typing import List


class Detection:
    """
    A single object detection result from the EdgeTPU.

    Attributes:
        class_id: Label string (or numeric ID as string) of the detected
            object, as emitted by edgetpu_node.
        score: Confidence in [0.0, 1.0].
        bbox: (center_x, center_y, width, height) in pixels of the source
            image (the /camera/forward frame).
    """

    def __init__(self, class_id: str, score: float, bbox: tuple) -> None:
        self.class_id = class_id
        self.score = score
        self.bbox = bbox

    def __repr__(self) -> str:
        return (
            f"Detection(class_id={self.class_id!r}, score={self.score:.2f}, "
            f"bbox=({self.bbox[0]:.0f}, {self.bbox[1]:.0f}, "
            f"{self.bbox[2]:.0f}, {self.bbox[3]:.0f}))"
        )


class Vision(abc.ABC):
    """
    Provides access to onboard ML object detection via the Coral EdgeTPU.
    """

    @abc.abstractmethod
    def get_detections(self) -> List[Detection]:
        """
        Returns the latest list of object detections from the EdgeTPU.

        Returns:
            A list of Detection objects with class_id, score, and pixel-space
            bounding box. Empty list if nothing was detected or the edgetpu
            node is not publishing.

        Example::

            detections = rc.vision.get_detections()
            for det in detections:
                print(f"Found {det.class_id} at ({det.bbox[0]}, {det.bbox[1]})")
        """
        pass

    @abc.abstractmethod
    def get_detections_async(self) -> List[Detection]:
        """
        Returns the latest detections without the car in "go" mode.

        Warning:
            This function breaks the start-update paradigm and should only
            be used in Jupyter Notebook.
        """
        pass
