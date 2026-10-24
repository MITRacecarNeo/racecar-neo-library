"""CameraReal subscribes on request and decodes on read; PhysicsReal reads the battery means."""

import threading
import time

import numpy as np
import pytest

rclpy = pytest.importorskip("rclpy")


@pytest.fixture
def ros(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "94")  # away from a running car
    rclpy.init()
    from rclpy.executors import SingleThreadedExecutor

    executor = SingleThreadedExecutor()
    thread = threading.Thread(target=executor.spin, daemon=True)
    yield executor, thread
    executor.shutdown()
    rclpy.try_shutdown()


def wait(done, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not done() and time.monotonic() < deadline:
        time.sleep(0.02)
    return done()


def image_msg():
    from sensor_msgs.msg import Image

    msg = Image(height=2, width=3, encoding="bgr8", step=9)
    msg.data = bytes(range(18))
    return msg


def test_camera_subscribes_on_the_first_read(ros):
    executor, thread = ros
    from camera_real import CameraReal

    cam = CameraReal()
    executor.add_node(cam.node)
    pub_node = rclpy.create_node("fake_camera")
    executor.add_node(pub_node)
    from sensor_msgs.msg import Image

    pub = pub_node.create_publisher(Image, "/camera/color", 10)
    thread.start()
    assert cam.node.get_subscriptions_info_by_topic("/camera/color") == []

    stop = threading.Event()

    def publish():
        while not stop.is_set():
            pub.publish(image_msg())
            time.sleep(0.02)

    threading.Thread(target=publish, daemon=True).start()
    try:
        image = cam.get_color_image_async()
        assert image is not None and image.shape == (2, 3, 3)
        assert image[1, 2].tolist() == [15, 16, 17]
        assert cam.get_color_image_async() is not None
    finally:
        stop.set()


def test_camera_without_frames_returns_none(ros):
    executor, thread = ros
    from camera_real import CameraReal

    cam = CameraReal()
    executor.add_node(cam.node)
    thread.start()
    start = time.monotonic()
    assert cam.get_depth_image_async() is None
    assert time.monotonic() - start < 2.0


def test_battery_comes_from_the_state_means(ros):
    executor, thread = ros
    from physics_real import PhysicsReal
    from sensor_msgs.msg import BatteryState

    physics = PhysicsReal()
    executor.add_node(physics.node)
    pub_node = rclpy.create_node("fake_pit")
    executor.add_node(pub_node)
    pub = pub_node.create_publisher(BatteryState, "/battery/state", 10)
    thread.start()
    assert wait(lambda: pub.get_subscription_count() > 0)
    pub.publish(BatteryState(voltage=8.1, current=-2.5))
    assert wait(lambda: physics.get_battery_voltage() > 0)
    assert physics.get_battery_voltage() == pytest.approx(8.1)
    assert physics.get_battery_current() == pytest.approx(2.5)
    assert np.isfinite(physics.get_battery_current())
