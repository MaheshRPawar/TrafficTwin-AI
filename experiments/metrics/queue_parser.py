"""
Parse SUMO queue XML output and return per-timestep lane queue records.
"""

import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path


def parse_queue(filepath: Path) -> list[dict]:
    """Read a queue XML file and return a list of per-lane queue snapshots.

    Each record is a dict with keys:
      timestep, lane_id, queueing_length, queueing_time
    Only lanes where queueing_length > 0 are included.
    """
    tree = ET.parse(filepath)  # nosec B314
    root = tree.getroot()

    records = []
    for data_elem in root.findall("data"):
        timestep = float(data_elem.attrib["timestep"])
        lanes_elem = data_elem.find("lanes")
        if lanes_elem is None:
            continue

        for lane in lanes_elem.findall("lane"):
            q_len = float(lane.attrib.get("queueing_length", 0.0))
            if q_len <= 0.0:
                continue
            records.append({
                "timestep": timestep,
                "lane_id": lane.attrib["id"],
                "queueing_length": q_len,
                "queueing_time": float(lane.attrib.get("queueing_time", 0.0)),
            })

    return records
