import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    avail = params["avail"]
    time_req = params["time"]
    min_prod = params["minProd"]
    max_prod = params["maxProd"]

    num_products = 6
    num_stages = 11

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(float(profit[j]) * x[j] for j in range(num_products)),
        GRB.MAXIMIZE
    )

    for s in range(num_stages):
        row = time_req[s] if hasattr(time_req[s], '__getitem__') else [
            time_req[s * num_products + j] for j in range(num_products)
        ]
        model.addConstr(
            gp.quicksum(float(row[j]) * x[j] for j in range(num_products))
            <= float(avail[s]),
            name=f"stage_{s}"
        )

    for j in range(num_products):
        model.addConstr(x[j] >= float(min_prod[j]), name=f"min_{j}")
        model.addConstr(x[j] <= float(max_prod[j]), name=f"max_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}