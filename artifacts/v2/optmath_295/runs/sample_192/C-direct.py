import gurobipy as gp
from gurobipy import GRB

def solve(params):
    early_penalty = params["early_penalty"]
    late_penalty = params["late_penalty"]
    earliest_landing = params["earliest_landing"]
    latest_landing = params["latest_landing"]
    target_landing = params["target_landing"]
    separation = params["separation_i_before_j"]

    n = len(earliest_landing)
    aircraft = list(range(n))

    model = gp.Model("aircraft_landing")
    model.Params.OutputFlag = 0

    L = model.addVars(aircraft, lb=0.0, vtype=GRB.CONTINUOUS, name="L")
    E = model.addVars(aircraft, lb=0.0, vtype=GRB.CONTINUOUS, name="E")
    Tard = model.addVars(aircraft, lb=0.0, vtype=GRB.CONTINUOUS, name="Tard")

    y = {}
    for i in aircraft:
        for j in aircraft:
            if i != j:
                y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    # separation may be a dict keyed by (i,j) or a list of lists
    def get_sep(i, j):
        if isinstance(separation, dict):
            return separation[(i, j)]
        return separation[i][j]

    max_sep = max(get_sep(i, j) for i in aircraft for j in aircraft if i != j)
    M = max(latest_landing) + max_sep

    for i in aircraft:
        model.addConstr(L[i] >= earliest_landing[i], name=f"earliest_{i}")
        model.addConstr(L[i] <= latest_landing[i], name=f"latest_{i}")

    for i in aircraft:
        model.addConstr(E[i] >= target_landing[i] - L[i], name=f"early_def_{i}")
        model.addConstr(Tard[i] >= L[i] - target_landing[i], name=f"tard_def_{i}")

    for i in aircraft:
        for j in aircraft:
            if i < j:
                model.addConstr(y[i, j] + y[j, i] == 1, name=f"order_{i}_{j}")

    for i in aircraft:
        for j in aircraft:
            if i != j:
                model.addConstr(
                    L[j] >= L[i] + get_sep(i, j) - M * (1 - y[i, j]),
                    name=f"sep_{i}_{j}",
                )

    model.setObjective(
        gp.quicksum(
            early_penalty[i] * E[i] + late_penalty[i] * Tard[i] for i in aircraft
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "not_optimal"}