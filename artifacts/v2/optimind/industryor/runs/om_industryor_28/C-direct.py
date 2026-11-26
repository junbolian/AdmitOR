import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = len(params["price"])
    protein = params["protein_content"]
    minerals = params["minerals_content"]
    vitamins = params["vitamins_content"]
    price = params["price"]
    req_p = params["requirement_protein"]
    req_m = params["requirement_minerals"]
    req_v = params["requirement_vitamins"]

    model = gp.Model("feed")
    x = model.addVars(n, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(gp.quicksum(price[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    model.addConstr(
        gp.quicksum(protein[i] * x[i] for i in range(n)) >= req_p, "protein"
    )
    model.addConstr(
        gp.quicksum(minerals[i] * x[i] for i in range(n)) >= req_m, "minerals"
    )
    model.addConstr(
        gp.quicksum(vitamins[i] * x[i] for i in range(n)) >= req_v, "vitamins"
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "not_optimal"}