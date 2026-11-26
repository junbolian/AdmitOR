import gurobipy as gp
from gurobipy import GRB

def solve(params):
    mango_per_A = params["mango_per_A"]
    pineapple_per_A = params["pineapple_per_A"]
    strawberry_per_A = params["strawberry_per_A"]
    profit_A = params["profit_A"]

    mango_per_B = params["mango_per_B"]
    pineapple_per_B = params["pineapple_per_B"]
    strawberry_per_B = params["strawberry_per_B"]
    profit_B = params["profit_B"]

    mango_stock = params["mango_stock"]
    pineapple_stock = params["pineapple_stock"]
    strawberry_stock = params["strawberry_stock"]
    tol = params["completeness_tolerance"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x1")
    x2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x2")

    model.setObjective(profit_A * x1 + profit_B * x2, GRB.MAXIMIZE)

    # Mango completeness: |mango_per_A*x1 + mango_per_B*x2 - mango_stock| <= tol
    model.addConstr(mango_per_A * x1 + mango_per_B * x2 <= mango_stock + tol, "mango_upper")
    model.addConstr(mango_per_A * x1 + mango_per_B * x2 >= mango_stock - tol, "mango_lower")

    # Pineapple completeness
    model.addConstr(pineapple_per_A * x1 + pineapple_per_B * x2 <= pineapple_stock + tol, "pineapple_upper")
    model.addConstr(pineapple_per_A * x1 + pineapple_per_B * x2 >= pineapple_stock - tol, "pineapple_lower")

    # Strawberry completeness
    model.addConstr(strawberry_per_A * x1 + strawberry_per_B * x2 <= strawberry_stock + tol, "strawberry_upper")
    model.addConstr(strawberry_per_A * x1 + strawberry_per_B * x2 >= strawberry_stock - tol, "strawberry_lower")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}