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

import threading
import time

import rclpy as ros2
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSReliabilityPolicy,
    QoSProfile,
)
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


class _Frame:
    """
    The newest frame as received, decoded on first request.

    Frames arrive at up to 60 per second; a program that reads a few of them
    should not pay to decode the rest. The subscription hands over the raw
    message bytes, and nothing is deserialized until a getter asks.
    """

    def __init__(self, raw, decode):
        self.__raw = raw
        self.__decode = decode
        self.__image = None

    def image(self):
        if self.__raw is not None:
            self.__image = self.__decode(deserialize_message(self.__raw, Image))
            self.__raw = None
        return self.__image


class CameraReal(Camera):
    # RACECAR topics fed by the RealSense D435i; realsense.launch.py remaps the
    # RealSense color/image_raw and depth/image_rect_raw onto these names.
    __COLOR_TOPIC = "/camera/color"
    __DEPTH_TOPIC = "/camera/depth"

    def __init__(self):
        self.__bridge = CvBridge()
        self.node = ros2.create_node("image_sub")

        self.__qos = QoSProfile(depth=1)
        self.__qos.history = QoSHistoryPolicy.KEEP_LAST
        self.__qos.reliability = QoSReliabilityPolicy.BEST_EFFORT
        self.__qos.durability = QoSDurabilityPolicy.VOLATILE

        # Each stream is subscribed on the first request for it, so a program
        # that never reads the camera does not receive its frames.
        self.__subscribe_lock = threading.Lock()
        self.__color_image_sub = None
        self.__color = None
        self.__color_new = None
        self.__depth_image_sub = None
        self.__depth = None
        self.__depth_new = None

    # Longest wait for the first frame after subscribing.
    __FIRST_FRAME_TIMEOUT_S = 1.0

    def __subscribe_color(self):
        with self.__subscribe_lock:
            if self.__color_image_sub is not None:
                return
            self.__color_image_sub = self.node.create_subscription(
                Image, self.__COLOR_TOPIC, self.__color_callback, self.__qos, raw=True
            )
        self.__wait_for(lambda: self.__color_new)

    def __subscribe_depth(self):
        with self.__subscribe_lock:
            if self.__depth_image_sub is not None:
                return
            self.__depth_image_sub = self.node.create_subscription(
                Image, self.__DEPTH_TOPIC, self.__depth_callback, self.__qos, raw=True
            )
        self.__wait_for(lambda: self.__depth_new)

    def __wait_for(self, frame):
        end = time.monotonic() + self.__FIRST_FRAME_TIMEOUT_S
        while frame() is None and time.monotonic() < end:
            time.sleep(0.01)

    def __color_callback(self, raw):
        self.__color_new = _Frame(raw, self.__decode_color)

    def __depth_callback(self, raw):
        self.__depth_new = _Frame(raw, self.__decode_depth)

    def __decode_color(self, msg):
        try:
            return self.__bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except CvBridgeError as e:
            print(f"camera_real: failed to decode color frame: {e}")
            return None

    def __decode_depth(self, msg):
        # RealSense depth is 16UC1 (uint16) in millimeters; the API returns cm.
        try:
            depth_mm = self.__bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
            return depth_mm.astype(np.float32) / 10.0
        except CvBridgeError as e:
            print(f"camera_real: failed to decode depth frame: {e}")
            return None

    def __update(self):
        self.__color = self.__color_new
        self.__depth = self.__depth_new

    @staticmethod
    def __image(frame):
        return None if frame is None else frame.image()

    def get_color_image_no_copy(self) -> NDArray[(480, 640, 3), np.uint8]:
        if self.__color_image_sub is None:
            self.__subscribe_color()
            self.__color = self.__color_new
        return self.__image(self.__color)

    def get_color_image_async(self) -> NDArray[(480, 640, 3), np.uint8]:
        if self.__color_image_sub is None:
            self.__subscribe_color()
        return self.__image(self.__color_new)

    def get_depth_image(self) -> NDArray[(480, 640), np.float32]:
        if self.__depth_image_sub is None:
            self.__subscribe_depth()
            self.__depth = self.__depth_new
        return self.__image(self.__depth)

    def get_depth_image_async(self) -> NDArray[(480, 640), np.float32]:
        if self.__depth_image_sub is None:
            self.__subscribe_depth()
        return self.__image(self.__depth_new)
