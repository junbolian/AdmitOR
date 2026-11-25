import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply   = params["supply"]    # flat: index = i * num_products + p
    demand   = params["demand"]    # flat: index = j * num_products + p
    cost     = params["cost"]      # flat: index = i * num_destinations * num_products + j * num_products + p
    capacity = params["capacity"]  # flat: index = i * num_destinations + j

    num_origins      = 4
    num_destinations = 5
    num_products     = 2

    origins      = range(num_origins)
    destinations = range(num_destinations)
    products     = range(num_products)

    def get_supply(i, p):
        return supply[i * num_products + p]

    def get_demand(j, p):
        return demand[j * num_products + p]

    def get_cost(i, j, p):
        return cost[i * num_destinations * num_products + j * num_products + p]

    def get_capacity(i, j):
        return capacity[i * num_destinations + j]

    model = gp.Model("transport")
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(get_cost(i, j, p) * x[i, j, p]
                    for i in origins for j in destinations for p in products),
        GRB.MINIMIZE
    )

    for i in origins:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in destinations) == get_supply(i, p),
                name=f"supply_{i}_{p}"
            )

    for j in destinations:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in origins) == get_demand(j, p),
                name=f"demand_{j}_{p}"
            )

    for i in origins:
        for j in destinations:
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in products) <= get_capacity(i, j),
                name=f"capacity_{i}_{j}"
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