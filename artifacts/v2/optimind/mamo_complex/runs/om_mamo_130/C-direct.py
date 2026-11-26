import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    mango_per_A = params["mango_per_A"]
    pineapple_per_A = params["pineapple_per_A"]
    strawberry_per_A = params["strawberry_per_A"]
    mango_per_B = params["mango_per_B"]
    pineapple_per_B = params["pineapple_per_B"]
    strawberry_per_B = params["strawberry_per_B"]
    mango_stock = params["mango_stock"]
    pineapple_stock = params["pineapple_stock"]
    strawberry_stock = params["strawberry_stock"]
    slack_tolerance = params["slack_tolerance"]

    model = gp.Model("fruit_salad")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x1")
    x2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x2")

    model.setObjective(profit_A * x1 + profit_B * x2, GRB.MAXIMIZE)

    # Mango usage must be within slack_tolerance of mango_stock
    model.addConstr(mango_per_A * x1 + mango_per_B * x2 >= mango_stock - slack_tolerance, "mango_lb")
    model.addConstr(mango_per_A * x1 + mango_per_B * x2 <= mango_stock + slack_tolerance, "mango_ub")

    # Pineapple usage
    model.addConstr(pineapple_per_A * x1 + pineapple_per_B * x2 >= pineapple_stock - slack_tolerance, "pineapple_lb")
    model.addConstr(pineapple_per_A * x1 + pineapple_per_B * x2 <= pineapple_stock + slack_tolerance, "pineapple_ub")

    # Strawberry usage
    model.addConstr(strawberry_per_A * x1 + strawberry_per_B * x2 >= strawberry_stock - slack_tolerance, "strawberry_lb")
    model.addConstr(strawberry_per_A * x1 + strawberry_per_B * x2 <= strawberry_stock + slack_tolerance, "strawberry_ub")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}