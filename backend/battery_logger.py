

import os
import csv
from datetime import datetime


LOG_FILENAME = "battery_log.csv"
LOG_PATH = os.path.join(os.path.dirname(__file__), LOG_FILENAME)


def log_battery_data(chip_id, node_mac, role, battery, distance, uptime_ms, timestamp=None):
 
    try:
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        file_exists = os.path.exists(LOG_PATH)

        # Open in append mode so each call writes one line
        with open(LOG_PATH, mode="a", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write header once when file is first created
            if not file_exists:
                writer.writerow(
                    [
                        "timestamp",
                        "chip_id",
                        "node_mac",
                        "role",
                        "battery",
                        "distance",
                        "uptime_ms",
                    ]
                )

            writer.writerow(
                [
                    timestamp,
                    chip_id,
                    node_mac or "",
                    role or "",
                    battery if battery is not None else "",
                    distance if distance is not None else "",
                    uptime_ms if uptime_ms is not None else "",
                ]
            )
    except Exception as exc:
        # Never crash the app because of logging problems
        print(f"[BatteryLogger] Failed to write log: {exc}")

