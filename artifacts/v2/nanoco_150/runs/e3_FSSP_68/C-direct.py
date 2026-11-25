import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    p = {}
    for i in range(3):
        for j in range(3):
            p[i, j] = params[f"p_{i}_{j}"]

    lots = [0, 1, 2]
    stations = [0, 1, 2]

    # Big-M for disjunctive constraints
    M = sum(p[i, j] for i in lots for j in stations) + 1000

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times: s[i, j] = start time of lot i on station j
    s = model.addVars(lots, stations, lb=0.0, name="s")

    # Makespan
    cmax = model.addVar(lb=0.0, name="cmax")

    # Objective: minimize makespan
    model.setObjective(cmax, GRB.MINIMIZE)

    # Makespan >= completion of every lot on station 2
    for i in lots:
        model.addConstr(cmax >= s[i, 2] + p[i, 2])

    # Technological order: each lot must finish on station j before starting station j+1
    for i in lots:
        for j in range(2):
            model.addConstr(s[i, j + 1] >= s[i, j] + p[i, j])

    # Machine capacity: on each station, no two lots overlap
    # Binary y[i, k, j] = 1 if lot i precedes lot k on station j
    y = model.addVars(lots, lots, stations, vtype=GRB.BINARY, name="y")

    for j in stations:
        for i in lots:
            for k in lots:
                if i != k:
                    # Either i before k or k before i (enforced by pair constraints below)
                    model.addConstr(s[i, j] + p[i, j] <= s[k, j] + M * (1 - y[i, k, j]))

        for i in lots:
            for k in lots:
                if i < k:
                    # Exactly one of the two orderings must hold
                    model.addConstr(y[i, k, j] + y[k, i, j] == 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}