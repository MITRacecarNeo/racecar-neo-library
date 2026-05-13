"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: vision_real.py
File Description: Contains the Vision module of the racecar_core library.
Subscribes to /edgetpu/inference and surfaces detections as Detection objects.
Ported from MITUavNeo/uav-neo-library's detector_real.
"""

from typing import List

from vision import Vision, Detection

import rclpy as ros2
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSReliabilityPolicy,
    QoSProfile,
)
from vision_msgs.msg import Detection2DArray


class VisionReal(Vision):
    __INFERENCE_TOPIC = "/edgetpu/inference"

    def __init__(self):
        self.node = ros2.create_node("vision_sub")

        qos_profile = QoSProfile(depth=10)
        qos_profile.history = QoSHistoryPolicy.KEEP_LAST
        qos_profile.reliability = QoSReliabilityPolicy.BEST_EFFORT
        qos_profile.durability = QoSDurabilityPolicy.VOLATILE

        self.__detections_sub = self.node.create_subscription(
            Detection2DArray,
            self.__INFERENCE_TOPIC,
            self.__inference_callback,
            qos_profile,
        )
        self.__detections: List[Detection] = []
        self.__detections_new: List[Detection] = []

    def __inference_callback(self, msg):
        detections: List[Detection] = []
        for det in msg.detections:
            if not det.results:
                continue
            hyp = det.results[0].hypothesis
            bbox = (
                det.bbox.center.position.x,
                det.bbox.center.position.y,
                det.bbox.size_x,
                det.bbox.size_y,
            )
            detections.append(Detection(hyp.class_id, hyp.score, bbox))
        self.__detections_new = detections

    def __update(self):
        self.__detections = self.__detections_new

    def get_detections(self) -> List[Detection]:
        return list(self.__detections)

    def get_detections_async(self) -> List[Detection]:
        return list(self.__detections_new)
