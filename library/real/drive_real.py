"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: drive_real.py
File Description: Contains the Drive module of the racecar_core library
"""

from drive import Drive

import rclpy as ros2
from ackermann_msgs.msg import AckermannDriveStamped


class DriveReal(Drive):
    # The ROS topic to which we publish drive messages
    __TOPIC = "/drive"

    # ROS frame ID stamped on every published drive message
    __FRAME_ID = "base_link"

    # Continuous republish at 20 Hz keeps mux_node's command_timeout_sec (0.5 s)
    # satisfied with headroom. Driven by a node-side timer rather than
    # racecar_core_real.__run, so go_async() can't strand the publisher when
    # the rate-paced run loop deadlocks on rclpy.Rate.sleep().
    __PUBLISH_PERIOD_SEC = 0.05

    def __init__(self):
        self.node = ros2.create_node("drive_pub")
        self.__publisher = self.node.create_publisher(
            AckermannDriveStamped, self.__TOPIC, qos_profile=1
        )
        self.__message = AckermannDriveStamped()
        self.__message.header.frame_id = self.__FRAME_ID
        self.__max_speed = 0.50

        self.node.create_timer(self.__PUBLISH_PERIOD_SEC, self.__update)

    def set_speed_angle(self, speed: float, angle: float) -> None:
        assert (
            -1.0 <= speed <= 1.0
        ), f"speed [{speed}] must be between -1.0 and 1.0 inclusive."
        assert (
            -1.0 <= angle <= 1.0
        ), f"angle [{angle}] must be between -1.0 and 1.0 inclusive."

        self.__message.drive.speed = float(speed * self.__max_speed)
        # Negate angle so positive = right in the student API, matching the
        # sim convention; the throttle/pwm chain handles servo-side sign.
        self.__message.drive.steering_angle = float(-angle)

    def set_max_speed(self, max_speed: float = 0.50) -> None:
        assert (
            0.0 <= max_speed <= 1.0
        ), f"max_speed [{max_speed}] must be between 0.0 and 1.0 inclusive."

        self.__max_speed = max_speed

    def __update(self):
        """
        Stamps and publishes the current drive message. Called from the
        node's own 20 Hz timer rather than from racecar_core_real's run
        thread, so the publisher keeps running under both go() and
        go_async() regardless of run-loop pacing issues.
        """
        self.__message.header.stamp = self.node.get_clock().now().to_msg()
        self.__publisher.publish(self.__message)
