import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    operational_cost = params["operational_cost"]
    penalty_cost = params["penalty_cost"]
    demand = params["demand"]
    min_frequency = params["min_frequency"]
    max_frequency = params["max_frequency"]
    total_vehicle_limit = params["total_vehicle_limit"]
    vehicle_usage_per_frequency = params["vehicle_usage_per_frequency"]

    lines = list(range(9))  # L_0 .. L_8
    od_pairs = ["OD_3_2", "OD_2_0", "OD_0_1", "OD_1_3", "OD_3_4",
                "OD_1_0", "OD_1_4", "OD_2_3", "OD_4_3", "OD_4_0"]
    od_indices = list(range(len(od_pairs)))

    # Lines that serve each OD pair (by OD index)
    od_lines = {
        0: [0, 3, 4, 5, 6],  # OD_3_2
        1: [2, 7, 8],         # OD_2_0
        2: [0, 3, 5, 7],      # OD_0_1
        3: [8],               # OD_1_3
        4: [3, 6, 7, 8],      # OD_3_4
        5: [2, 8],            # OD_1_0
        6: [1, 5, 7],         # OD_1_4
        7: [5],               # OD_2_3
        8: [3, 5, 8],         # OD_4_3
        9: [3, 5],            # OD_4_0
    }

    # Transfer station: station -> list of lines passing through it
    station_lines = {
        0: [3, 4, 5, 7, 8],
        1: [1, 4],
        2: [1, 6],
        3: [],
        4: [0, 3, 4],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: whether line i is selected
    x = model.addVars(lines, vtype=GRB.BINARY, name="x")
    # Continuous: frequency of line i
    f = model.addVars(lines, lb=0.0, name="f")
    # Continuous: unmet demand for each OD pair (by index)
    u = model.addVars(od_indices, lb=0.0, name="u")
    # Binary: transfer station designation
    t = model.addVars([0, 1, 2, 3, 4], vtype=GRB.BINARY, name="t")

    # Objective: fixed costs + operational costs + penalty costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * x[i] for i in lines) +
        gp.quicksum(operational_cost[i] * f[i] for i in lines) +
        gp.quicksum(penalty_cost[k] * u[k] for k in od_indices),
        GRB.MINIMIZE
    )

    # Frequency bounds: f[i] in [min_frequency * x[i], max_frequency * x[i]]
    for i in lines:
        model.addConstr(f[i] >= min_frequency * x[i], name=f"freq_min_{i}")
        model.addConstr(f[i] <= max_frequency * x[i], name=f"freq_max_{i}")

    # Demand coverage: sum of frequencies of serving lines + unmet >= demand
    for k in od_indices:
        model.addConstr(
            gp.quicksum(f[i] for i in od_lines[k]) + u[k] >= demand[k],
            name=f"demand_{k}"
        )

    # Vehicle limit
    model.addConstr(
        gp.quicksum(vehicle_usage_per_frequency[i] * f[i] for i in lines) <= total_vehicle_limit,
        name="vehicle_limit"
    )

    # Transfer station: t[s] = 1 only if at least 2 lines from station_lines[s] are selected
    for s, sl in station_lines.items():
        if len(sl) < 2:
            model.addConstr(t[s] == 0, name=f"no_transfer_{s}")
        else:
            model.addConstr(
                2 * t[s] <= gp.quicksum(x[i] for i in sl),
                name=f"transfer_min2_{s}"
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
        return {"objective": None, "status": f"solver_status_{status}"}