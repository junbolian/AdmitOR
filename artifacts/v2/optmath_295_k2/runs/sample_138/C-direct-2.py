import gurobipy as gp
from gurobipy import GRB


def solve(params):
    net_demand = params["net_demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_cities = 6

    # Map each directed pair (i, j), i != j, to its index within source row i.
    # For source city i the 5 destinations are 0..5 with i skipped, in order.
    route_idx = {}
    for i in range(n_cities):
        k = 0
        for j in range(n_cities):
            if j == i:
                continue
            route_idx[(i, j)] = k
            k += 1

    model = gp.Model("transportation")
    model.modelSense = GRB.MINIMIZE

    # Decision variables x[i, j]: flow from city i to city j.
    # Capacity bound folded into the variable upper bound.
    x = {}
    for i in range(n_cities):
        for j in range(n_cities):
            if i == j:
                continue
            ridx = route_idx[(i, j)]
            x[i, j] = model.addVar(
                lb=0.0,
                ub=capacity[i][ridx],
                obj=cost[i][ridx],
                name=f"x_{i}_{j}",
            )

    # Flow balance: inflow - outflow = net_demand[i].
    # Positive net_demand => net consumer; negative => net supplier.
    for i in range(n_cities):
        flow_in = gp.quicksum(x[j, i] for j in range(n_cities) if j != i)
        flow_out = gp.quicksum(x[i, j] for j in range(n_cities) if j != i)
        model.addConstr(flow_in - flow_out == net_demand[i], name=f"balance_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}