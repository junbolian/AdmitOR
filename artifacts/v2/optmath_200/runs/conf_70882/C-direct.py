import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    operational_cost = params["operational_cost"]
    penalty_cost = params["penalty_cost"]
    vehicle_time_per_frequency = params["vehicle_time_per_frequency"]
    total_vehicle_capacity = params["total_vehicle_capacity"]
    min_frequency_if_selected = params["min_frequency_if_selected"]
    max_frequency_if_selected = params["max_frequency_if_selected"]
    min_od_frequency = params["min_od_frequency"]
    min_transfer_hub_lines = params["min_transfer_hub_lines"]
    example_od_7_4_demand = params["example_od_7_4_demand"]

    # Lines: L_0 .. L_11
    lines = list(range(12))

    # Fixed costs indexed by line (list indexed by line index)
    fc = {i: fixed_cost[i] for i in lines}
    oc = {i: operational_cost[i] for i in lines}
    vt = {i: vehicle_time_per_frequency[i] for i in lines}

    # OD pairs in order matching the penalty_cost list
    od_pairs = ["OD_7_4", "OD_5_4", "OD_0_6", "OD_4_0", "OD_3_1", "OD_7_0",
                "OD_4_7", "OD_7_2", "OD_3_5", "OD_7_6", "OD_2_1", "OD_2_3",
                "OD_4_1", "OD_1_6", "OD_0_7"]

    # penalty_cost is a list; map by index position
    pc = {od: penalty_cost[idx] for idx, od in enumerate(od_pairs)}

    # Lines serving each OD pair
    od_lines = {
        "OD_7_4":  [1, 2, 8, 9, 10],
        "OD_5_4":  [0, 4, 5, 6],
        "OD_0_6":  [3, 6, 7, 11],
        "OD_4_0":  [0, 2, 5, 9],
        "OD_3_1":  [1, 3, 7, 10],
        "OD_7_0":  [0, 8, 9, 11],
        "OD_4_7":  [1, 2, 8, 9, 10],
        "OD_7_2":  [2, 7, 8, 10],
        "OD_3_5":  [3, 5, 6, 11],
        "OD_7_6":  [6, 7, 8, 11],
        "OD_2_1":  [1, 2, 3, 9],
        "OD_2_3":  [2, 3, 7, 10],
        "OD_4_1":  [1, 4, 5, 9],
        "OD_1_6":  [0, 6, 7, 11],
        "OD_0_7":  [0, 8, 9, 11],
    }

    # Demand for each OD pair; OD_7_4 comes from params
    od_demand = {
        "OD_7_4":  example_od_7_4_demand,
        "OD_5_4":  18,
        "OD_0_6":  15,
        "OD_4_0":  22,
        "OD_3_1":  17,
        "OD_7_0":  20,
        "OD_4_7":  19,
        "OD_7_2":  16,
        "OD_3_5":  14,
        "OD_7_6":  13,
        "OD_2_1":  12,
        "OD_2_3":  25,
        "OD_4_1":  23,
        "OD_1_6":  28,
        "OD_0_7":  20,
    }

    # Stations and lines passing through each station
    station_lines = {
        0: [0, 1, 2, 9, 11],
        1: [1, 3, 4, 7, 9],
        2: [2, 3, 7, 8, 10],
        3: [3, 5, 6, 10, 11],
        4: [0, 2, 4, 5, 9],
        5: [4, 5, 6, 8, 11],
        6: [0, 6, 7, 10, 11],
        7: [1, 7, 8, 9, 10],
    }

    model = gp.Model("transit_network")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if line i is selected
    y = model.addVars(lines, vtype=GRB.BINARY, name="y")
    # f[i] = frequency of line i
    f = model.addVars(lines, lb=0.0, name="f")
    # u[od] = unsatisfied demand for OD pair od
    u = model.addVars(od_pairs, lb=0.0, name="u")
    # h[s] = 1 if station s is a transfer hub
    stations = list(station_lines.keys())
    h = model.addVars(stations, vtype=GRB.BINARY, name="h")

    # Objective: fixed costs + operational costs + penalty costs
    obj = (
        gp.quicksum(fc[i] * y[i] for i in lines) +
        gp.quicksum(oc[i] * f[i] for i in lines) +
        gp.quicksum(pc[od] * u[od] for od in od_pairs)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Frequency bounds linked to selection
    for i in lines:
        model.addConstr(f[i] >= min_frequency_if_selected * y[i], name=f"min_freq_{i}")
        model.addConstr(f[i] <= max_frequency_if_selected * y[i], name=f"max_freq_{i}")

    # Vehicle capacity constraint
    model.addConstr(
        gp.quicksum(vt[i] * f[i] for i in lines) <= total_vehicle_capacity,
        name="vehicle_capacity"
    )

    # OD demand constraints: frequencies on relevant lines + unsatisfied demand >= required demand
    for od in od_pairs:
        relevant = od_lines[od]
        model.addConstr(
            gp.quicksum(f[i] for i in relevant) + u[od] >= od_demand[od],
            name=f"demand_{od}"
        )

    # Minimum OD frequency: each relevant line that is selected must contribute at least min_od_frequency
    for od in od_pairs:
        relevant = od_lines[od]
        model.addConstr(
            gp.quicksum(f[i] for i in relevant) >= min_od_frequency * gp.quicksum(y[i] for i in relevant),
            name=f"min_od_freq_{od}"
        )

    # Transfer hub constraints
    for s in stations:
        lines_at_s = station_lines[s]
        model.addConstr(
            gp.quicksum(y[i] for i in lines_at_s) >= min_transfer_hub_lines * h[s],
            name=f"hub_{s}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}