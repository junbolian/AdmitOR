import gurobipy as gp
from gurobipy import GRB

def solve(params):
    target_times = params["target_times"]
    earliest_times = params["earliest_times"]
    latest_times = params["latest_times"]
    early_penalties = params["early_penalties"]
    late_penalties = params["late_penalties"]

    # Separation times: sep[i][j] = min separation if i lands before j
    # For symmetric pairs the problem states the same value both ways
    sep = {
        (0, 1): params["separation_0_1"],
        (1, 0): params["separation_0_1"],  # problem states symmetric for 0-1
        (0, 2): params["separation_0_2"],
        (2, 0): params["separation_0_2"],
        (0, 3): params["separation_0_3"],
        (3, 0): params["separation_0_3"],
        (1, 2): params["separation_1_2"],
        (2, 1): params["separation_1_2"],
        (1, 3): params["separation_1_3"],
        (3, 1): params["separation_1_3"],
        (2, 3): params["separation_2_3"],
        (3, 2): params["separation_2_3"],
    }

    n = 4
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    M = 1000  # big-M for ordering constraints

    model = gp.Model("aircraft_landing")
    model.setParam("OutputFlag", 0)

    # Landing times
    x = model.addVars(n, lb=0.0, name="x")

    # Early/late deviation variables
    e = model.addVars(n, lb=0.0, name="e")  # early deviation
    l = model.addVars(n, lb=0.0, name="l")  # late deviation

    # Binary ordering variable: z[i,j] = 1 if aircraft i lands before aircraft j
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Time window constraints
    for i in range(n):
        model.addConstr(x[i] >= earliest_times[i], name=f"earliest_{i}")
        model.addConstr(x[i] <= latest_times[i], name=f"latest_{i}")

    # Early/late penalty constraints
    for i in range(n):
        model.addConstr(e[i] >= target_times[i] - x[i], name=f"early_{i}")
        model.addConstr(l[i] >= x[i] - target_times[i], name=f"late_{i}")

    # Ordering and separation constraints
    for (i, j) in pairs:
        # z[i,j] = 1 => i lands before j: x[j] - x[i] >= sep[i,j]
        model.addConstr(
            x[j] - x[i] >= sep[(i, j)] - M * (1 - z[i, j]),
            name=f"sep_{i}_{j}_ij"
        )
        # z[i,j] = 0 => j lands before i: x[i] - x[j] >= sep[j,i]
        model.addConstr(
            x[i] - x[j] >= sep[(j, i)] - M * z[i, j],
            name=f"sep_{i}_{j}_ji"
        )

    # Objective: minimize total penalty
    obj = gp.quicksum(
        early_penalties[i] * e[i] + late_penalties[i] * l[i]
        for i in range(n)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}