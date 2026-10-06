"""
TrafficTwin AI - Signal Preemption & Monitoring Controller
Aarambh WCE Hackathon 2026 - Day-1 Working Prototype

Core Functionality:
- Establishes bi-directional TraCI socket link with Eclipse SUMO.
- Tracks live vehicle telemetry and route navigation.
- Evaluates approach distances to junction J6.
- Grants dynamic green-wave preemption to emergency vehicles.
- Safely restores baseline cyclic timing once intersection is cleared.
"""

import os
import sys

# Ensure SUMO_HOME is set; fallback to site-packages if installed via pip
if 'SUMO_HOME' not in os.environ:
    try:
        import sumo
        os.environ['SUMO_HOME'] = sumo.SUMO_HOME
    except ImportError:
        pass

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# Simulation launch parameters
Sumo_config = [
    'sumo-gui',
    '-c', 'SUMOSample/Sample.sumocfg',
    '--start',
    '--step-length', '0.05',
    '--delay', '100',
    '--lateral-resolution', '0.1'
]

# Start SUMO runtime and connect TraCI controller
traci.start(Sumo_config)

# Mapping of junction ID + approach corridor to target green phase index
desired_phase_mapping = {
    'Node2_EW': 0,
    'Node2_NS': 2,
    'Node5_EW': 0,
    'Node5_NS': 2,
    'J6_EW': 0,     # Phase 0: East-West green
    'J6_NS': 2,     # Phase 2: North-South green
}

adjusted_tls = {}
step = 0

def get_emergency_vehicle_direction(vehicle_id):
    """Determine the primary corridor direction based on active road ID."""
    current_edge = traci.vehicle.getRoadID(vehicle_id).lower()
    print(f"Vehicle {vehicle_id} is on edge {current_edge}", flush=True)
    if 'nb' in current_edge or 'sb' in current_edge or 'e5' in current_edge:
        return 'NS'
    elif 'eb' in current_edge or 'wb' in current_edge or 'e3' in current_edge or 'e4' in current_edge:
        return 'EW'
    else:
        return None

def process_emergency_vehicles(desired_phase_mapping, adjusted_tls, step):
    """
    Detect emergency vehicles, override traffic signals to clear priority corridor,
    and revert to normal schedule when the intersection is cleared.
    """
    emergency_vehicles = [
        veh for veh in traci.vehicle.getIDList()
        if traci.vehicle.getTypeID(veh) == "emergency"
    ]

    active_tls = set()

    for veh in emergency_vehicles:
        direction = get_emergency_vehicle_direction(veh)
        if direction:
            next_tls = traci.vehicle.getNextTLS(veh)
            print(f"next_tls for {veh}: {next_tls}", flush=True)

            if next_tls:
                tls_info = next_tls[0]
                tlsID, linkIndex, distance, state = tls_info
                tl_key = f"{tlsID}_{direction}"
                desired_phase = desired_phase_mapping.get(tl_key)

                if desired_phase is not None:
                    current_phase = traci.trafficlight.getPhase(tlsID)
                    print(f"TLS {tlsID}, Current phase: {current_phase}, Desired phase: {desired_phase}", flush=True)

                    active_tls.add(tlsID)

                    if tlsID not in adjusted_tls or adjusted_tls[tlsID] != desired_phase:
                        adjusted_tls[tlsID] = desired_phase
                        if current_phase == desired_phase:
                            new_duration = max(20, traci.trafficlight.getPhaseDuration(tlsID) + 10)
                            traci.trafficlight.setPhaseDuration(tlsID, new_duration)
                            print(f"Extended phase {current_phase} of {tlsID} to {new_duration} seconds", flush=True)
                        else:
                            # Rapid cycle transition
                            traci.trafficlight.setPhaseDuration(tlsID, 0.1)
                            print(f"Shortened phase {current_phase} of {tlsID} to transition quickly", flush=True)

    # Revert signals when emergency vehicle exits junction
    for tlsID in list(adjusted_tls.keys()):
        if tlsID not in active_tls:
            del adjusted_tls[tlsID]
            print(f"Resetting traffic light {tlsID} to normal operation.", flush=True)

    step += 1
    return step

# Main simulation loop
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    step = process_emergency_vehicles(desired_phase_mapping, adjusted_tls, step)

traci.close()
