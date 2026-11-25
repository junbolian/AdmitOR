import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit_data = {
        0: params["profit_supplier0"],
        1: params["profit_supplier1"],
        2: params["profit_supplier2"],
        3: params["profit_supplier3"],
    }

    num_suppliers = 4
    num_regions = 5
    num_products = 2

    # profit[s][r][p] from row-major flat list (R0P0, R0P1, R1P0, R1P1, ...)
    profit = {}
    for s in range(num_suppliers):
        flat = profit_data[s]
        profit[s] = {}
        for r in range(num_regions):
            profit[s][r] = {}
            for p in range(num_products):
                profit[s][r][p] = flat[r * num_products + p]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[s, r, p] = units supplied by supplier s to region r for product p
    x = model.addVars(num_suppliers, num_regions, num_products, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit[s][r][p] * x[s, r, p]
            for s in range(num_suppliers)
            for r in range(num_regions)
            for p in range(num_products)
        ),
        GRB.MAXIMIZE,
    )

    # Demand satisfaction: sum over suppliers == demand[r * num_products + p]
    for r in range(num_regions):
        for p in range(num_products):
            rhs = demand[r * num_products + p]
            model.addConstr(
                gp.quicksum(x[s, r, p] for s in range(num_suppliers)) == rhs,
                name=f"demand_r{r}_p{p}",
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
        return {"objective": None, "status": f"gurobi_status_{status}"}