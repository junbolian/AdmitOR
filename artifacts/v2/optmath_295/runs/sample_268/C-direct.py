import gurobipy as gp
from gurobipy import GRB

def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    shipping_cost = params["shipping_cost"]
    route_capacity = params["route_capacity"]

    # Support both dict and list inputs
    if isinstance(warehouse_supply, dict):
        origins = list(warehouse_supply.keys())
        supply = warehouse_supply
    else:
        origins = [f"origin_{i}" for i in range(len(warehouse_supply))]
        supply = {origins[i]: warehouse_supply[i] for i in range(len(origins))}

    if isinstance(store_demand, dict):
        destinations = list(store_demand.keys())
        demand = store_demand
    else:
        destinations = [f"destination_{j}" for j in range(len(store_demand))]
        demand = {destinations[j]: store_demand[j] for j in range(len(destinations))}

    # Normalize shipping_cost to dict-of-dict
    if isinstance(shipping_cost, list):
        cost = {
            origins[i]: {destinations[j]: shipping_cost[i][j] for j in range(len(destinations))}
            for i in range(len(origins))
        }
    else:
        cost = shipping_cost

    # Normalize route_capacity to dict-of-dict
    if isinstance(route_capacity, list):
        cap = {
            origins[i]: {destinations[j]: route_capacity[i][j] for j in range(len(destinations))}
            for i in range(len(origins))
        }
    else:
        cap = route_capacity

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = {
        (i, j): model.addVar(lb=0.0, ub=cap[i][j], name=f"x_{i}_{j}")
        for i in origins
        for j in destinations
    }

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE
    )

    for i in origins:
        model.addConstr(
            gp.quicksum(x[i, j] for j in destinations) == supply[i],
            name=f"supply_{i}"
        )

    for j in destinations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in origins) == demand[j],
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