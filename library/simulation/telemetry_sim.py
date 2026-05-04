"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: telemetry_sim.py
File Description: Contains the Telemetry simulation module of the racecar_core library.
"""

import time

import pandas as pd
from matplotlib import pyplot as plt
from telemetry import Telemetry, _resolve_log_paths


class TelemetrySim(Telemetry):

    def __init__(self) -> None:
        self.variable_names = None
        self._LOG_FILE_NAME, self._PLOT_FILE_NAME = _resolve_log_paths()
        self.log_file = open(self._LOG_FILE_NAME, "w+")
        self.start_time = time.time()

    def declare_variables(self, *names: str) -> None:
        if self.variable_names is None:
            self.variable_names = names
            names = ["time", *names]
            print(','.join(map(str, names)), file=self.log_file)

    def record(self, *values: any) -> None:
        assert(
            len(self.variable_names) == len(values)
        ), f"{len(self.variable_names)} variables were declared, but {len(values)} values were provided"

        time_since_start = time.time() - self.start_time
        values = [time_since_start, *values]
        print(','.join(map(str, values)), file=self.log_file)

    def visualize(self) -> None:
        if self.variable_names is None:
            return

        # Seek to beginning of file before reading,
        # then seek to the end afterwards in case we want to write more data
        self.log_file.seek(0)
        frame = pd.read_csv(self.log_file)
        frame["time"] *= 1000

        fig, ax = plt.subplots()
        ax.set_xlabel("Time (ms)")
        ax.set_title("Telemetry Variables vs. Time")
        for variable in frame.columns:
            if variable != "time":
                ax.plot(frame["time"], frame[variable], label=variable)
        ax.legend()

        plt.savefig(self._PLOT_FILE_NAME)
        self.log_file.seek(0, 2)
