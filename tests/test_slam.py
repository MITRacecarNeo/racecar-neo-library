"""rc.slam: OccupancyMap, headings, the simulator stub, and SlamReal against a test publisher."""

import math
import time

import numpy as np
import pytest

import racecar_utils
from slam import OccupancyMap, heading_degrees


def room_map():
    # 4 columns x 3 rows of 0.5 m, lower-left corner at (-1, -1); a wall along the bottom row.
    data = np.zeros((3, 4), dtype=np.int8)
    data[0, :] = 100
    data[2, 3] = -1
    return OccupancyMap(4, 3, 0.5, (-1.0, -1.0), data)


class TestOccupancyMap:
    def test_to_cell_counts_rows_up_from_the_bottom(self):
        m = room_map()
        assert m.to_cell(-1.0, -1.0) == (0, 0)
        assert m.to_cell(-0.75, 0.2) == (2, 0)
        assert m.to_cell(0.99, 0.49) == (2, 3)

    def test_to_cell_off_the_map(self):
        m = room_map()
        assert m.to_cell(-1.01, 0.0) is None
        assert m.to_cell(1.0, 0.0) is None  # the right edge belongs to no cell
        assert m.to_cell(0.0, 0.5) is None

    def test_to_point_is_the_cell_center(self):
        assert room_map().to_point(2, 3) == pytest.approx((0.75, 0.25))

    def test_round_trip(self):
        m = room_map()
        for row in range(3):
            for col in range(4):
                assert m.to_cell(*m.to_point(row, col)) == (row, col)

    def test_value_at(self):
        m = room_map()
        assert m.value_at(0.0, -0.9) == OccupancyMap.WALL
        assert m.value_at(0.0, -0.4) == OccupancyMap.FREE
        assert m.value_at(0.8, 0.3) == OccupancyMap.UNKNOWN
        assert m.value_at(5.0, 5.0) == OccupancyMap.UNKNOWN

    def test_repr(self):
        assert repr(room_map()) == "OccupancyMap(4 x 3 cells, 0.50 m, origin (-1.00, -1.00))"


@pytest.mark.parametrize(
    "yaw_deg, expected",
    [(0.0, 0.0), (90.0, 90.0), (-90.0, -90.0), (179.0, 179.0), (180.0, -180.0), (270.0, -90.0)],
)
def test_heading_degrees(yaw_deg, expected):
    half = math.radians(yaw_deg) / 2
    assert heading_degrees(math.sin(half), math.cos(half)) == pytest.approx(expected)


def test_sim_stub_reports_off_and_warns_once(monkeypatch):
    from slam_sim import SlamSim

    warnings = []
    monkeypatch.setattr(racecar_utils, "print_warning", warnings.append)
    s = SlamSim()
    assert s.get_mode() == "off"
    assert s.get_map_name() == ""
    assert s.is_localized() is False
    assert s.get_pose() is None and s.get_pose_async() is None
    assert s.get_map() is None
    s.save_map()
    assert s.get_save_status().startswith("failed")
    assert len(warnings) == 1


# -- SlamReal against a test publisher (needs ROS 2) --

rclpy = pytest.importorskip("rclpy")


@pytest.fixture
def ros(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "93")  # away from a running car
    rclpy.init()
    from rclpy.executors import SingleThreadedExecutor

    executor = SingleThreadedExecutor()
    yield executor
    executor.shutdown()
    rclpy.try_shutdown()


