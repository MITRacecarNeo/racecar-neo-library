"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: slam_real.py
File Description: Contains the Slam module of the racecar_core library.
Subscribes to the driver's autonomy service: /autonomy/status (mode, map,
localized; latched, 1 Hz), /autonomy/pose (map pose, 20 Hz), and /map (the
occupancy grid; latched), and saves through the /autonomy/save_map service.
Only standard ROS messages are used, so it loads on a car without SLAM
installed and then reports mode "off".
"""

import threading
import time
from typing import Optional, Tuple

import numpy as np

from slam import OccupancyMap, Slam, heading_degrees

import rclpy as ros2
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from diagnostic_msgs.msg import DiagnosticStatus
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid
from std_srvs.srv import Trigger


class SlamReal(Slam):
    __STATUS_TOPIC = "/autonomy/status"
    __POSE_TOPIC = "/autonomy/pose"
    __MAP_TOPIC = "/map"
    __SAVE_SERVICE = "/autonomy/save_map"

    # The status arrives once a second; older than this, the service has stopped.
    __STATUS_TIMEOUT_S = 5.0

    def __init__(self):
        self.node = ros2.create_node("slam_sub")

        latched = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.__status_sub = self.node.create_subscription(
            DiagnosticStatus, self.__STATUS_TOPIC, self.__status_callback, latched
        )
        self.__pose_sub = self.node.create_subscription(
            PoseWithCovarianceStamped, self.__POSE_TOPIC, self.__pose_callback, 10
        )
        self.__map_sub = self.node.create_subscription(
            OccupancyGrid, self.__MAP_TOPIC, self.__map_callback, latched
        )
        self.__save_client = self.node.create_client(Trigger, self.__SAVE_SERVICE)

        self.__lock = threading.Lock()
        self.__status: dict = {}
        self.__status_time: Optional[float] = None
        self.__pose_new: Optional[Tuple[float, float, float]] = None
        self.__map: Optional[OccupancyMap] = None
        self.__save_status = ""

        # Latched once per frame by __update
        self.__mode = "off"
        self.__map_name = ""
        self.__localized = False
        self.__pose: Optional[Tuple[float, float, float]] = None

    def __status_callback(self, msg):
        values = {kv.key: kv.value for kv in msg.values}
        with self.__lock:
            self.__status = values
            self.__status_time = time.monotonic()

    def __pose_callback(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        pose = (p.x, p.y, heading_degrees(q.z, q.w))
        with self.__lock:
            self.__pose_new = pose

    def __map_callback(self, msg):
        info = msg.info
        data = np.asarray(msg.data, dtype=np.int8).reshape(info.height, info.width)
        grid = OccupancyMap(
            info.width,
            info.height,
            info.resolution,
            (info.origin.position.x, info.origin.position.y),
            data,
        )
        with self.__lock:
            self.__map = grid

    def __current(self) -> Tuple[str, str, bool]:
        """Mode, map name, and localized from the newest status; "off" once it is stale."""
        with self.__lock:
            values, at = dict(self.__status), self.__status_time
        mode = values.get("mode", "off")
        if at is None or time.monotonic() - at > self.__STATUS_TIMEOUT_S:
            mode = "off"
        if mode not in ("mapping", "localization"):
            return "off", "", False
        return mode, values.get("map", ""), values.get("localized") == "true"

    def __update(self):
        self.__mode, self.__map_name, self.__localized = self.__current()
        with self.__lock:
            self.__pose = self.__pose_new if self.__mode != "off" else None

    def get_mode(self) -> str:
        return self.__mode

    def get_map_name(self) -> str:
        return self.__map_name

    def is_localized(self) -> bool:
        return self.__localized

    def get_pose(self) -> Optional[Tuple[float, float, float]]:
        return self.__pose

    def get_pose_async(self) -> Optional[Tuple[float, float, float]]:
        if self.__current()[0] == "off":
            return None
        with self.__lock:
            return self.__pose_new

    def get_map(self) -> Optional[OccupancyMap]:
        if self.__current()[0] == "off":
            return None
        with self.__lock:
            return self.__map

    def save_map(self) -> None:
        if self.__save_status == "saving":
            return
        if self.__current()[0] != "mapping":
            self.__save_status = "failed: not mapping"
            return
        if not self.__save_client.service_is_ready():
            self.__save_status = "failed: the autonomy service is not answering"
            return
        self.__save_status = "saving"
        future = self.__save_client.call_async(Trigger.Request())
        future.add_done_callback(self.__save_done)

    def __save_done(self, future):
        try:
            result = future.result()
        except Exception as exc:  # the service went away mid-call
            self.__save_status = f"failed: {exc}"
            return
        self.__save_status = "saved" if result.success else f"failed: {result.message}"

    def get_save_status(self) -> str:
        return self.__save_status
