import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    num_warehouses = len(supply)
    num_stores = len(demand)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from warehouse i to store j
    x = [[model.addVar(lb=0, name=f"x_{i}_{j}") for j in range(num_stores)]
         for i in range(num_warehouses)]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i][j]
                    for i in range(num_warehouses)
                    for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Supply constraints: each warehouse ships out all its stock
    for i in range(num_warehouses):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_stores)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: each store receives exactly what it needs
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_warehouses)) == demand[j],
            name=f"demand_{j}"
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