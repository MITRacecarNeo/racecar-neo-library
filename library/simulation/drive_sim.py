import struct

from drive import Drive


class DriveSim(Drive):
    def __init__(self, racecar) -> None:
        self.__racecar = racecar

    def set_speed_angle(self, speed: float, angle: float) -> None:
        assert (
            -1.0 <= speed <= 1.0
        ), f"speed [{speed}] must be between -1.0 and 1.0 inclusive."
        assert (
            -1.0 <= angle <= 1.0
        ), f"angle [{angle}] must be between -1.0 and 1.0 inclusive."

        self.__racecar._RacecarSim__send_data(
            struct.pack(
                "Bff", self.__racecar.Header.drive_set_speed_angle.value, speed, angle,
            )
        )

    def set_max_speed(self, max_speed: float = 0.25) -> None:
        assert (
            0.0 <= max_speed <= 1.0
        ), f"max_speed [{max_speed}] must be between 0.0 and 1.0 inclusive."

        self.__racecar._RacecarSim__send_data(
            struct.pack(
                "Bf", self.__racecar.Header.drive_set_max_speed.value, max_speed,
            )
        )
