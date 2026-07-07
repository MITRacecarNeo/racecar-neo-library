"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: physics_real.py
File Description: Contains the Physics module of the racecar_core library
"""

from physics import Physics

# General
from collections import deque
import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

# ROS2
import rclpy as ros2
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSReliabilityPolicy,
    QoSProfile,
)
from sensor_msgs.msg import Imu, MagneticField
from std_msgs.msg import Float32, Float32MultiArray


class PhysicsReal(Physics):
    # The ROS topic from which we read imu data. imu_fusion_node merges the
    # RealSense and Teensy LSM9DS1 IMUs into /imu/fused (single source of truth
    # when only one publishes). /mag has no source yet (the D435i has no
    # magnetometer); it stays empty until the Teensy LSM9DS1.
    __IMU_TOPIC = "/imu/fused"
    __MAG_TOPIC = "/mag"
    # Vehicle speed (m/s) republished by pit_node from the Teensy encoder.
    __ENCODER_TOPIC = "/encoder/speed"
    # Power telemetry (INA226) and the eight FlySky RC channels, republished by
    # pit_node: voltage in V, current in A, RC channels normalized to [-1, 1].
    __VOLTAGE_TOPIC = "/battery/voltage"
    __CURRENT_TOPIC = "/battery/current"
    __RC_TOPIC = "/rc/channels"

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

        # subscribe to the encoder speed topic (m/s)
        self.__encoder_sub = self.node.create_subscription(
            Float32, self.__ENCODER_TOPIC, self.__encoder_callback, qos_profile
        )

        # subscribe to the power telemetry (V, A) and RC channel topics
        self.__voltage_sub = self.node.create_subscription(
            Float32, self.__VOLTAGE_TOPIC, self.__voltage_callback, qos_profile
        )
        self.__current_sub = self.node.create_subscription(
            Float32, self.__CURRENT_TOPIC, self.__current_callback, qos_profile
        )
        self.__rc_sub = self.node.create_subscription(
            Float32MultiArray, self.__RC_TOPIC, self.__rc_callback, qos_profile
        )

        self.__acceleration = np.array([0, 0, 0])
        self.__acceleration_buffer = deque()
        self.__angular_velocity = np.array([0, 0, 0])
        self.__angular_velocity_buffer = deque()
        self.__magnetic_field = np.array([0, 0, 0])
        self.__magnetic_field_buffer = deque()
        self.__encoder_speed = 0.0
        self.__encoder_speed_buffer = deque()
        self.__voltage = 0.0
        self.__voltage_buffer = deque()
        self.__current = 0.0
        self.__current_buffer = deque()
        self.__rc_channels = np.zeros(8)

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

    def __encoder_callback(self, data):
        self.__encoder_speed_buffer.append(data.data)
        if len(self.__encoder_speed_buffer) > self.__BUFFER_CAP:
            self.__encoder_speed_buffer.popleft()

    def __voltage_callback(self, data):
        self.__voltage_buffer.append(data.data)
        if len(self.__voltage_buffer) > self.__BUFFER_CAP:
            self.__voltage_buffer.popleft()

    def __current_callback(self, data):
        self.__current_buffer.append(data.data)
        if len(self.__current_buffer) > self.__BUFFER_CAP:
            self.__current_buffer.popleft()

    def __rc_callback(self, data):
        # RC channels are control inputs; keep the most recent frame, not an
        # average. Pad or truncate to eight in case a frame is malformed.
        values = list(data.data)[:8]
        values += [0.0] * (8 - len(values))
        self.__rc_channels = np.array(values)

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

        if len(self.__encoder_speed_buffer) > 0:
            self.__encoder_speed = float(np.mean(self.__encoder_speed_buffer))
            self.__encoder_speed_buffer.clear()

        if len(self.__voltage_buffer) > 0:
            self.__voltage = float(np.mean(self.__voltage_buffer))
            self.__voltage_buffer.clear()

        if len(self.__current_buffer) > 0:
            self.__current = float(np.mean(self.__current_buffer))
            self.__current_buffer.clear()

    def get_linear_acceleration(self) -> NDArray[3, np.float32]:
        return np.array(self.__acceleration)

    def get_angular_velocity(self) -> NDArray[3, np.float32]:
        return np.array(self.__angular_velocity)

    def get_magnetic_field(self) -> NDArray[3, np.float32]:
        return np.array(self.__magnetic_field)

    def get_encoder_speed(self) -> float:
        return self.__encoder_speed

    def get_battery_voltage(self) -> float:
        return self.__voltage

    def get_battery_current(self) -> float:
        return self.__current

    def get_rc_channels(self) -> NDArray[8, np.float32]:
        return np.array(self.__rc_channels)
