"""
Copyright MIT and Harvey Mudd College
MIT License
Summer 2020

Manages communication with RacecarSim.
"""

import struct
import socket
import sys
import select
from enum import IntEnum
from signal import signal, SIGINT
from typing import Callable, Optional

import camera_sim
import controller_sim
import display_sim
import drive_sim
import lidar_sim
import physics_sim

from racecar_core import Racecar
import racecar_utils as rc_utils


class RacecarSim(Racecar):
    __IP = "127.0.0.1"
    __UNITY_PORT = (__IP, 5065)
    __UNITY_ASYNC_PORT = (__IP, 5064)
    __VERSION = 1

    class Header(IntEnum):
        """
        The packet headers of the communication protocol with RacecarSim.
        """

        error = 0
        connect = 1
        unity_start = 2
        unity_update = 3
        unity_exit = 4
        python_finished = 5
        python_send_next = 6
        python_exit = 7
        racecar_go = 8
        racecar_set_start_update = 9
        racecar_get_delta_time = 10
        racecar_set_update_slow_time = 11
        camera_get_color_image = 12
        camera_get_depth_image = 13
        camera_get_width = 14
        camera_get_height = 15
        controller_is_down = 16
        controller_was_pressed = 17
        controller_was_released = 18
        controller_get_trigger = 19
        controller_get_joystick = 20
        display_show_image = 21
        drive_set_speed_angle = 22
        drive_stop = 23
        drive_set_max_speed = 24
        lidar_get_num_samples = 25
        lidar_get_samples = 26
        physics_get_linear_acceleration = 27
        physics_get_angular_velocity = 28

    class Error(IntEnum):
        """
        The error codes defined in the communication protocol with RacecarSim.
        """

        generic = 0
        timeout = 1
        python_exception = 2
        no_free_car = 3
        python_outdated = 4
        racecarsim_outdated = 5
        fragment_mismatch = 6

    def __send_header(self, function_code: Header, is_async: bool = False) -> None:
        self.__send_data(struct.pack("B", function_code.value), is_async)

    def __send_error(self, error: Error, is_async: bool = False) -> None:
        self.__send_data(struct.pack("BB", self.Header.error, error), is_async)

    def __send_data(self, data: bytes, is_async: bool = False) -> None:
        if is_async:
            self.__socket.sendto(data, self.__UNITY_ASYNC_PORT)
        else:
            self.__socket.sendto(data, self.__UNITY_PORT)

    def __receive_data(self, buffer_size: int = 8) -> bytes:
        data, _ = self.__socket.recvfrom(buffer_size)
        return data

    def __receive_fragmented(
        self, num_fragments: int, total_bytes: int, is_async: bool = False
    ) -> bytes:
        raw_bytes: bytes = bytes()
        fragment_size = total_bytes // num_fragments
        for i in range(0, num_fragments):
            raw_bytes += self.__receive_data(fragment_size)
            self.__send_header(self.Header.python_send_next, is_async)
        return raw_bytes

    def __init__(self, isHeadless: bool = False) -> None:
        self.camera = camera_sim.CameraSim(self)
        self.controller = controller_sim.ControllerSim(self)
        self.display = display_sim.DisplaySim(isHeadless)
        self.drive = drive_sim.DriveSim(self)
        self.physics = physics_sim.PhysicsSim(self)
        self.lidar = lidar_sim.LidarSim(self)

        self.__start: Callable[[], None]
        self.__update: Callable[[], None]
        self.__update_slow: Optional[Callable[[], None]]
        self.__update_slow_time: float = 1
        self.__update_slow_counter: float = 0
        self.__delta_time: float = -1

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__in_call: bool = False

        signal(SIGINT, self.__handle_sigint)

    def go(self) -> None:
        print(">> Python script loaded, awaiting connection from RacecarSim.")

        # Repeatedly try to connect to RacecarSim (async) until we receive a response
        while True:
            self.__send_data(
                struct.pack("BB", self.Header.connect, self.__VERSION), True
            )
            ready = select.select([self.__socket], [], [], 0.25)
            if ready[0]:
                data, _ = self.__socket.recvfrom(2)
                header = int(data[0])
                if header == self.Header.connect.value:
                    car_index = int(data[1])
                    rc_utils.print_colored(
                        f">> Connection established with RacecarSim (assigned to car number {car_index}). Enter user program mode in RacecarSim to begin...",
                        rc_utils.TerminalColor.green,
                    )
                    break
                elif header == self.Header.error.value:
                    self.__handle_error(int(data[1]))
                else:
                    rc_utils.print_error(
                        ">> Invalid handshake with RacecarSim, closing script..."
                    )
                    self.__send_header(self.Header.error)
                    return

        # Respond to start/update commands from RacecarSim (sync) until we receive an
        # exit or error command
        while True:
            data, _ = self.__socket.recvfrom(8)
            header = int(data[0])

            if header == self.Header.unity_start.value:
                try:
                    self.__in_call = True
                    self.set_update_slow_time()
                    self.__start()
                    self.__in_call = False
                except SystemExit:
                    raise
                except:
                    self.__send_error(self.Error.python_exception)
                    raise
            elif header == self.Header.unity_update.value:
                try:
                    self.__in_call = True
                    self.__handle_update()
                    self.__in_call = False
                except SystemExit:
                    raise
                except:
                    self.__send_error(self.Error.python_exception)
                    raise
            elif header == self.Header.unity_exit.value:
                rc_utils.print_warning(
                    ">> Exit command received from RacecarSim, closing script..."
                )
                break
            elif header == self.Header.error:
                error = int(data[1]) if len(data) > 1 else self.Error.generic
                self.__handle_error(error)
            else:
                rc_utils.print_error(
                    f">> Error: unexpected packet with header [{header}] received from RacecarSim, closing script..."
                )
                self.__send_header(self.Header.error)
                break

            self.__send_header(self.Header.python_finished)

    def set_start_update(
        self,
        start: Callable[[], None],
        update: Callable[[], None],
        update_slow: Optional[Callable[[], None]] = None,
    ) -> None:
        self.__start = start
        self.__update = update
        self.__update_slow = update_slow

    def get_delta_time(self) -> float:
        if self.__delta_time < 0:
            self.__send_header(self.Header.racecar_get_delta_time)
            [value] = struct.unpack("f", self.__receive_data())
            self.__delta_time = value
        return self.__delta_time

    def set_update_slow_time(self, update_slow_time: float = 1.0) -> None:
        self.__update_slow_time = update_slow_time

    def __handle_update(self) -> None:
        self.__update()

        self.__delta_time = -1
        if self.__update_slow is not None:
            self.__update_slow_counter -= self.get_delta_time()
            if self.__update_slow_counter < 0:
                self.__update_slow()
                self.__update_slow_counter = self.__update_slow_time

        self.camera._CameraSim__update()
        self.controller._ControllerSim__update()
        self.lidar._LidarSim__update()

    def __handle_sigint(self, signal_received: int, frame) -> None:
        # Send exit command to sync port if we are in the middle of servicing a start
        # or update call; otherwise send it to the async port
        is_async = not self.__in_call
        label = "async" if is_async else "sync"

        rc_utils.print_warning(
            f">> CTRL-C (SIGINT) detected. Sending exit command to Unity ({label})..."
        )
        self.__send_header(self.Header.python_exit, is_async)

        print(">> Closing script...")
        exit(0)

    def __handle_error(self, error: Error):
        text = ">> Error: "
        if error == self.Error.generic:
            text += "An unknown error has occurred when communicating with RacecarSim."
        elif error == self.Error.timeout:
            text = "The Python script took too long to respond to RacecarSim. If this issue persists, make sure that your script does not block execution."
        elif error == self.Error.no_free_car:
            text += "Unable to connect to RacecarSim because every racecar already has a connected Python script."
        elif error == self.Error.python_outdated:
            text = "racecar_core is out of date and incompatible with RacecarSim. Please update your Python racecar libraries to the newest version."
        elif error == self.Error.racecarsim_outdated:
            text = "RacecarSim is out of date and incompatible with racecar_core. Please download the newest version of RacecarSim."
        elif error == self.Error.fragment_mismatch:
            text = "RacecarSim and Python become out of sync while sending a block message."

        rc_utils.print_error(text)
        print(">> Closing script...")
        exit(0)
