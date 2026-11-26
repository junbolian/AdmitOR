import gurobipy as gp
from gurobipy import GRB

def solve(params):
    income = params["income"]   # list of annual incomes per property
    cost = params["cost"]       # list of purchase costs per property
    budget = params["budget"]   # total budget

    n = len(income)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: buy property i or not
    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    # Maximize total annual income
    model.setObjective(gp.quicksum(income[i] * x[i] for i in range(n)), GRB.MAXIMIZE)

    # Budget constraint
    model.addConstr(gp.quicksum(cost[i] * x[i] for i in range(n)) <= budget, name="budget")

    # If Property 4 (index 3) is purchased, Property 3 (index 2) cannot be purchased
    # x[3] + x[2] <= 1
    model.addConstr(x[3] + x[2] <= 1, name="exclusivity")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}