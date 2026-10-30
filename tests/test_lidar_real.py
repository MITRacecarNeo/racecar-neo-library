"""LidarReal: sample j looks j * 360 / n degrees clockwise from the nose, given the lidar's mount."""

import math

import numpy as np
import pytest

rclpy = pytest.importorskip("rclpy")

# The car's /scan: 1080 rays from -180 to +180 degrees, both ends on the same ray.
N = 1080
ANGLE_MIN = -math.pi
INC = 2 * math.pi / (N - 1)


@pytest.fixture
def lidar(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "94")  # away from a running car
    rclpy.init()
    import lidar_real

    yield lidar_real.LidarReal()
    rclpy.try_shutdown()


def scan(ranges):
    from sensor_msgs.msg import LaserScan

    msg = LaserScan(angle_min=ANGLE_MIN, angle_increment=INC, range_min=0.05, range_max=12.0)
    msg.ranges = [float(r) for r in ranges]
    return msg


def raw_index(raw_deg):
    """The ray at raw angle `raw_deg`, read in (-180, 180] like LidarReal."""
    raw = math.radians(180.0 - (180.0 - raw_deg) % 360.0)
    return round((raw - ANGLE_MIN) / INC) % N


def feed(lidar, ranges):
    lidar._LidarReal__scan_callback(scan(ranges))
    return lidar.get_samples_async()


def mount(lidar, yaw_deg, parent="base_link", child="laser"):
    from geometry_msgs.msg import TransformStamped
    from tf2_msgs.msg import TFMessage

    t = TransformStamped()
    t.header.frame_id, t.child_frame_id = parent, child
    t.transform.rotation.z = math.sin(math.radians(yaw_deg) / 2)
    t.transform.rotation.w = math.cos(math.radians(yaw_deg) / 2)
    lidar._LidarReal__tf_callback(TFMessage(transforms=[t]))


def test_keeps_the_old_order_on_an_aft_mount(lidar):
    # The library used to reverse the scan; with the lidar at 180 degrees that
    # is the same order, give or take the one ray the two ends share.
    ranges = np.linspace(1.0, 5.0, N)
    old = np.flip(ranges * 100)
    new = feed(lidar, ranges)
    assert len(new) == N
    assert np.max(np.abs(new - old)) <= 2 * (400.0 / (N - 1)) + 1e-6


def test_the_car_s_right_is_a_quarter_turn_in(lidar):
    # Measured on hardware: an object off the car's right sits at raw +90.
    ranges = np.full(N, 5.0)
    ranges[raw_index(90.0)] = 1.0
    samples = feed(lidar, ranges)
    assert samples[N // 4] == pytest.approx(100.0)
    assert samples[3 * N // 4] == pytest.approx(500.0)


def test_a_calibrated_yaw_turns_the_samples(lidar):
    # Turned 0.381 degrees short of aft, the lidar sees the nose at raw 180.381.
    mount(lidar, 179.619)
    ranges = np.full(N, 5.0)
    ranges[raw_index(180.381)] = 1.0
    assert feed(lidar, ranges)[0] == pytest.approx(100.0)


def test_other_transforms_are_ignored(lidar):
    mount(lidar, 0.0, parent="odom", child="base_link")
    ranges = np.full(N, 5.0)
    ranges[raw_index(180.0)] = 1.0
    assert feed(lidar, ranges)[0] == pytest.approx(100.0)


def test_no_return_reads_zero(lidar):
    ranges = np.full(N, 2.0)
    ranges[raw_index(180.0)] = float("inf")
    ranges[raw_index(90.0)] = float("nan")
    samples = feed(lidar, ranges)
    assert samples[0] == 0 and samples[N // 4] == 0
    assert np.isfinite(samples).all()
