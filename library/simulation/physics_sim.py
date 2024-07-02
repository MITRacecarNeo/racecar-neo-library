import struct
import numpy as np
from nptyping import NDArray, Shape, Float32

from physics import Physics


class PhysicsSim(Physics):
    def __init__(self, racecar) -> None:
        self.__racecar = racecar

    def get_linear_acceleration(self) -> NDArray[Shape['3'], Float32]:
        self.__racecar._RacecarSim__send_header(
            self.__racecar.Header.physics_get_linear_acceleration
        )
        values = struct.unpack("fff", self.__racecar._RacecarSim__receive_data(12))
        return np.array(values)

    def get_angular_velocity(self) -> NDArray[Shape['3'], Float32]:
        self.__racecar._RacecarSim__send_header(
            self.__racecar.Header.physics_get_angular_velocity
        )
        values = struct.unpack("fff", self.__racecar._RacecarSim__receive_data(12))
        return np.array(values)
