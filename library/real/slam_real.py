"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: slam_real.py
File Description: Contains the Slam module of the racecar_core library, backed by slam_toolbox.
"""

from slam import Slam

# General
import math
import os
from typing import List, Tuple

import numpy as np

# ROS2
from nav_msgs.msg import OccupancyGrid
import rclpy as ros2
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from slam_toolbox.srv import Clear, DeserializePoseGraph, SerializePoseGraph
from tf2_ros import Buffer, TransformListener


class SlamReal(Slam):
    # Topics and frames published by the slam.launch.py bringup.
    __MAP_TOPIC = "/map"
    __MAP_FRAME = "map"
    __BASE_FRAME = "base_footprint"

    # Saved pose-graphs live here (matches the simulator's maps directory).
    __MAPS_DIR = os.path.expanduser("~/.neoracer/maps")

    # Student-facing map contract (matches the simulator): 160 x 160 @ 0.25 m.
    __GRID_W = 160
    __GRID_H = 160
    __CELL_M = 0.25

    def __init__(self):
        # ROS node
        self.node = ros2.create_node("rc_slam")

        # /map is latched (TRANSIENT_LOCAL) and reliable from slam_toolbox.
        map_qos = QoSProfile(depth=1)
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        self.__map_sub = self.node.create_subscription(
            OccupancyGrid, self.__MAP_TOPIC, self.__map_callback, map_qos
        )
        self.__map_msg = None

        # map -> base_footprint pose is read from the TF tree.
        self.__tf_buffer = Buffer()
        self.__tf_listener = TransformListener(self.__tf_buffer, self.node)
        self.__pose = (0.0, 0.0, 0.0)

        # slam_toolbox save / load / clear service clients.
        self.__serialize = self.node.create_client(
            SerializePoseGraph, "/slam_toolbox/serialize_map"
        )
        self.__deserialize = self.node.create_client(
            DeserializePoseGraph, "/slam_toolbox/deserialize_map"
        )
        self.__clear = self.node.create_client(Clear, "/slam_toolbox/clear_changes")

    def __map_callback(self, msg):
        self.__map_msg = msg

    def __update(self):
        # Refresh the cached pose from the latest TF every frame.
        if self.__tf_buffer.can_transform(self.__MAP_FRAME, self.__BASE_FRAME, Time()):
            t = self.__tf_buffer.lookup_transform(
                self.__MAP_FRAME, self.__BASE_FRAME, Time()
            ).transform
            q = t.rotation
            yaw = math.atan2(
                2.0 * (q.w * q.z + q.x * q.y),
                1.0 - 2.0 * (q.y * q.y + q.z * q.z),
            )
            self.__pose = (t.translation.x, t.translation.y, yaw)

    # ── Slam interface ──────────────────────────────────────────

    def update(self, scan) -> Tuple[float, float, float]:
        # slam_toolbox ingests /scan directly; scan is accepted for sim parity.
        return self.__pose

    def get_pose(self) -> Tuple[float, float, float]:
        return self.__pose

    def get_map(self) -> Tuple[int, int, float, List[int]]:
        if self.__map_msg is None:
            return (
                self.__GRID_W,
                self.__GRID_H,
                self.__CELL_M,
                [-1] * (self.__GRID_W * self.__GRID_H),
            )
        return self.__resample(self.__map_msg)

    def reset(self) -> None:
        # slam_toolbox has no live full-map reset: clear interactive changes and
        # drop the cached map. A fresh map requires relaunching slam.launch.py.
        self.__map_msg = None
        if self.__clear.service_is_ready():
            self.__clear.call_async(Clear.Request())

    def save_map(self, name: str) -> None:
        os.makedirs(self.__MAPS_DIR, exist_ok=True)
        request = SerializePoseGraph.Request()
        request.filename = os.path.join(self.__MAPS_DIR, name)
        self.__serialize.call_async(request)
        # also emit occupancy .pgm/.yaml to ~/maps so nav/student.sh can load this map
        import subprocess as _sp
        _m=os.path.expanduser('~/maps'); os.makedirs(_m, exist_ok=True)
        _sp.Popen(['ros2','run','nav2_map_server','map_saver_cli','-f',os.path.join(_m,name),'--ros-args','-p','save_map_timeout:=20.0'], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)

    def load_map(self, name: str) -> bool:
        path = os.path.join(self.__MAPS_DIR, name)
        if not os.path.exists(path + ".posegraph"):
            return False
        request = DeserializePoseGraph.Request()
        request.filename = path
        request.match_type = DeserializePoseGraph.Request.START_AT_FIRST_NODE
        self.__deserialize.call_async(request)
        return True

    # ── Internals ───────────────────────────────────────────────

    def __resample(self, m) -> Tuple[int, int, float, List[int]]:
        # Downsample the fine slam_toolbox grid onto the 160 x 160 @ 0.25 m
        # student contract, centered on the explored map. A target cell is
        # occupied if any covered source cell is, else free if any is known,
        # else unknown.
        res = m.info.resolution
        width, height = m.info.width, m.info.height
        src = np.array(m.data, dtype=np.int16).reshape(height, width)
        ratio = int(round(self.__CELL_M / res))
        sub_w = self.__GRID_W * ratio
        sub_h = self.__GRID_H * ratio

        map_cx = m.info.origin.position.x + width * res / 2.0
        map_cy = m.info.origin.position.y + height * res / 2.0
        win_ox = map_cx - self.__GRID_W * self.__CELL_M / 2.0
        win_oy = map_cy - self.__GRID_H * self.__CELL_M / 2.0
        sx0 = int(round((win_ox - m.info.origin.position.x) / res))
        sy0 = int(round((win_oy - m.info.origin.position.y) / res))

        region = np.full((sub_h, sub_w), -1, dtype=np.int16)
        src_x0, src_y0 = max(0, sx0), max(0, sy0)
        src_x1, src_y1 = min(width, sx0 + sub_w), min(height, sy0 + sub_h)
        if src_x1 > src_x0 and src_y1 > src_y0:
            dx, dy = src_x0 - sx0, src_y0 - sy0
            region[dy:dy + (src_y1 - src_y0), dx:dx + (src_x1 - src_x0)] = (
                src[src_y0:src_y1, src_x0:src_x1]
            )

        blocks = region.reshape(self.__GRID_H, ratio, self.__GRID_W, ratio)
        occupied = (blocks >= 50).any(axis=(1, 3))
        known = (blocks >= 0).any(axis=(1, 3))
        out = np.where(occupied, 100, np.where(known, 0, -1)).astype(np.int16)
        return (self.__GRID_W, self.__GRID_H, self.__CELL_M, out.flatten().tolist())
