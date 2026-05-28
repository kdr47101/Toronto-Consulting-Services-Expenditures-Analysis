"""One-command pipeline: fetch -> clean -> analyze -> anomaly."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))

import fetch_data  # noqa: E402
import clean_data  # noqa: E402
import analyze  # noqa: E402
import anomaly  # noqa: E402


def main() -> None:
    print(">>> 1/4  fetching raw data")
    fetch_data.fetch_consulting_data()

    print("\n>>> 2/4  cleaning")
    clean_data.build()

    print("\n>>> 3/4  rendering charts")
    analyze.render_all()

    print("\n>>> 4/4  scoring anomalies")
    anomaly.run()

    print("\nDone.")


if __name__ == "__main__":
    main()
