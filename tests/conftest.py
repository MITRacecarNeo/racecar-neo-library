"""Put library/ and its real/ and simulation/ folders on the import path, as create_racecar does."""

import sys
from pathlib import Path

LIBRARY = Path(__file__).resolve().parent.parent / "library"
for folder in (LIBRARY, LIBRARY / "real", LIBRARY / "simulation"):
    sys.path.insert(0, str(folder))
