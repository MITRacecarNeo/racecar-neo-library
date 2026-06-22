"""
Copyright MIT
MIT License

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: nav_real.py
File Description: Contains the Nav module of the racecar_core library, backed by Nav2.
"""

from nav import Nav

# General
import math
import threading

# ROS2
from nav2_msgs.action import ComputePathToPose
import rclpy as ros2
from rclpy.action import ActionClient
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


def _normalize_angle(theta):
    while theta > math.pi:
        theta -= 2.0 * math.pi
    while theta < -math.pi:
        theta += 2.0 * math.pi
    return theta


class NavReal(Nav):
    __MAP_FRAME = "map"
    __BASE_FRAME = "base_footprint"
    __PLANNER_ID = "GridBased"

    # Ackermann pure-pursuit + arrival tuning (refine on the car).
    __WHEELBASE_M = 0.285
    __MAX_STEER_RAD = 0.5
    __LOOKAHEAD_M = 0.6
    __ARRIVE_M = 0.25
    __PLAN_TIMEOUT_S = 5.0

    def __init__(self):
        self.node = ros2.create_node("rc_nav")
        self.__planner = ActionClient(
            self.node, ComputePathToPose, "/compute_path_to_pose"
        )
        self.__tf_buffer = Buffer()
        self.__tf_listener = TransformListener(self.__tf_buffer, self.node)

        self.__pose = (0.0, 0.0, 0.0)
        self.__goal = None
        self.__goal_heading = None
        self.__path = []

        self.__plan_done = threading.Event()
        self.__plan_result = []

    def __update(self):
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

    # ── Goal state ──────────────────────────────────────────────

    def set_goal(self, x, y, heading=None):
        self.__goal = (float(x), float(y))
        self.__goal_heading = heading
        self.__path = []

    def get_goal(self):
        return self.__goal

    def get_goal_heading(self):
        return self.__goal_heading

    def clear_goal(self):
        self.__goal = None
        self.__goal_heading = None
        self.__path = []

    def invalidate(self):
        self.__path = []

    # ── Planning ────────────────────────────────────────────────

    def plan(self, goal_x=None, goal_y=None):
        if goal_x is not None and goal_y is not None:
            self.set_goal(goal_x, goal_y)
        if self.__goal is None:
            return []
        self.__path = self.__compute_path(self.__goal[0], self.__goal[1])
        return self.__path

    def plan_hybrid(self, goal_x=None, goal_y=None, goal_heading=None):
        if goal_x is not None and goal_y is not None:
            self.set_goal(goal_x, goal_y, goal_heading)
        pts = self.plan()
        out = []
        for i, (x, y) in enumerate(pts):
            if i + 1 < len(pts):
                theta = math.atan2(pts[i + 1][1] - y, pts[i + 1][0] - x)
            elif out:
                theta = out[-1][2]
            else:
                theta = self.__pose[2]
            out.append((x, y, theta, 1))
        return out

    def __compute_path(self, gx, gy):
        if not self.__planner.wait_for_server(timeout_sec=2.0):
            return []
        goal = ComputePathToPose.Goal()
        goal.goal.header.frame_id = self.__MAP_FRAME
        goal.goal.pose.position.x = gx
        goal.goal.pose.position.y = gy
        goal.goal.pose.orientation.w = 1.0
        goal.planner_id = self.__PLANNER_ID
        goal.use_start = False

        self.__plan_done.clear()
        self.__plan_result = []
        self.__planner.send_goal_async(goal).add_done_callback(self.__on_goal_response)
        self.__plan_done.wait(timeout=self.__PLAN_TIMEOUT_S)
        return self.__plan_result

    def __on_goal_response(self, future):
        handle = future.result()
        if handle is None or not handle.accepted:
            self.__plan_done.set()
            return
        handle.get_result_async().add_done_callback(self.__on_plan_result)

    def __on_plan_result(self, future):
        poses = future.result().result.path.poses
        self.__plan_result = [(p.pose.position.x, p.pose.position.y) for p in poses]
        self.__plan_done.set()

    # ── Following ───────────────────────────────────────────────

    def follow_goal(self, speed=0.5):
        return self.__follow(speed)

    def follow_hybrid_goal(self, speed=0.3):
        # Forward Nav2 paths only for now; reverse/switchback is a follow-up.
        return self.__follow(speed)

    def __follow(self, speed):
        if self.__goal is None:
            return (0.0, 0.0, "no_goal")
        if not self.__path:
            self.plan()
        if not self.__path:
            return (0.0, 0.0, "no_path")

        x, y, yaw = self.__pose
        gx, gy = self.__goal
        if math.hypot(gx - x, gy - y) <= self.__ARRIVE_M:
            return (0.0, 0.0, "arrived")

        lx, ly = self.__lookahead(x, y)
        alpha = _normalize_angle(math.atan2(ly - y, lx - x) - yaw)
        steer = math.atan2(2.0 * self.__WHEELBASE_M * math.sin(alpha), self.__LOOKAHEAD_M)
        steer_norm = max(-1.0, min(1.0, steer / self.__MAX_STEER_RAD))
        return (speed, steer_norm, "driving")

    def __lookahead(self, x, y):
        for px, py in self.__path:
            if math.hypot(px - x, py - y) >= self.__LOOKAHEAD_M:
                return (px, py)
        return self.__path[-1]
