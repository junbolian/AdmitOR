import gurobipy as gp
from gurobipy import GRB, quicksum


def solve(params):
    n = int(params["num_cities"])
    num_route_vars = int(params["num_route_vars"])
    pos_ub = int(params["position_upper_bound"])
    city0_fixed = int(params["city0_position_fixed"])

    cities = list(range(n))
    arcs = [(i, j) for i in cities for j in cities if i != j]
    if len(arcs) != num_route_vars:
        return {"objective": None, "status": "num_route_vars mismatch"}

    cost = {(i, j): float(params[f"cost_{i}_{j}"]) for i, j in arcs}

    model = gp.Model("delivery_route")
    model.setParam("OutputFlag", 0)
    model.setParam("MIPGap", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="route")
    u = model.addVars(cities, vtype=GRB.INTEGER, lb=0, ub=pos_ub, name="position")

    model.addConstr(u[0] == city0_fixed, name="fix_city0_position")

    for i in cities:
        model.addConstr(quicksum(x[i, j] for j in cities if j != i) == 1, name=f"out_{i}")
        model.addConstr(quicksum(x[j, i] for j in cities if j != i) == 1, name=f"in_{i}")

    for i in cities:
        if i == 0:
            continue
        for j in cities:
            if j == 0 or j == i:
                continue
            model.addConstr(n * x[i, j] + u[i] - u[j] <= pos_ub, name=f"mtz_{i}_{j}")

    model.setObjective(quicksum(cost[i, j] * x[i, j] for i, j in arcs), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}