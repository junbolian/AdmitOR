import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    avail = params["avail"]
    time = params["time"]
    minProd = params["minProd"]
    maxProd = params["maxProd"]

    num_products = 6
    num_stages = 11

    # Normalize time into time[s][p] (stage-major order).
    if isinstance(time[0], (list, tuple)):
        time_mat = [list(time[s]) for s in range(num_stages)]
    else:
        time_mat = [
            [time[s * num_products + p] for p in range(num_products)]
            for s in range(num_stages)
        ]

    model = gp.Model("production")
    model.setParam("OutputFlag", 0)

    x = [
        model.addVar(lb=minProd[p], ub=maxProd[p], obj=profit[p], name=f"x_{p}")
        for p in range(num_products)
    ]
    model.modelSense = GRB.MAXIMIZE

    for s in range(num_stages):
        model.addConstr(
            gp.quicksum(time_mat[s][p] * x[p] for p in range(num_products)) <= avail[s],
            name=f"stage_{s}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}