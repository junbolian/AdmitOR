import gurobipy as gp
from gurobipy import GRB

def solve(params):
    shirts_available = params["shirts_available"]
    pants_available = params["pants_available"]
    shirts_per_A = params["shirts_per_A"]
    pants_per_A = params["pants_per_A"]
    price_A = params["price_A"]
    shirts_per_B = params["shirts_per_B"]
    pants_per_B = params["pants_per_B"]
    price_B = params["price_B"]
    min_A = params["min_A"]
    min_B = params["min_B"]

    model = gp.Model("clothing_packages")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of each package to sell
    x_A = model.addVar(lb=min_A, vtype=GRB.INTEGER, name="x_A")
    x_B = model.addVar(lb=min_B, vtype=GRB.INTEGER, name="x_B")

    # Objective: maximize revenue
    model.setObjective(price_A * x_A + price_B * x_B, GRB.MAXIMIZE)

    # Inventory constraints
    model.addConstr(shirts_per_A * x_A + shirts_per_B * x_B <= shirts_available, name="shirts_limit")
    model.addConstr(pants_per_A * x_A + pants_per_B * x_B <= pants_available, name="pants_limit")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}