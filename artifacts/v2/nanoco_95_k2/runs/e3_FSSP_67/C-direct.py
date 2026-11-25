import gurobipy as gp
from gurobipy import GRB


def solve(params):
    p = params["processing_time"]  # rows = batches, cols = stations
    n_batches = len(p)
    n_stations = len(p[0])

    model = gp.Model("flowshop")

    # Big-M: sum of all processing times is a valid upper bound on makespan.
    M = sum(p[i][j] for i in range(n_batches) for j in range(n_stations)) + 1.0

    # Completion time of batch i on station j.
    C = {}
    for i in range(n_batches):
        for j in range(n_stations):
            C[i, j] = model.addVar(lb=0.0, name=f"C_{i}_{j}")

    # Ordering variable: y[i,k,j] = 1 if batch i is processed before batch k on station j.
    y = {}
    for i in range(n_batches):
        for k in range(i + 1, n_batches):
            for j in range(n_stations):
                y[i, k, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}_{j}")

    # Makespan.
    Cmax = model.addVar(lb=0.0, name="Cmax")

    model.update()

    # First station: completion must be at least its own processing time.
    for i in range(n_batches):
        model.addConstr(C[i, 0] >= p[i][0])

    # Stage precedence within a batch: station j cannot start until station j-1 finishes.
    for i in range(n_batches):
        for j in range(1, n_stations):
            model.addConstr(C[i, j] >= C[i, j - 1] + p[i][j])

    # Disjunctive (machine capacity) constraints.
    for i in range(n_batches):
        for k in range(i + 1, n_batches):
            for j in range(n_stations):
                # If y=1, i precedes k on station j.
                model.addConstr(C[k, j] >= C[i, j] + p[k][j] - M * (1 - y[i, k, j]))
                # If y=0, k precedes i on station j.
                model.addConstr(C[i, j] >= C[k, j] + p[i][j] - M * y[i, k, j])

    # Makespan definition.
    for i in range(n_batches):
        model.addConstr(Cmax >= C[i, n_stations - 1])

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    return {"objective": None, "status": f"status_{model.status}"}