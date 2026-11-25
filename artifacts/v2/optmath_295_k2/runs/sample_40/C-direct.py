import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]        # demand[m][p]
    profit_c0 = params["profit_c0"]  # profit_c0[m][p]
    profit_c1 = params["profit_c1"]  # profit_c1[m][p]

    num_markets = 4
    num_products = 3
    markets = range(num_markets)
    products = range(num_products)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, m, p] = units supplied by company c to market m of product p
    x0 = model.addVars(markets, products, lb=0.0, name="x0")  # company 0
    x1 = model.addVars(markets, products, lb=0.0, name="x1")  # company 1

    # Objective: maximize total profit
    obj = gp.quicksum(
        profit_c0[m][p] * x0[m, p] + profit_c1[m][p] * x1[m, p]
        for m in markets for p in products
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    # Demand satisfaction constraints
    for m in markets:
        for p in products:
            model.addConstr(
                x0[m, p] + x1[m, p] == demand[m][p],
                name=f"demand_{m}_{p}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}