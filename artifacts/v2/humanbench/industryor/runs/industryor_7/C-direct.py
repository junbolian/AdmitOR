import gurobipy as gp
from gurobipy import GRB

def solve(params):
    income_A = params["income_A"]
    income_B = params["income_B"]
    income_C = params["income_C"]
    income_D = params["income_D"]
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    cost_D = params["cost_D"]
    budget = params["budget"]

    model = gp.Model("restaurant_selection")
    model.setParam("OutputFlag", 0)

    x_A = model.addVar(vtype=GRB.BINARY, name="x_A")
    x_B = model.addVar(vtype=GRB.BINARY, name="x_B")
    x_C = model.addVar(vtype=GRB.BINARY, name="x_C")
    x_D = model.addVar(vtype=GRB.BINARY, name="x_D")

    model.setObjective(
        income_A * x_A + income_B * x_B + income_C * x_C + income_D * x_D,
        GRB.MAXIMIZE
    )

    model.addConstr(
        cost_A * x_A + cost_B * x_B + cost_C * x_C + cost_D * x_D <= budget,
        name="budget_constraint"
    )

    model.addConstr(x_D + x_A <= 1, name="mutex_D_A")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}