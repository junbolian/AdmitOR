import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    operational_cost = params["operational_cost"]
    penalty_cost = params["penalty_cost"]
    demand = params["demand"]
    min_frequency = params["min_frequency"]
    max_frequency = params["max_frequency"]
    vehicle_capacity = params["vehicle_capacity"]
    vehicle_usage = params["vehicle_usage"]

    n_lines = 9
    lines = list(range(n_lines))
    od_pairs = [
        "OD_3_2", "OD_2_0", "OD_0_1", "OD_1_3", "OD_3_4",
        "OD_1_0", "OD_1_4", "OD_2_3", "OD_4_3", "OD_4_0",
    ]
    stations = [0, 1, 2, 3, 4]

    # line_serves_od: od_pair -> list of line indices
    line_serves_od = {
        "OD_3_2": [0, 3, 4, 5, 6],
        "OD_2_0": [2, 7, 8],
        "OD_0_1": [0, 3, 5, 7],
        "OD_1_3": [8],
        "OD_3_4": [3, 6, 7, 8],
        "OD_1_0": [2, 8],
        "OD_1_4": [1, 5, 7],
        "OD_2_3": [5],
        "OD_4_3": [3, 5, 8],
        "OD_4_0": [3, 5],
    }

    # lines_through_station: station -> list of line indices
    lines_through_station = {
        0: [3, 4, 5, 7, 8],
        1: [1, 4],
        2: [1, 6],
        3: [],
        4: [0, 3, 4],
    }

    od_index = {od: i for i, od in enumerate(od_pairs)}

    model = gp.Model("transit_network")
    model.Params.OutputFlag = 0

    y = model.addVars(n_lines, vtype=GRB.BINARY, name="y")
    f = model.addVars(n_lines, vtype=GRB.CONTINUOUS, lb=0.0, name="f")
    u = model.addVars(len(od_pairs), vtype=GRB.CONTINUOUS, lb=0.0, name="u")
    t = model.addVars(len(stations), vtype=GRB.BINARY, name="t")

    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in lines)
        + gp.quicksum(operational_cost[i] * f[i] for i in lines)
        + gp.quicksum(penalty_cost[od_index[od]] * u[od_index[od]] for od in od_pairs),
        GRB.MINIMIZE,
    )

    for od in od_pairs:
        oi = od_index[od]
        model.addConstr(
            gp.quicksum(f[i] for i in line_serves_od[od]) + u[oi] >= demand[oi],
            name=f"demand_{od}",
        )

    for i in lines:
        model.addConstr(f[i] >= min_frequency * y[i], name=f"min_freq_{i}")
        model.addConstr(f[i] <= max_frequency * y[i], name=f"max_freq_{i}")

    model.addConstr(
        gp.quicksum(vehicle_usage[i] * f[i] for i in lines) <= vehicle_capacity,
        name="vehicle_capacity",
    )

    for s in stations:
        if s == 3:
            model.addConstr(t[s] == 0, name=f"no_transfer_{s}")
        else:
            model.addConstr(
                2 * t[s] <= gp.quicksum(y[i] for i in lines_through_station[s]),
                name=f"transfer_{s}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}