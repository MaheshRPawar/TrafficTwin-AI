"""
Parse SUMO tripinfo XML output and return per-vehicle trip records.
"""

import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path


def parse_tripinfo(filepath: Path) -> list[dict]:
    """Read a tripinfo XML file and return a list of trip records.

    Each record is a dict with keys:
      id, vtype, depart, arrival, duration, waiting_time, travel_time, route_length
    Only completed trips (arrival >= 0) are included.
    """
    tree = ET.parse(filepath)  # nosec B314
    root = tree.getroot()

    trips = []
    for elem in root.findall("tripinfo"):
        arrival = float(elem.attrib.get("arrival", -1))
        if arrival < 0:
            # Vehicle did not complete its route during the simulation window
            continue

        trips.append({
            "id": elem.attrib["id"],
            "vtype": elem.attrib.get("vType", ""),
            "depart": float(elem.attrib["depart"]),
            "arrival": arrival,
            "duration": float(elem.attrib["duration"]),
            "waiting_time": float(elem.attrib.get("waitingTime", 0.0)),
            "travel_time": float(elem.attrib["duration"]),
            "route_length": float(elem.attrib.get("routeLength", 0.0)),
        })

    return trips
