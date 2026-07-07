"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: camera_real.py
File Description: Contains the Camera module of the racecar_core library
"""

from camera import Camera

import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

import rclpy as ros2
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSReliabilityPolicy,
    QoSProfile,
)
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


class CameraReal(Camera):
    # RACECAR topics fed by the RealSense D435i; realsense.launch.py remaps the
    # RealSense color/image_raw and depth/image_rect_raw onto these names.
    __COLOR_TOPIC = "/camera/color"
    __DEPTH_TOPIC = "/camera/depth"

    def __init__(self):
        self.__bridge = CvBridge()
        self.node = ros2.create_node("image_sub")

        qos_profile = QoSProfile(depth=10)
        qos_profile.history = QoSHistoryPolicy.KEEP_LAST
        qos_profile.reliability = QoSReliabilityPolicy.BEST_EFFORT
        qos_profile.durability = QoSDurabilityPolicy.VOLATILE

        self.__color_image_sub = self.node.create_subscription(
            Image, self.__COLOR_TOPIC, self.__color_callback, qos_profile
        )
        self.__color_image = None
        self.__color_image_new = None

        self.__depth_image_sub = self.node.create_subscription(
            Image, self.__DEPTH_TOPIC, self.__depth_callback, qos_profile
        )
        self.__depth_image = None
        self.__depth_image_new = None

    def __color_callback(self, data):
        try:
            self.__color_image_new = self.__bridge.imgmsg_to_cv2(
                data, desired_encoding="bgr8"
            )
        except CvBridgeError as e:
            print(f"camera_real: failed to decode color frame: {e}")

    def __depth_callback(self, data):
        # RealSense depth is 16UC1 (uint16) in millimeters; the API returns cm.
        try:
            depth_mm = self.__bridge.imgmsg_to_cv2(data, desired_encoding="passthrough")
            self.__depth_image_new = depth_mm.astype(np.float32) / 10.0
        except CvBridgeError as e:
            print(f"camera_real: failed to decode depth frame: {e}")

    def __update(self):
        self.__color_image = self.__color_image_new
        self.__depth_image = self.__depth_image_new

    def get_color_image_no_copy(self) -> NDArray[(480, 640, 3), np.uint8]:
        return self.__color_image

    def get_color_image_async(self) -> NDArray[(480, 640, 3), np.uint8]:
        return self.__color_image_new

    def get_depth_image(self) -> NDArray[(480, 640), np.float32]:
        return self.__depth_image

    def get_depth_image_async(self) -> NDArray[(480, 640), np.float32]:
        return self.__depth_image_new
