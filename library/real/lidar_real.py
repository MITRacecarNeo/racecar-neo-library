"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: lidar_real.py
File Description: Contains the Lidar module of the racecar_core library
"""

from lidar import Lidar

# General
import math
import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

# ROS2
import rclpy as ros2
from rclpy.qos import qos_profile_sensor_data, DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from tf2_msgs.msg import TFMessage


class LidarReal(Lidar):
    # The ROS topic from which we get Lidar data
    __SCAN_TOPIC = "/scan"
    # The lidar's mount on the car, published by the driver from the car's
    # calibration: the base_link -> laser transform.
    __TF_TOPIC = "/tf_static"
    # Until that transform arrives: the RACECAR Neo's lidar faces aft.
    __DEFAULT_YAW = math.pi

    def __init__(self):
        # ROS node
        self.node = ros2.create_node("scan_sub")

        # subscribe to the scan topic, which will call
        # __scan_callback every time the lidar sends data
        self.__scan_sub = self.node.create_subscription(
            LaserScan, self.__SCAN_TOPIC, self.__scan_callback, qos_profile_sensor_data
        )
        # /tf_static is latched: the mount arrives once, right after subscribing
        latched = QoSProfile(
            depth=100,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.__tf_sub = self.node.create_subscription(
            TFMessage, self.__TF_TOPIC, self.__tf_callback, latched
        )

        self.__yaw = self.__DEFAULT_YAW
        self.__samples = np.empty(0)
        self.__samples_new = np.empty(0)

    def __tf_callback(self, data):
        for t in data.transforms:
            if t.header.frame_id == "base_link" and t.child_frame_id == "laser":
                q = t.transform.rotation
                self.__yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

    # LIDAR Scan returns value in meters, multiplying by 100 to be processed in cm.
    # Sample j looks j * 360 / n degrees clockwise from the car's nose, as in
    # the simulator: each sample takes the ray that points there, given the
    # lidar's mount. No return ("inf") reads as 0, to match the sim lidar.
    def __scan_callback(self, data):
        ranges = np.asarray(data.ranges, dtype=np.float64) * 100
        ranges[~np.isfinite(ranges)] = 0
        self.__samples_new = ranges[self.__ray_order(data, len(ranges))]

    def __ray_order(self, data, n):
        """Index of the ray behind each sample."""
        clockwise = np.arange(n) * (2 * math.pi / n)
        # A ray at raw angle r points r + yaw counterclockwise from the nose.
        raw = -clockwise - self.__yaw
        # Into (-pi, pi]: the nose of an aft-facing lidar is its last ray, as before.
        raw = math.pi - np.mod(math.pi - raw, 2 * math.pi)
        return np.round((raw - data.angle_min) / data.angle_increment).astype(int) % n

    def __update(self):
        self.__samples = self.__samples_new

    def get_samples(self) -> NDArray[1080, np.float32]:
        return self.__samples

    def get_samples_async(self) -> NDArray[1080, np.float32]:
        return self.__samples_new
