"""
Copyright MIT
GNU General Public License v3.0

BWSI Autonomous RACECAR Course
Racecar Neo LTS

File Name: telemetry.py
File Description: Defines the interface of the Telemetry module of the racecar_core library
"""

import abc
import os
import re
import sys
import time


def _resolve_log_paths() -> tuple[str, str]:
    """
    Build the CSV and PNG log paths inside racecar-student/labs/logs/.

    Filename format: YYYYMMDD_HHMMSS_<calling_file_stem>.{csv,png}, where the
    timestamp is wall-clock local time on the student's machine. Creates the
    logs/ folder on first use.
    """
    # labs/ lives at <library_root>/../labs/, regardless of which racecar-venv or
    # CWD the student runs from. __file__ is racecar-student/library/telemetry.py.
    library_dir = os.path.dirname(os.path.abspath(__file__))
    labs_dir = os.path.abspath(os.path.join(library_dir, "..", "labs"))
    logs_dir = os.path.join(labs_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Identify what produced the log. .py scripts give us argv[0]; notebooks
    # leak their path through __vsc_ipynb_file__ (VS Code) or JPY_SESSION_NAME.
    stem = "interactive"
    argv0 = sys.argv[0] if sys.argv else ""
    main_mod = sys.modules.get("__main__")
    nb_path = getattr(main_mod, "__vsc_ipynb_file__", None) or os.environ.get("JPY_SESSION_NAME")
    if nb_path:
        stem = os.path.splitext(os.path.basename(nb_path))[0]
    elif argv0 and not argv0.endswith(("ipykernel_launcher.py", "kernel.py")):
        base = os.path.basename(argv0)
        if base:
            stem = os.path.splitext(base)[0]
    elif "ipykernel" in sys.modules:
        stem = "notebook"

    # Strip anything that would make the filename awkward on Windows/macOS.
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "log"

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"{timestamp}_{stem}"
    return os.path.join(logs_dir, base + ".csv"), os.path.join(logs_dir, base + ".png")


class Telemetry(abc.ABC):
    """
    Records and visualizes real time sensor data and internal states
    """
    @abc.abstractmethod
    def declare_variables(self, *names: str) -> None:
        """
        Declare a list of variables that will be recorded by telemetry.

        Args:
            names: The names of each variable to be declared.

        Note:
            This function should only be called once, and all subsequent calls will have no effect.
            In addition to the variables declared here, when a data point is pushed to telemetry, its timestamp will
            also be recorded.

        Example::

            # Declare variables to be recorded
            rc.telemetry.declare_variables("speed", "angle")

            # Push a data point containing a speed and angle value to the telemetry
            rc.telemetry.record(1, 0.5)
        """
        pass

    @abc.abstractmethod
    def record(self, *values: any) -> None:
        """
        Record a data point. This should contain a value for each declared variable.

        Args:
            values: The value of each declared variable, in the same order as the declaration.

        Note:
            `declare_variables` must be called before this function.
            If too few / too many values are provided, an exception will be thrown.

        Example::

            # Declare variables to be recorded
            rc.telemetry.declare_variables("speed", "angle")

            # Push a data point containing a speed and angle value to the telemetry
            rc.telemetry.record(1, 0.5)
        """
        pass

    @abc.abstractmethod
    def visualize(self) -> None:
        """
        Generate and save a time-series graph of the recorded data points

        Note:
            This function does not need to be manually called, as it should be
            called automatically when the user program exits.
            If some variables look squished on the line graph, consider normalizing
            your variables so they have similar magnitude.
        """
        pass
