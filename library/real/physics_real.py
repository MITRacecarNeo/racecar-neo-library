"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: physics_real.py
File Description: Contains the Physics module of the racecar_core library
"""

from physics import Physics

# General
from collections import deque
import numpy as np
from nptyping import NDArray

# ROS2
import rclpy as ros2
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSReliabilityPolicy,
    QoSProfile,
)
from sensor_msgs.msg import Imu, MagneticField


class PhysicsReal(Physics):
    # The ROS topic from which we read imu data
    __IMU_TOPIC = "/imu"
    __MAG_TOPIC = "/mag"

    # Limit on buffer size to prevent memory overflow
    __BUFFER_CAP = 60

    def __init__(self):
        self.node = ros2.create_node("imu_sub")

        qos_profile = QoSProfile(depth=1)
        qos_profile.history = QoSHistoryPolicy.KEEP_LAST
        qos_profile.reliability = QoSReliabilityPolicy.BEST_EFFORT
        qos_profile.durability = QoSDurabilityPolicy.VOLATILE

        # subscribe to the imu topic, which will call
        # __imu_callback every time the IMU publishes data
        self.__imu_sub = self.node.create_subscription(
            Imu, self.__IMU_TOPIC, self.__imu_callback, qos_profile
        )

        # subscribe to the mag topic, which will call
        # __mag_callback every time the IMU publishes data
        self.__mag_sub = self.node.create_subscription(
            MagneticField, self.__MAG_TOPIC, self.__mag_callback, qos_profile
        )

        self.__acceleration = np.array([0, 0, 0])
        self.__acceleration_buffer = deque()
        self.__angular_velocity = np.array([0, 0, 0])
        self.__angular_velocity_buffer = deque()
        self.__magnetic_field = np.array([0, 0, 0])
        self.__magnetic_field_buffer = deque()

    def __imu_callback(self, data):
        new_acceleration = np.array(
            [data.linear_acceleration.x, data.linear_acceleration.y, data.linear_acceleration.z]
        )

        self.__acceleration_buffer.append(new_acceleration)
        if len(self.__acceleration_buffer) > self.__BUFFER_CAP:
            self.__acceleration_buffer.popleft()

        new_angular_velocity = np.array(
            [data.angular_velocity.x, data.angular_velocity.y, data.angular_velocity.z]
        )

        self.__angular_velocity_buffer.append(new_angular_velocity)
        if len(self.__angular_velocity_buffer) > self.__BUFFER_CAP:
            self.__angular_velocity_buffer.popleft()

    def __mag_callback(self, data):
        new_magnetic_field = np.array(
            [data.magnetic_field.x, data.magnetic_field.y, data.magnetic_field.z]
        )

        self.__magnetic_field_buffer.append(new_magnetic_field)
        if len(self.__magnetic_field_buffer) > self.__BUFFER_CAP:
            self.__magnetic_field_buffer.popleft()
    
    def __update(self):
        if len(self.__acceleration_buffer) > 0:
            self.__acceleration = np.mean(self.__acceleration_buffer, axis=0)
            self.__acceleration_buffer.clear()

        if len(self.__angular_velocity_buffer) > 0:
            self.__angular_velocity = np.mean(self.__angular_velocity_buffer, axis=0)
            self.__angular_velocity_buffer.clear()

        if len(self.__magnetic_field_buffer) > 0:
            self.__magnetic_field = np.mean(self.__magnetic_field_buffer, axis=0)
            self.__magnetic_field_buffer.clear()

    def get_linear_acceleration(self) -> NDArray[3, np.float32]:
        return np.array(self.__acceleration)

    def get_angular_velocity(self) -> NDArray[3, np.float32]:
        return np.array(self.__angular_velocity)

    def get_magnetic_field(self) -> NDArray[3, np.float32]:
        return np.array(self.__magnetic_field)
