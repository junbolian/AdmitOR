import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_market0 = params["demand_market0"]  # list of 3 values
    demand_market1 = params["demand_market1"]  # list of 3 values

    profit_supplier0_market0 = params["profit_supplier0_market0"]
    profit_supplier0_market1 = params["profit_supplier0_market1"]
    profit_supplier1_market0 = params["profit_supplier1_market0"]
    profit_supplier1_market1 = params["profit_supplier1_market1"]
    profit_supplier2_market0 = params["profit_supplier2_market0"]
    profit_supplier2_market1 = params["profit_supplier2_market1"]

    # profit[s][m][p]
    profit = [
        [profit_supplier0_market0, profit_supplier0_market1],
        [profit_supplier1_market0, profit_supplier1_market1],
        [profit_supplier2_market0, profit_supplier2_market1],
    ]

    demand = [demand_market0, demand_market1]

    num_suppliers = 3
    num_markets = 2
    num_products = 3

    model = gp.Model("logistics")
    model.setParam("OutputFlag", 0)

    # x[s, m, p] = quantity supplied by supplier s to market m for product p
    x = model.addVars(num_suppliers, num_markets, num_products, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit[s][m][p] * x[s, m, p]
            for s in range(num_suppliers)
            for m in range(num_markets)
            for p in range(num_products)
        ),
        GRB.MAXIMIZE
    )

    # Demand constraints: for each market m and product p,
    # sum over suppliers must exactly equal demand
    for m in range(num_markets):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[s, m, p] for s in range(num_suppliers)) == demand[m][p],
                name=f"demand_m{m}_p{p}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}