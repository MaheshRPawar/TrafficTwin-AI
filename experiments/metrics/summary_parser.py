"""
Parse SUMO summary XML output and return per-step simulation state records.
"""

import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path


def parse_summary(filepath: Path) -> list[dict]:
    """Read a summary XML file and return a list of simulation step snapshots.

    Each record is a dict with keys:
      time, inserted, arrived, running, halting, collisions, teleports,
      mean_waiting_time, mean_travel_time, mean_speed
    """
    tree = ET.parse(filepath)  # nosec B314
    root = tree.getroot()

    steps = []
    for elem in root.findall("step"):
        steps.append({
            "time": float(elem.attrib["time"]),
            "inserted": int(elem.attrib.get("inserted", 0)),
            "arrived": int(elem.attrib.get("arrived", 0)),
            "running": int(elem.attrib.get("running", 0)),
            "halting": int(elem.attrib.get("halting", 0)),
            "collisions": int(elem.attrib.get("collisions", 0)),
            "teleports": int(elem.attrib.get("teleports", 0)),
            "mean_waiting_time": float(elem.attrib.get("meanWaitingTime", 0.0)),
            "mean_travel_time": float(elem.attrib.get("meanTravelTime", -1.0)),
            "mean_speed": float(elem.attrib.get("meanSpeed", 0.0)),
        })

    return steps
