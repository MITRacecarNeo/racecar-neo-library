import struct
import numpy as np
class NDArray:  # stub - no runtime dependency on nptyping
    def __class_getitem__(cls, _): return cls

from physics import Physics


class PhysicsSim(Physics):
    def __init__(self, racecar) -> None:
        self.__racecar = racecar

    def __request(self, header, size: int) -> bytes:
        # Inside start/update the sim answers on the sync port; anywhere else
        # (Jupyter) on the async port
        is_async = not self.__racecar._RacecarSim__in_call
        self.__racecar._RacecarSim__send_header(header, is_async)
        return self.__racecar._RacecarSim__receive_data(size)

    def get_linear_acceleration(self) -> NDArray[3, np.float32]:
        data = self.__request(self.__racecar.Header.physics_get_linear_acceleration, 12)
        return np.array(struct.unpack("fff", data))

    def get_angular_velocity(self) -> NDArray[3, np.float32]:
        data = self.__request(self.__racecar.Header.physics_get_angular_velocity, 12)
        return np.array(struct.unpack("fff", data))

    def get_magnetic_field(self) -> NDArray[3, np.float32]:
        data = self.__request(self.__racecar.Header.physics_get_magnetic_field, 12)
        return np.array(struct.unpack("fff", data))

    def get_encoder_speed(self) -> float:
        data = self.__request(self.__racecar.Header.physics_get_encoder_speed, 4)
        return struct.unpack("f", data)[0]

    def get_battery_voltage(self) -> float:
        data = self.__request(self.__racecar.Header.physics_get_battery_voltage, 4)
        return struct.unpack("f", data)[0]

    def get_battery_current(self) -> float:
        data = self.__request(self.__racecar.Header.physics_get_battery_current, 4)
        return struct.unpack("f", data)[0]

    def get_rc_channels(self) -> NDArray[8, np.float32]:
        return np.zeros(8)  # No RC receiver in simulation.
