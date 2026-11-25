import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    profit_margin = params["profit_margin"]

    S = 4  # suppliers
    P = 2  # products
    R = 5  # regions

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[s][p][r] = units supplied by supplier s of product p to region r
    x = [[[model.addVar(lb=0.0, name=f"x_{s}_{p}_{r}")
            for r in range(R)]
           for p in range(P)]
          for s in range(S)]

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            profit_margin[s][p][r] * x[s][p][r]
            for s in range(S)
            for p in range(P)
            for r in range(R)
        ),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    # demand is a flat product-major list: demand[p*R + r]
    for p in range(P):
        for r in range(R):
            model.addConstr(
                gp.quicksum(x[s][p][r] for s in range(S)) == demand[p * R + r],
                name=f"demand_{p}_{r}"
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