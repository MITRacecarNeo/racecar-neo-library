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
    # The ROS topic from which we read camera data. gscam publishes a raw
    # sensor_msgs/Image after decoding the MJPEG stream itself, so we use
    # cv_bridge with bgr8 (not cv.imdecode on a JPEG buffer).
    __COLOR_TOPIC = "/camera/forward"

    # v2 cameras (Logitech BRIO + Arducam B0578) are RGB-only. Depth is not
    # available on the physical RACECAR; the depth API is retained so labs
    # that compile against the sim still parse, but every call warns.
    __DEPTH_WARNING = (
        "rc.camera.get_depth_image*() is unsupported on the v2 RACECAR — "
        "the physical platform has no depth sensor. This call returns None. "
        "Depth-based labs only run in the simulator."
    )

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

        self.__depth_warned = False

    def __color_callback(self, data):
        try:
            self.__color_image_new = self.__bridge.imgmsg_to_cv2(
                data, desired_encoding="bgr8"
            )
        except CvBridgeError as e:
            print(f"camera_real: failed to decode color frame: {e}")

    def __warn_depth_unsupported(self):
        if not self.__depth_warned:
            print(f"[WARNING] {self.__DEPTH_WARNING}")
            self.__depth_warned = True

    def __update(self):
        self.__color_image = self.__color_image_new

    def get_color_image_no_copy(self) -> NDArray[(480, 640, 3), np.uint8]:
        return self.__color_image

    def get_color_image_async(self) -> NDArray[(480, 640, 3), np.uint8]:
        return self.__color_image_new

    def get_depth_image(self) -> NDArray[(480, 640), np.float32]:
        self.__warn_depth_unsupported()
        return None

    def get_depth_image_async(self) -> NDArray[(480, 640), np.float32]:
        self.__warn_depth_unsupported()
        return None
