import json
import xml.etree.ElementTree as ET

# ---- Input & Output ----
INPUT_JSON = "Traffic.json"   # cleaned JSON file
OUTPUT_ROU = "synthetic_routes.rou.xml"  # output SUMO route file

# ---- Vehicle Types ----
vehicle_types = {
    "car": {
        "vClass": "passenger", "accel": "3.0", "decel": "4.5",
        "length": "5.0", "maxSpeed": "20", "color": "0,0,255"
    },
    "bus": {
        "vClass": "bus", "accel": "2.0", "decel": "4.0",
        "length": "12.0", "maxSpeed": "15", "color": "255,165,0"
    },
    "truck": {
        "vClass": "truck", "accel": "1.5", "decel": "4.0",
        "length": "8.0", "maxSpeed": "18", "color": "0,128,0"
    },
    "ambulance": {
        "vClass": "emergency", "accel": "3.5", "decel": "5.0",
        "length": "6.0", "maxSpeed": "25", "color": "255,0,0"
    }
}

# ---- Lane to Route Mapping ----
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

# ---- Route Definitions ----
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


# ---- Build XML ----
routes = ET.Element("routes")

# Add vehicle type definitions
for vtype, attrs in vehicle_types.items():
    ET.SubElement(routes, "vType", id=vtype, **attrs)

# Add route definitions
for route_id, edges in routes_defined.items():
    ET.SubElement(routes, "route", id=route_id, edges=" ".join(edges))

# ---- Load JSON Data ----
with open(INPUT_JSON, "r") as f:
    data = json.load(f)

# Extract vehicles across all time windows
vehicles = []
for time_window, details in data.items():
    departures = details.get("vehicle_departures", [])
    vehicles.extend(departures)

# ---- Add Vehicles to XML ----
for v in vehicles:
    veh_id = str(v.get("vehicle_id", f"veh_{id(v)}"))
    vtype = v.get("type", "car")
    depart = str(round(float(v.get("depart", 0)), 2))
    lane = v.get("lane")

    # Map lane -> route
    if lane in lane_to_route:
        route_id = lane_to_route[lane]
    else:
        continue  # skip vehicles whose lane has no mapping
    
    ET.SubElement(
        routes, "vehicle",
        id=veh_id, type=vtype, route=route_id, depart=depart
    )

# ---- Write XML File ----
tree = ET.ElementTree(routes)
tree.write(OUTPUT_ROU, encoding="UTF-8", xml_declaration=True)

print(f"✅ Route file generated successfully: {OUTPUT_ROU}")
