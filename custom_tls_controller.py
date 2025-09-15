import traci
import json

# ---------------- Lane → Route Mapping ----------------
lane_to_route = {
    "E_0_0": "E0_to_E1",
    "E_0_1": "E0_to_E1",
    "E_0_2": "E0_to_E1",
    "E_0_3": "E0_to_N3",
    "W_1_0": "W1_to_N3",
    "W_1_1": "W1_to_W0",
    "W_1_2": "W1_to_W0",
    "W_1_3": "W1_to_S1",
    "N_0": "N_to_E1",
    "N_1": "N_to_N3",
    "N_2": "N_to_W0",
    "S_0": "S_to_W0",
    "S_1_0": "S_to_S1",
    "S_1_1": "S_to_E1"
}

routes_defined = {
    "E0_to_E1": ["E_0", "E_1"],
    "E0_to_S1": ["E_0", "S_1"],
    "E0_to_N3": ["E_0", "N_3"],
    "W1_to_N3": ["W_1", "N_3"],
    "W1_to_W0": ["W_1", "W_0"],
    "W1_to_S1": ["W_1", "S_1"],
    "N_to_E1": ["N", "E_1"],
    "N_to_N3": ["N", "N_3"],
    "N_to_W0": ["N", "W_0"],
    "S_to_W0": ["S", "W_0"],
    "S_to_S1": ["S", "S_1"],
    "S_to_E1": ["S", "E_1"]
}

# ---------------- Lane → Phase Mapping ----------------
# (depends on your TLS definition in net.xml)
lane_to_phase = {
    "E_0_0": 0, "E_0_1": 0, "E_0_2": 0, "E_0_3": 0,  # Eastbound
    "W_1_0": 0, "W_1_1": 0, "W_1_2": 0, "W_1_3": 0,  # Westbound
    "N_0": 1, "N_1": 1, "N_2": 1,                   # Northbound
    "S_0": 1, "S_1_0": 1, "S_1_1": 1                # Southbound
}

# ---------------- Load traffic.json ----------------
with open("traffic.json", "r") as f:
    traffic_data = json.load(f)

# Convert JSON keys ("00:00:00 - 00:00:05") → step ranges
time_slots = {}
for slot, details in traffic_data.items():
    start_str, end_str = slot.split(" - ")
    h, m, s = map(int, start_str.split(":"))
    start_time = h * 3600 + m * 60 + s
    h, m, s = map(int, end_str.split(":"))
    end_time = h * 3600 + m * 60 + s
    time_slots[(start_time, end_time)] = details


# ---------------- Traffic Light Custom Logic ----------------
def get_green_times(vehicle_counts):
    """Assign green times based on vehicle counts from JSON."""
    min_green, max_green = 10, 40
    total = sum(vehicle_counts.values())
    if total == 0:
        return {lane: min_green for lane in vehicle_counts}

    green_times = {}
    for lane, count in vehicle_counts.items():
        green_times[lane] = min_green + int((count / total) * (max_green - min_green))
    return green_times


# ---------------- Run Simulation ----------------
def run():
    traci.start(["sumo-gui", "-c", "college_sumo.sumocfg"])
    step = 0
    active_vehicles = set()

    while step < 500:  # run for 500 seconds
        traci.simulationStep()

        # Check which 5s slot we are in
        for (start, end), details in time_slots.items():
            if step == start:
                vehicle_counts = details["vehicle_counts"]
                vehicles = details.get("vehicles", [])

                print(f"\n⏱️ Time {start}-{end}s Summary:")
                print(" Vehicle Counts:", vehicle_counts)

                # Print & inject vehicles
                for v in vehicles:
                    print(f" Vehicle {v['veh_id']} | Lane: {v['lane']} | Depart: {v['depart_time']}")

                    if int(v["depart_time"]) == step and v["veh_id"] not in active_vehicles:
                        try:
                            route_id = lane_to_route.get(v["lane"])
                            if route_id:
                                if not traci.route.exists(route_id):
                                    traci.route.add(route_id, routes_defined[route_id])
                                traci.vehicle.add(
                                    v["veh_id"], routeID=route_id,
                                    typeID=v["type"], depart=str(v["depart_time"])
                                )
                                active_vehicles.add(v["veh_id"])
                            else:
                                print(f"⚠️ No route found for lane {v['lane']}")
                        except traci.TraCIException as e:
                            print(f"⚠️ Could not add {v['veh_id']}: {e}")

                # Compute signal plan
                green_times = get_green_times(vehicle_counts)
                print(" Signal Plan:", green_times)

                # Apply logic: green → lane with max count
                if traci.trafficlight.getIDList():
                    tls_id = traci.trafficlight.getIDList()[0]
                    best_lane = max(green_times, key=green_times.get)
                    if best_lane in lane_to_phase:
                        phase_idx = lane_to_phase[best_lane]
                        traci.trafficlight.setPhase(tls_id, phase_idx)
                        traci.trafficlight.setPhaseDuration(tls_id, green_times[best_lane])
                        print(f" 🚦 Green given to {best_lane} (phase {phase_idx}) for {green_times[best_lane]}s")

        step += 1

    traci.close()


if __name__ == "__main__":
    run()

