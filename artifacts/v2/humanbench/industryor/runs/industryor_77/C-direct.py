import gurobipy as gp
from gurobipy import GRB

def solve(params):
    days = params["days"]
    max_demand = params["max_demand"]        # list of 3
    price = params["price"]                  # list of 3
    prod_cost = params["prod_cost"]          # list of 3
    quota = params["quota"]                  # list of 3
    activation_cost = params["activation_cost"]  # list of 3
    min_batch = params["min_batch"]          # list of 3

    products = range(3)

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # x[i]: total units (100 kg) of product i produced in the month
    x = model.addVars(products, lb=0.0, name="x")

    # y[i]: binary, 1 if production line i is activated
    y = model.addVars(products, vtype=GRB.BINARY, name="y")

    # Objective: maximize profit = revenue - production costs - activation costs
    model.setObjective(
        gp.quicksum((price[i] - prod_cost[i]) * x[i] for i in products)
        - gp.quicksum(activation_cost[i] * y[i] for i in products),
        GRB.MAXIMIZE
    )

    # Demand constraints
    for i in products:
        model.addConstr(x[i] <= max_demand[i], name=f"demand_{i}")

    # Production capacity: total units <= quota[i] * days * y[i]
    for i in products:
        model.addConstr(x[i] <= quota[i] * days * y[i], name=f"capacity_{i}")

    # Minimum batch size: if activated, must produce at least min_batch[i]
    for i in products:
        model.addConstr(x[i] >= min_batch[i] * y[i], name=f"min_batch_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}