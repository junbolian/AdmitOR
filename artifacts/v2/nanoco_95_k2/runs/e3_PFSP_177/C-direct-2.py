import gurobipy as gp
from gurobipy import GRB


def solve(params):
    p = params["proc_time"]  # rows = batches (B0..B3), cols = units (U0,U1,U2)

    n_batches = len(p)
    n_units = len(p[0]) if n_batches > 0 else 0

    model = gp.Model("pfsp")
    model.Params.OutputFlag = 0

    # Start time S[i,u] of batch i on unit u
    S = {}
    for i in range(n_batches):
        for u in range(n_units):
            S[i, u] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"S_{i}_{u}")

    # Ordering binary: y[i,j]=1 means batch i precedes batch j (i<j), common across all units
    y = {}
    for i in range(n_batches):
        for j in range(i + 1, n_batches):
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    # Campaign start / end markers
    t_start = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="t_start")
    t_end = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="t_end")
    makespan = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="makespan")

    # Big-M: total processing time across all batches/units is a safe upper bound
    M = sum(p[i][u] for i in range(n_batches) for u in range(n_units)) + 1.0

    # Each batch must complete a unit before starting the next unit
    for i in range(n_batches):
        for u in range(n_units - 1):
            model.addConstr(S[i, u + 1] >= S[i, u] + p[i][u], name=f"route_{i}_{u}")

    # Disjunctive constraints on each unit using the common sequence y[i,j]
    for u in range(n_units):
        for i in range(n_batches):
            for j in range(i + 1, n_batches):
                # If y[i,j]=1: i before j on this unit
                model.addConstr(
                    S[j, u] >= S[i, u] + p[i][u] - M * (1 - y[i, j]),
                    name=f"order_{i}_{j}_{u}_a",
                )
                # If y[i,j]=0: j before i on this unit
                model.addConstr(
                    S[i, u] >= S[j, u] + p[j][u] - M * y[i, j],
                    name=f"order_{i}_{j}_{u}_b",
                )

    # Campaign window
    for i in range(n_batches):
        model.addConstr(t_start <= S[i, 0], name=f"start_lb_{i}")
        model.addConstr(t_end >= S[i, n_units - 1] + p[i][n_units - 1], name=f"end_ub_{i}")
    model.addConstr(makespan == t_end - t_start, name="makespan_def")

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}