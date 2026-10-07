"""TrafficTwin AI — GPS-like Event Stream Schema and Normalization (Module M4).

Defines normalized simulated GPS event format, extraction from SUMO vehicle state,
and validation logic.
"""


def extract_location_context(road_id: str, lane_id: str) -> tuple[str | None, str]:
    """Map SUMO road and lane IDs to junction and road segment representation."""
    # Check if vehicle is inside a junction (internal edge starts with ':')
    if road_id.startswith(":"):
        junction_id = road_id[1:].split("_")[0]
        road_segment_id = road_id
    else:
        junction_id = None
        road_segment_id = road_id

    return junction_id, road_segment_id


def build_gps_event(
    vehicle_id: str,
    vehicle_type: str,
    timestamp: float,
    x: float,
    y: float,
    speed_mps: float,
    heading: float,
    lane_id: str,
    road_id: str,
    corridor_id: str = "corridor_4j",
) -> dict:
    """Construct a normalized GPS-like event from simulated vehicle observations."""
    # Convert speed from m/s to km/h
    speed_kmph = round(speed_mps * 3.6, 2)

    # Normalize heading to 0-360 degrees
    heading_degrees = round(float(heading) % 360.0, 2)

    # Map road and lane to corridor location context
    junction_id, road_segment_id = extract_location_context(road_id, lane_id)

    # Deterministic event ID
    event_id = f"gps_{vehicle_id}_{timestamp:.1f}"

    return {
        "event_type": "vehicle_position",
        "event_id": event_id,
        "vehicle_id": vehicle_id,
        "vehicle_type": vehicle_type,
        "timestamp": round(float(timestamp), 2),
        "corridor_id": corridor_id,
        "junction_id": junction_id,
        "lane_id": lane_id,
        "road_segment_id": road_segment_id,
        "x": round(float(x), 2),
        "y": round(float(y), 2),
        "speed_kmph": speed_kmph,
        "heading_degrees": heading_degrees,
        "source": "simulated_sumo",
        "freshness_seconds": 0.0,
    }


def validate_gps_event(event: dict) -> tuple[bool, str]:
    """Validate a GPS-like event against the TrafficTwin normalized schema."""
    if not isinstance(event, dict):
        return False, "Event must be a dictionary"

    # Validate event type
    if event.get("event_type") != "vehicle_position":
        return False, f"Invalid event_type: {event.get('event_type')}"

    # Required string fields
    required_strings = [
        "event_id",
        "vehicle_id",
        "vehicle_type",
        "corridor_id",
        "lane_id",
        "road_segment_id",
        "source",
    ]
    for field in required_strings:
        val = event.get(field)
        if not isinstance(val, str) or not val.strip():
            return False, f"Field '{field}' must be a non-empty string"

    # Validate source
    if event.get("source") != "simulated_sumo":
        return False, f"Invalid source: {event.get('source')}"

    # Validate junction_id (optional string or None)
    junction_id = event.get("junction_id")
    if junction_id is not None and not isinstance(junction_id, str):
        return False, "Field 'junction_id' must be a string or None"

    # Numeric fields
    numeric_fields = ["timestamp", "x", "y", "speed_kmph", "heading_degrees", "freshness_seconds"]
    for num_field in numeric_fields:
        val = event.get(num_field)
        if not isinstance(val, (int, float)):
            return False, f"Field '{num_field}' must be a number"

    # Value range checks
    if event["timestamp"] < 0.0:
        return False, "Timestamp must be non-negative"

    if event["speed_kmph"] < 0.0:
        return False, "Speed must be non-negative"

    if not (0.0 <= event["heading_degrees"] <= 360.0):
        return False, "Heading must be between 0 and 360 degrees"

    if event["freshness_seconds"] < 0.0:
        return False, "Freshness must be non-negative"

    return True, ""
