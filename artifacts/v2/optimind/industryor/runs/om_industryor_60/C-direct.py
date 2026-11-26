import gurobipy as gp

def solve(params):
    revenue = params["revenue"]  # dict with keys A, B, C, D
    cost = params["cost"]        # dict with keys A, B, C, D
    budget = params["budget"]    # scalar

    restaurants = ["A", "B", "C", "D"]

    model = gp.Model("zhang_restaurants")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: buy[r] = 1 if restaurant r is purchased
    buy = model.addVars(restaurants, vtype=gp.GRB.BINARY, name="buy")

    # Objective: maximize total annual revenue
    model.setObjective(
        gp.quicksum(revenue[r] * buy[r] for r in restaurants),
        gp.GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(cost[r] * buy[r] for r in restaurants) <= budget,
        name="budget"
    )

    # If D is purchased, A cannot be purchased
    model.addConstr(buy["D"] + buy["A"] <= 1, name="D_excludes_A")

    model.optimize()

    status = model.Status
    if status == gp.GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == gp.GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == gp.GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}