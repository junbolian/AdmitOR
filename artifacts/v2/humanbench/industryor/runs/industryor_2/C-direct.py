import gurobipy as gp
from gurobipy import GRB

def solve(params):
    income = params["income"]   # list of annual incomes, indexed 0..3
    cost = params["cost"]       # list of purchase costs, indexed 0..3
    budget = params["budget"]   # total budget

    n = 4  # number of properties (structural constant)

    model = gp.Model("real_estate")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: buy[i] = 1 if property i is purchased
    buy = model.addVars(n, vtype=GRB.BINARY, name="buy")

    # Objective: maximize annual income
    model.setObjective(gp.quicksum(income[i] * buy[i] for i in range(n)), GRB.MAXIMIZE)

    # Budget constraint
    model.addConstr(gp.quicksum(cost[i] * buy[i] for i in range(n)) <= budget, name="budget")

    # If Property 4 (index 3) is purchased, Property 3 (index 2) cannot be purchased
    model.addConstr(buy[3] + buy[2] <= 1, name="exclusivity_3_4")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}