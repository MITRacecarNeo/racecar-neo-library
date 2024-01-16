import sys
import struct
import numpy as np
from nptyping import NDArray

from lidar import Lidar


class LidarSim(Lidar):
    def __init__(self, racecar) -> None:
        self.__racecar = racecar
        self.__ranges: NDArray[720, np.float32]
        self.__is_current: bool = False

    def get_samples(self) -> NDArray[720, np.float32]:
        if not self.__is_current:
            self.__racecar._RacecarSim__send_header(
                self.__racecar.Header.lidar_get_samples
            )
            raw_bytes: bytes = self.__racecar._RacecarSim__receive_data(
                self._NUM_SAMPLES * 4
            )
            self.__ranges = np.frombuffer(raw_bytes, dtype=np.float32)
            self.__is_current = True
        return self.__ranges

    def get_samples_async(self) -> NDArray[720, np.float32]:
        self.__racecar._RacecarSim__send_header(
            self.__racecar.Header.lidar_get_samples, True
        )
        raw_bytes: bytes = self.__racecar._RacecarSim__receive_data(
            self._NUM_SAMPLES * 4
        )
        return np.frombuffer(raw_bytes, dtype=np.float32)

    def __update(self) -> None:
        self.__is_current = False
