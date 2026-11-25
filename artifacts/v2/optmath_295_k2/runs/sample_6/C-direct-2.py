import gurobipy as gp
from gurobipy import GRB


def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    num_warehouses = len(warehouse_supply)
    num_stores = len(store_demand)

    model = gp.Model("transportation")
    model.modelSense = GRB.MINIMIZE

    # Decision variables: units shipped from warehouse i to store j.
    # Upper bound encodes the per-route capacity limit directly.
    x = {}
    for i in range(num_warehouses):
        for j in range(num_stores):
            x[i, j] = model.addVar(
                lb=0.0,
                ub=route_capacity[i][j],
                obj=transport_cost[i][j],
                name=f"ship_{i}_{j}",
            )

    # Supply constraints: each warehouse ships no more than its available goods.
    for i in range(num_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= warehouse_supply[i],
            name=f"supply_{i}",
        )

    # Demand constraints: each store receives exactly its required demand.
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_warehouses)) == store_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}

    return {"objective": None, "status": f"status_{model.status}"}