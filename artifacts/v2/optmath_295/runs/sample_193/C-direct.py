import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_flat = params["supply"]    # [4][2] row-major
    demand_flat = params["demand"]    # [5][2] row-major
    cost_flat   = params["cost"]      # [4][5][2] row-major
    cap_flat    = params["capacity"]  # [4][5] row-major

    n_origins      = 4
    n_destinations = 5
    n_products     = 2

    # Reshape inputs
    supply = [[supply_flat[i * n_products + k] for k in range(n_products)]
              for i in range(n_origins)]

    demand = [[demand_flat[j * n_products + k] for k in range(n_products)]
              for j in range(n_destinations)]

    cost = [[[cost_flat[i * n_destinations * n_products + j * n_products + k]
               for k in range(n_products)]
              for j in range(n_destinations)]
             for i in range(n_origins)]

    capacity = [[cap_flat[i * n_destinations + j]
                 for j in range(n_destinations)]
                for i in range(n_origins)]

    model = gp.Model("multi_commodity_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j][k] = units of product k from origin i to destination j
    x = [[[model.addVar(lb=0.0, name=f"x_{i}_{j}_{k}")
           for k in range(n_products)]
          for j in range(n_destinations)]
         for i in range(n_origins)]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            cost[i][j][k] * x[i][j][k]
            for i in range(n_origins)
            for j in range(n_destinations)
            for k in range(n_products)
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from origin i of product k == supply[i][k]
    for i in range(n_origins):
        for k in range(n_products):
            model.addConstr(
                gp.quicksum(x[i][j][k] for j in range(n_destinations)) == supply[i][k],
                name=f"supply_{i}_{k}"
            )

    # Demand constraints: total received at destination j of product k == demand[j][k]
    for j in range(n_destinations):
        for k in range(n_products):
            model.addConstr(
                gp.quicksum(x[i][j][k] for i in range(n_origins)) == demand[j][k],
                name=f"demand_{j}_{k}"
            )

    # Capacity constraints: total units (both products) on arc (i,j) <= capacity[i][j]
    for i in range(n_origins):
        for j in range(n_destinations):
            model.addConstr(
                gp.quicksum(x[i][j][k] for k in range(n_products)) <= capacity[i][j],
                name=f"cap_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}