import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n_origins = len(supply)
    n_dest = len(demand)

    if n_origins == 0 or n_dest == 0:
        return {"objective": None, "status": "empty data"}

    # Cost matrix must be origin-major: cost_matrix[i][j] from origin i to dest j
    if len(cost_matrix) != n_origins:
        return {"objective": None, "status": "cost_matrix shape mismatch"}
    for row in cost_matrix:
        if len(row) != n_dest:
            return {"objective": None, "status": "cost_matrix shape mismatch"}

    total_supply = sum(supply)
    total_demand = sum(demand)
    if abs(total_supply - total_demand) > 1e-6:
        return {"objective": None, "status": "unbalanced supply/demand"}

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_dest):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=GRB.INFINITY,
                obj=cost_matrix[i][j],
                name=f"x_{i}_{j}",
            )

    model.ModelSense = GRB.MINIMIZE

    # Supply constraints: sum over destinations equals supply[i]
    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_dest)) == supply[i],
            name=f"supply_{i}",
        )

    # Demand constraints: sum over origins equals demand[j]
    for j in range(n_dest):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}

    return {"objective": None, "status": f"solver status {model.status}"}