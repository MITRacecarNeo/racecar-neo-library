"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: lidar_real.py
File Description: Contains the Lidar module of the racecar_core library
"""

from lidar import Lidar

# General
import numpy as np
from nptyping import NDArray

# ROS2
import rclpy as ros2
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class LidarReal(Lidar):
    # The ROS topic from which we get Lidar data
    __SCAN_TOPIC = "/scan"

    def __init__(self):
        # ROS node
        self.node = ros2.create_node("scan_sub")

        # subscribe to the scan topic, which will call
        # __scan_callback every time the lidar sends data
        self.__scan_sub = self.node.create_subscription(
            LaserScan, self.__SCAN_TOPIC, self.__scan_callback, qos_profile_sensor_data
        )

        self.__samples = np.empty(0)
        self.__samples_new = np.empty(0)

    # LIDAR Scan returns value in meters, multiplying by 100 to be processed in cm
    # LIDAR Scan reversed, flipping order of data entry to correct for CW spin - matches with sim
    # For RPLidar - replace "inf" with 0 to match sim LIDAR data
    def __scan_callback(self, data):
        scan_data = np.flip(np.multiply(np.array(data.ranges), 100))
        self.__samples_new = np.array([0 if str(x) == "inf" else x for x in scan_data])

    def __update(self):
        self.__samples = self.__samples_new

    def get_samples(self) -> NDArray[720, np.float32]:
        return self.__samples

    def get_samples_async(self) -> NDArray[720, np.float32]:
        return self.__samples_new
