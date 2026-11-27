"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: drive_real.py
File Description: Contains the Drive module of the racecar_core library.

The car drives from one source at a time. On a car with the driver installed,
the program holds the car from create_racecar() until it exits, moving or not.
While something else holds it (an app, a Planner mission), rc.drive does
nothing and the program says so once in the terminal; the program takes the
car when the other lets go, and drives again from its next stop. While rc.nav
drives, rc.drive calls are ignored.
"""

import atexit
import os

from drive import Drive

import rclpy as ros2
from ackermann_msgs.msg import AckermannDriveStamped


def program_lease():
    """Return the driver's drive lease for this program, or None without the driver."""
    try:
        from racecar_neo_ros2_driver.drive_lease import DriveLease
    except ImportError:
        return None
    # One owner per program, so two programs do not share the car.
    return DriveLease(f"program-{os.getpid()}", "Program")


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

    def __init__(self, lease=None):
        self.node = ros2.create_node("drive_pub")
        self.__publisher = self.node.create_publisher(
            AckermannDriveStamped, self.__TOPIC, qos_profile=1
        )
        self.__message = AckermannDriveStamped()
        self.__message.header.frame_id = self.__FRAME_ID
        self.__max_speed = 0.25

        self.__lease = lease if lease is not None else program_lease()
        self.__refused_by = ""  # who held the car when this program was last told
        self.__wait_for_stop = False  # refused while moving: drive again from a stop
        self.__nav = False  # rc.nav drives
        self.__nav_told = False
        if self.__lease is not None:
            atexit.register(self.__lease.release)

        self.node.create_timer(self.__PUBLISH_PERIOD_SEC, self.__update)

    def set_speed_angle(self, speed: float, angle: float) -> None:
        assert (
            -1.0 <= speed <= 1.0
        ), f"speed [{speed}] must be between -1.0 and 1.0 inclusive."
        assert (
            -1.0 <= angle <= 1.0
        ), f"angle [{angle}] must be between -1.0 and 1.0 inclusive."

        if self.__nav:
            if not self.__nav_told:
                print(">> rc.drive does nothing while rc.nav drives.")
                self.__nav_told = True
            return
        self.__message.drive.speed = float(speed * self.__max_speed)
        # Negate angle so positive = right in the student API, matching the
        # sim convention; the throttle/pwm chain handles servo-side sign.
        self.__message.drive.steering_angle = float(-angle)

    def set_max_speed(self, max_speed: float = 0.25) -> None:
        assert (
            0.0 <= max_speed <= 1.0
        ), f"max_speed [{max_speed}] must be between 0.0 and 1.0 inclusive."

        self.__max_speed = max_speed

    def holds_car(self) -> bool:
        """Return True while this program holds the car (always without the driver)."""
        return self.__lease is None or self.__lease.held

    def refused_by(self) -> str:
        """Return why the car is not this program's, such as "Planner is driving.", or ""."""
        if self.__lease is None or self.__lease.held:
            return ""
        return self.__lease.refused()

    def _nav_drives(self, on: bool) -> None:
        """
        Called by rc.nav: while on, the navigator drives under this program's
        hold and rc.drive calls are ignored. Off, the car is at zero until the
        next rc.drive call.
        """
        self.__nav = on
        self.__nav_told = False
        self.__message.drive.speed = 0.0
        self.__message.drive.steering_angle = 0.0
        if self.__lease is not None:
            self.__lease.nav = on
            self.__lease.hold()

    def __update(self):
        """
        Stamps and publishes the current drive message. Called from the
        node's own 20 Hz timer rather than from racecar_core_real's run
        thread, so the publisher keeps running under both go() and
        go_async() regardless of run-loop pacing issues.
        """
        if self.__lease is not None and not self.__lease.hold():
            holder = self.__lease.refused()  # "Planner is driving."
            if holder != self.__refused_by:
                print(f">> {holder} rc.drive will not drive the car until it stops.")
                self.__refused_by = holder
            if self.__message.drive.speed != 0.0:
                self.__wait_for_stop = True
            return
        if self.__refused_by:
            name = self.__refused_by.removesuffix(" is driving.")
            print(
                f">> {name} has stopped driving. "
                "rc.drive will now drive the car again after a speed reset to 0."
            )
            self.__refused_by = ""
        if self.__nav:
            return  # the navigator drives
        message = self.__message
        if self.__wait_for_stop:
            if message.drive.speed != 0.0:
                message = AckermannDriveStamped()
                message.header.frame_id = self.__FRAME_ID
            else:
                self.__wait_for_stop = False
        message.header.stamp = self.node.get_clock().now().to_msg()
        self.__publisher.publish(message)
