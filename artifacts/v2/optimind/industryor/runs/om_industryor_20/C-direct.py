import gurobipy as gp
from gurobipy import GRB

def solve(params):
    days = params["days"]
    max_demand = params["max_demand"]      # list of 3
    price = params["price"]                # list of 3
    cost = params["cost"]                  # list of 3
    quota = params["quota"]                # list of 3
    activation_cost = params["activation_cost"]  # list of 3
    min_batch = params["min_batch"]        # list of 3

    n_products = 3
    products = range(n_products)

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # x[i]: total units produced of product i (continuous)
    x = model.addVars(n_products, lb=0.0, name="x")

    # y[i]: binary, 1 if product i is activated (produced at all)
    y = model.addVars(n_products, vtype=GRB.BINARY, name="y")

    # d[i]: days allocated to product i
    d = model.addVars(n_products, lb=0.0, name="d")

    # Objective: maximize total profit (revenue - production cost - activation cost)
    model.setObjective(
        gp.quicksum(
            (price[i] - cost[i]) * x[i] - activation_cost[i] * y[i]
            for i in products
        ),
        GRB.MAXIMIZE
    )

    # Total days constraint
    model.addConstr(gp.quicksum(d[i] for i in products) <= days, name="total_days")

    for i in products:
        # Production cannot exceed demand
        model.addConstr(x[i] <= max_demand[i], name=f"demand_{i}")

        # Production limited by days allocated and quota
        model.addConstr(x[i] <= quota[i] * d[i], name=f"quota_{i}")

        # Days allocated only if activated
        model.addConstr(d[i] <= days * y[i], name=f"days_activate_{i}")

        # If activated, must produce at least min_batch
        model.addConstr(x[i] >= min_batch[i] * y[i], name=f"min_batch_{i}")

        # If not activated, production is zero
        model.addConstr(x[i] <= max_demand[i] * y[i], name=f"zero_if_inactive_{i}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}