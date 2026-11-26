import gurobipy as gp
from gurobipy import GRB


def solve(params):
    proc = params["processing_times"]
    n = len(proc)          # batches
    m = len(proc[0])       # vats

    positions = range(n)
    vats = range(m)

    model = gp.Model("dyeing_flowshop")
    model.Params.OutputFlag = 0

    # x[i,k] = 1 if batch i is scheduled in position k
    x = model.addVars(n, positions, vtype=GRB.BINARY, name="x")
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, k] for k in positions) == 1)
    for k in positions:
        model.addConstr(gp.quicksum(x[i, k] for i in range(n)) == 1)

    # t[k,j] = processing time on vat j of the batch in position k
    t = model.addVars(positions, vats, lb=0.0, name="t")
    for k in positions:
        for j in vats:
            model.addConstr(
                t[k, j] == gp.quicksum(proc[i][j] * x[i, k] for i in range(n))
            )

    # S[k,j] = start time on vat j of the batch in position k
    S = model.addVars(positions, vats, lb=0.0, name="S")

    for k in positions:
        for j in range(m - 1):
            # same batch: vat j+1 starts after finishing on vat j
            model.addConstr(S[k, j + 1] >= S[k, j] + t[k, j])
    for k in range(n - 1):
        for j in vats:
            # vat j processes next batch after current one
            model.addConstr(S[k + 1, j] >= S[k, j] + t[k, j])
            # next batch on vat j+1 waits for previous batch to leave vat j+1
            if j < m - 1:
                model.addConstr(S[k + 1, j + 1] >= S[k, j + 1] + t[k, j + 1])

    model.setObjective(S[n - 1, m - 1] + t[n - 1, m - 1], GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "not_optimal"}