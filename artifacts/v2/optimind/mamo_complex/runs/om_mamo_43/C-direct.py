import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transfer_costs = params["transfer_costs"]

    n = len(supplies)

    def cost(i, j):
        # supports a 5x5 matrix (list of lists) or a dict keyed by (i, j)
        if isinstance(transfer_costs, dict):
            return transfer_costs[(i, j)]
        entry = transfer_costs[i][j]
        if entry is None:
            raise ValueError("missing cost entry for (%d, %d)" % (i, j))
        return entry

    model = gp.Model("medical_supply_distribution")
    x = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            x[i, j] = model.addVar(
                lb=0, ub=GRB.INFINITY, obj=cost(i, j),
                vtype=GRB.CONTINUOUS, name="x_%d_%d" % (i, j)
            )
    model.ModelSense = GRB.MINIMIZE

    for i in range(n):
        inflow = gp.quicksum(x[j, i] for j in range(n) if j != i)
        outflow = gp.quicksum(x[i, j] for j in range(n) if j != i)
        model.addConstr(
            supplies[i] - outflow + inflow >= demands[i],
            name="demand_%d" % i
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no optimal solution"}