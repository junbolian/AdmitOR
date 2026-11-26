import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A1 = params["profit_A1"]
    profit_A2 = params["profit_A2"]
    milk_supply = params["milk_supply"]
    labor_hours = params["labor_hours"]
    A1_per_barrel = params["A1_per_barrel"]
    A2_per_barrel = params["A2_per_barrel"]
    hours_per_barrel_A1 = params["hours_per_barrel_A1"]
    hours_per_barrel_A2 = params["hours_per_barrel_A2"]
    A1_capacity = params["A1_capacity"]

    model = gp.Model("dairy")
    model.setParam("OutputFlag", 0)

    # Decision variables: barrels of milk allocated to A1 and A2 production
    x1 = model.addVar(lb=0.0, name="x1")  # barrels used for A1
    x2 = model.addVar(lb=0.0, name="x2")  # barrels used for A2

    # Objective: maximize profit
    model.setObjective(
        profit_A1 * A1_per_barrel * x1 + profit_A2 * A2_per_barrel * x2,
        GRB.MAXIMIZE
    )

    # Milk supply constraint
    model.addConstr(x1 + x2 <= milk_supply, name="milk")

    # Labor hours constraint
    model.addConstr(
        hours_per_barrel_A1 * x1 + hours_per_barrel_A2 * x2 <= labor_hours,
        name="labor"
    )

    # Type A equipment capacity constraint (kg of A1 per day)
    model.addConstr(A1_per_barrel * x1 <= A1_capacity, name="A1_cap")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}