def spin_until(executor, done, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not done() and time.monotonic() < deadline:
        executor.spin_once(timeout_sec=0.05)
    return done()


class FakeAutonomy:
    """Publishes /autonomy/status, /autonomy/pose and /map, and serves /autonomy/save_map."""

    def __init__(self, executor, save_ok=True):
        from diagnostic_msgs.msg import DiagnosticStatus, KeyValue
        from geometry_msgs.msg import PoseWithCovarianceStamped
        from nav_msgs.msg import OccupancyGrid
        from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
        from std_srvs.srv import Trigger

        self.node = rclpy.create_node("fake_autonomy")
        executor.add_node(self.node)
        latched = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._kv, self._status_cls = KeyValue, DiagnosticStatus
        self.status_pub = self.node.create_publisher(DiagnosticStatus, "/autonomy/status", latched)
        self.pose_pub = self.node.create_publisher(PoseWithCovarianceStamped, "/autonomy/pose", 10)
        self.map_pub = self.node.create_publisher(OccupancyGrid, "/map", latched)
        self._pose_cls, self._grid_cls = PoseWithCovarianceStamped, OccupancyGrid
        self.saves = 0

        def on_save(_, response):
            self.saves += 1
            response.success, response.message = save_ok, "" if save_ok else "disk full"
            return response

        self.node.create_service(Trigger, "/autonomy/save_map", on_save)

    def status(self, **values):
        msg = self._status_cls(values=[self._kv(key=k, value=v) for k, v in values.items()])
        self.status_pub.publish(msg)

    def pose(self, x, y, yaw_deg):
        msg = self._pose_cls()
        msg.pose.pose.position.x, msg.pose.pose.position.y = x, y
        msg.pose.pose.orientation.z = math.sin(math.radians(yaw_deg) / 2)
        msg.pose.pose.orientation.w = math.cos(math.radians(yaw_deg) / 2)
        self.pose_pub.publish(msg)

    def grid(self):
        msg = self._grid_cls()
        msg.info.width, msg.info.height, msg.info.resolution = 2, 3, 0.05
        msg.info.origin.position.x, msg.info.origin.position.y = 1.0, 2.0
        msg.data = [100, 100, 0, 0, -1, 0]
        self.map_pub.publish(msg)


@pytest.fixture
def slam(ros):
    from slam_real import SlamReal

    s = SlamReal()
    ros.add_node(s.node)
    return s


def update(s):
    s._SlamReal__update()


def test_off_before_any_status(ros, slam):
    spin_until(ros, lambda: False, timeout=0.3)
    update(slam)
    assert slam.get_mode() == "off" and slam.get_map_name() == ""
    assert slam.get_pose() is None and slam.get_map() is None
    assert slam.is_localized() is False


def test_localization_pose_and_map(ros, slam):
    fake = FakeAutonomy(ros)
    fake.status(mode="localization", map="room", localized="true")
    fake.grid()
    assert spin_until(
        ros,
        lambda: slam.get_map() is not None and slam._SlamReal__current()[0] == "localization",
    )
    pose = None
    for _ in range(20):  # the pose topic is volatile: publish until one arrives
        fake.pose(1.5, -0.5, 120.0)
        spin_until(ros, lambda: False, timeout=0.05)
        update(slam)
        pose = slam.get_pose()
        if pose is not None:
            break
    assert slam.get_map_name() == "room" and slam.is_localized() is True
    x, y, heading = pose
    assert (x, y) == pytest.approx((1.5, -0.5)) and heading == pytest.approx(120.0)
    m = slam.get_map()
    assert (m.width, m.height, m.origin) == (2, 3, (1.0, 2.0))
    assert m.data[0].tolist() == [100, 100]  # first grid row is the bottom row
    assert m.value_at(1.03, 2.13) == -1


def test_mode_off_after_stop_or_silence(ros, slam, monkeypatch):
    fake = FakeAutonomy(ros)
    fake.status(mode="localization", map="room", localized="true")
    assert spin_until(ros, lambda: (update(slam), slam.get_mode())[1] == "localization")
    fake.status(mode="off", map="room", localized="false")
    assert spin_until(ros, lambda: (update(slam), slam.get_mode())[1] == "off")
    fake.status(mode="mapping", map="hall", localized="true")
    assert spin_until(ros, lambda: (update(slam), slam.get_mode())[1] == "mapping")
    monkeypatch.setattr(type(slam), "_SlamReal__STATUS_TIMEOUT_S", 0.0)
    update(slam)
    assert slam.get_mode() == "off" and slam.get_pose() is None


@pytest.mark.parametrize("save_ok, expected", [(True, "saved"), (False, "failed: disk full")])
def test_save_while_mapping(ros, slam, save_ok, expected):
    fake = FakeAutonomy(ros, save_ok=save_ok)
    fake.status(mode="mapping", map="hall", localized="true")
    assert spin_until(ros, lambda: slam._SlamReal__current()[0] == "mapping")
    assert spin_until(ros, lambda: slam._SlamReal__save_client.service_is_ready())
    slam.save_map()
    assert slam.get_save_status() == "saving"
    assert spin_until(ros, lambda: slam.get_save_status() != "saving")
    assert slam.get_save_status() == expected and fake.saves == 1


def test_save_refused_unless_mapping(ros, slam):
    fake = FakeAutonomy(ros)
    fake.status(mode="localization", map="room", localized="true")
    assert spin_until(ros, lambda: slam._SlamReal__current()[0] == "localization")
    slam.save_map()
    assert slam.get_save_status() == "failed: not mapping" and fake.saves == 0
