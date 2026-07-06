"""
Nav module backed by Nav2. set_goal() hands the goal to Nav2's NavigateToPose
(its planner + Regulated Pure Pursuit controller + recoveries do the real navigation);
follow_goal() relays Nav2's /cmd_vel as (speed, angle) for rc.drive.

Execution model note (racecar_core):
  - rc.go() spins the shared rclpy executor in the MAIN thread.
  - A separate 60fps thread calls __update() every frame.
  Therefore __update() MUST be non-blocking: it never waits for a server or
  spins the executor. send_goal_async() is safe to call from the update thread
  (it only queues; the main-thread executor processes the discovery and fires
  the done callbacks). server_is_ready() is a cheap cached check.
"""
from nav import Nav
import math
import rclpy as ros2
from rclpy.action import ActionClient
from rclpy.time import Time
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import Empty
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from tf2_ros import Buffer, TransformListener

class NavReal(Nav):
    __MAP_FRAME = "map"
    __BASE_FRAME = "base_footprint"
    __PLANNER_ID = "GridBased"
    __WHEELBASE_M = 0.285
    __MAX_STEER_RAD = 0.50
    __REF_SPEED_MPS = 0.50
    __CMD_TIMEOUT_S = 0.5

    def __init__(self):
        self.node = ros2.create_node("rc_nav")
        self.__nav = ActionClient(self.node, NavigateToPose, "/navigate_to_pose")
        self.__planner = ActionClient(self.node, ComputePathToPose, "/compute_path_to_pose")
        self.__tf_buffer = Buffer()
        self.__tf_listener = TransformListener(self.__tf_buffer, self.node)
        self.node.create_subscription(Twist, "/cmd_vel", self.__cmd_cb, 10)
        # Web-UI goal pipeline: a Goal click in the browser publishes PoseStamped
        # on /web_goal; we adopt it as OUR goal (this class stays the single Nav2
        # goal owner), so a running lab drives goals clicked on the map. The web
        # Stop button publishes /web_goal_cancel.
        self.node.create_subscription(PoseStamped, "/web_goal", self.__web_goal_cb, 10)
        self.node.create_subscription(Empty, "/web_goal_cancel", lambda _m: self.clear_goal(), 10)
        self.__pose = (0.0, 0.0, 0.0)
        self.__goal = None
        self.__goal_heading = None
        self.__path = []
        self.__last_cmd = (0.0, 0.0)
        self.__last_cmd_t = None
        self.__goal_handle = None
        # __pending: True when a goal is set but has not yet been accepted by an
        # available Nav2 server. __update() retries send while this is True.
        self.__pending = False
        self.__status = "no_goal"
        # __epoch: monotonically increments on every set_goal()/clear_goal(). Each
        # async send captures the epoch it was armed under; goal/result callbacks
        # (which fire on the MAIN executor thread) drop their write to shared
        # status if the epoch has moved on. This guards against a stale,
        # superseded goal's result callback clobbering the live goal's status
        # (e.g. an old goal's ABORT/SUCCEED arriving after a newer set_goal has
        # already reached 'driving').
        self.__epoch = 0

    def __cmd_cb(self, msg):
        self.__last_cmd = (msg.linear.x, msg.angular.z)
        self.__last_cmd_t = self.node.get_clock().now()

    def __update(self):
        # Pose update (non-blocking TF lookup).
        if self.__tf_buffer.can_transform(self.__MAP_FRAME, self.__BASE_FRAME, Time()):
            t = self.__tf_buffer.lookup_transform(self.__MAP_FRAME, self.__BASE_FRAME, Time()).transform
            q = t.rotation
            yaw = math.atan2(2.0*(q.w*q.z + q.x*q.y), 1.0 - 2.0*(q.y*q.y + q.z*q.z))
            self.__pose = (t.translation.x, t.translation.y, yaw)

        # Robust, non-blocking goal arming. If a goal is pending and the Nav2
        # action server has become ready (cheap cached check; the main-thread
        # executor does the discovery), send it. This retries every frame until
        # bt_navigator comes up, so a slow Nav2 startup no longer wedges us in a
        # permanent 'no_server'/'waiting' state.
        if self.__pending and self.__goal is not None and self.__nav.server_is_ready():
            self.__arm_nav_goal()

    def __web_goal_cb(self, msg):
        # Fires on the MAIN executor thread; set_goal only mutates attributes and
        # queues a cancel, and the 60fps thread does the arming, so this is safe.
        q = msg.pose.orientation
        yaw = math.atan2(2.0*(q.w*q.z + q.x*q.y), 1.0 - 2.0*(q.y*q.y + q.z*q.z))
        self.set_goal(msg.pose.position.x, msg.pose.position.y, yaw)

    def set_goal(self, x, y, heading=None):
        # Non-blocking: just record the goal and mark it pending. __update() will
        # send it as soon as the Nav2 server is ready, retrying every frame.
        # Cancel any previously-armed Nav2 goal and bump the epoch so a late
        # callback from the old goal cannot clobber the new goal's status.
        self.cancel()
        self.__epoch += 1
        self.__goal = (float(x), float(y))
        self.__goal_heading = heading
        self.__path = []
        self.__goal_handle = None
        self.__pending = True
        self.__status = "waiting"

    def get_goal(self): return self.__goal
    def get_goal_heading(self): return self.__goal_heading

    def clear_goal(self):
        self.cancel()
        self.__epoch += 1
        self.__goal = None
        self.__goal_heading = None
        self.__path = []
        self.__pending = False
        self.__status = "no_goal"

    def invalidate(self): self.__path = []

    def __arm_nav_goal(self):
        # Called from __update() only when self.__nav.server_is_ready() is True,
        # so no blocking wait is needed here. Clear the pending flag BEFORE the
        # async send so a single goal is armed exactly once even though
        # __update() runs every frame.
        if self.__goal is None:
            self.__pending = False
            return
        self.__pending = False
        epoch = self.__epoch
        g = NavigateToPose.Goal()
        g.pose.header.frame_id = self.__MAP_FRAME
        g.pose.header.stamp = self.node.get_clock().now().to_msg()
        g.pose.pose.position.x = self.__goal[0]
        g.pose.pose.position.y = self.__goal[1]
        h = self.__goal_heading if self.__goal_heading is not None else 0.0
        g.pose.pose.orientation.z = math.sin(h/2.0)
        g.pose.pose.orientation.w = math.cos(h/2.0)
        # Stay 'waiting' until the server accepts the goal (callback flips to
        # 'driving') or rejects it ('no_path').
        self.__status = "waiting"
        self.__nav.send_goal_async(g).add_done_callback(
            lambda fut: self.__on_goal(fut, epoch))

    def __on_goal(self, future, epoch):
        # Fires on the MAIN executor thread. Ignore stale callbacks from a goal
        # that has since been superseded by a newer set_goal()/clear_goal().
        if epoch != self.__epoch:
            return
        try:
            handle = future.result()
        except Exception:
            # send_goal future raised (e.g. server vanished mid-send). Re-arm so
            # __update() retries rather than leaving us stuck in 'waiting'.
            self.__goal_handle = None
            self.__pending = True
            self.__status = "waiting"
            return
        self.__goal_handle = handle
        if handle is None or not handle.accepted:
            self.__status = "no_path"
            return
        self.__status = "driving"
        handle.get_result_async().add_done_callback(
            lambda fut: self.__on_result(fut, epoch))

    def __on_result(self, future, epoch):
        # Fires on the MAIN executor thread. Ignore results from a superseded
        # goal so an old goal's terminal status cannot clobber the live goal.
        if epoch != self.__epoch:
            return
        try:
            status = future.result().status
        except Exception:
            self.__status = "no_path"
            return
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.__status = "arrived"
        elif status == GoalStatus.STATUS_CANCELED:
            # Cleared mid-flight; if the goal is gone, reflect that.
            if self.__goal is None:
                self.__status = "no_goal"
        else:
            # ABORTED or any non-success terminal state: Nav2 gave up after
            # recoveries. Surface it rather than falsely reporting 'arrived'.
            self.__status = "no_path"

    def cancel(self):
        if self.__goal_handle is not None:
            self.__goal_handle.cancel_goal_async()
            self.__goal_handle = None

    def plan(self, goal_x=None, goal_y=None):
        if goal_x is not None and goal_y is not None: self.set_goal(goal_x, goal_y)
        if self.__goal is None: return []
        self.__path = self.__compute_path(self.__goal[0], self.__goal[1]); return self.__path

    def plan_hybrid(self, goal_x=None, goal_y=None, goal_heading=None):
        if goal_x is not None and goal_y is not None: self.set_goal(goal_x, goal_y, goal_heading)
        pts = self.plan(); out = []
        for i, (x, y) in enumerate(pts):
            if i + 1 < len(pts): theta = math.atan2(pts[i+1][1]-y, pts[i+1][0]-x)
            elif out: theta = out[-1][2]
            else: theta = self.__pose[2]
            out.append((x, y, theta, 1))
        return out

    def __compute_path(self, gx, gy):
        # plan() is called deliberately by students, so a SHORT blocking wait is
        # acceptable here (this path is never on the 60fps frame loop). Tolerate
        # the planner server being absent by returning an empty path.
        import threading
        if not self.__planner.wait_for_server(timeout_sec=2.0): return []
        goal = ComputePathToPose.Goal()
        goal.goal.header.frame_id = self.__MAP_FRAME
        goal.goal.pose.position.x = gx; goal.goal.pose.position.y = gy; goal.goal.pose.orientation.w = 1.0
        goal.planner_id = self.__PLANNER_ID; goal.use_start = False
        ev = threading.Event(); box = {}
        def on_res(f): box["r"] = f.result(); ev.set()
        def on_goal(f):
            h = f.result()
            if h is None or not h.accepted: ev.set(); return
            h.get_result_async().add_done_callback(on_res)
        self.__planner.send_goal_async(goal).add_done_callback(on_goal)
        ev.wait(timeout=5.0); r = box.get("r")
        if not r: return []
        return [(p.pose.position.x, p.pose.position.y) for p in r.result.path.poses]

    def follow_goal(self, speed=0.5):
        # Read status once into a local so a callback flipping it mid-method
        # cannot produce an inconsistent decision (status is an immutable str,
        # so this single read is atomic and hazard-free).
        status = self.__status
        if self.__goal is None: return (0.0, 0.0, "no_goal")
        if status != "driving":
            # Covers 'waiting', 'no_path', 'arrived', and any non-driving state.
            return (0.0, 0.0, status)
        v, w = 0.0, 0.0
        if self.__last_cmd_t is not None:
            age = (self.node.get_clock().now() - self.__last_cmd_t).nanoseconds * 1e-9
            if age <= self.__CMD_TIMEOUT_S: v, w = self.__last_cmd
        if abs(v) < 0.02 and abs(w) > 0.10:
            # Nav2 commanded rotate-in-place (e.g. RPP rotate-to-heading), which an
            # Ackermann car cannot do. Substitute a slow forward arc with the same
            # yaw direction so the heading still converges instead of deadlocking.
            v = 0.15
        sp = max(-1.0, min(1.0, v / self.__REF_SPEED_MPS))
        steer = 0.0 if abs(v) < 1e-3 else math.atan(self.__WHEELBASE_M * w / v)
        # NEGATED: ROS +steer = left, racecar angle +1 = right. Verified on
        # hardware 2026-07-02 (Nav2 w=+0.70 left came out steering_angle=-0.76 right).
        ang = max(-1.0, min(1.0, -steer / self.__MAX_STEER_RAD))
        return (sp, ang, "driving")

    def follow_hybrid_goal(self, speed=0.3): return self.follow_goal(speed)
