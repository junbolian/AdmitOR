import gurobipy as gp
from gurobipy import GRB


def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    num_warehouses = 5
    num_stores = 6

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_warehouses, num_stores, lb=0.0, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            transport_cost[i][j] * x[i, j]
            for i in range(num_warehouses)
            for j in range(num_stores)
        ),
        GRB.MINIMIZE,
    )

    # Supply constraints: each warehouse ships at most its available supply
    for i in range(num_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= warehouse_supply[i],
            name=f"supply_{i}",
        )

    # Demand constraints: each store receives exactly its required demand
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_warehouses)) == store_demand[j],
            name=f"demand_{j}",
        )

    # Route capacity constraints
    for i in range(num_warehouses):
        for j in range(num_stores):
            model.addConstr(
                x[i, j] <= route_capacity[i][j],
                name=f"cap_{i}_{j}",
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}