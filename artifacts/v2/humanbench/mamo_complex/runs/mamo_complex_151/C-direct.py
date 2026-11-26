import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_E_to_F = params["cost_E_to_F"]
    cost_E_to_G = params["cost_E_to_G"]
    cost_E_to_H = params["cost_E_to_H"]
    cost_F_to_E = params["cost_F_to_E"]
    cost_F_to_G = params["cost_F_to_G"]
    cost_F_to_H = params["cost_F_to_H"]
    cost_G_to_E = params["cost_G_to_E"]
    cost_G_to_F = params["cost_G_to_F"]
    cost_G_to_H = params["cost_G_to_H"]
    cost_H_to_E = params["cost_H_to_E"]
    cost_H_to_F = params["cost_H_to_F"]
    cost_H_to_G = params["cost_H_to_G"]

    locations = [0, 1, 2, 3]  # 0=E, 1=F, 2=G, 3=H
    n = len(locations)

    cost = {
        (0, 1): cost_E_to_F,
        (0, 2): cost_E_to_G,
        (0, 3): cost_E_to_H,
        (1, 0): cost_F_to_E,
        (1, 2): cost_F_to_G,
        (1, 3): cost_F_to_H,
        (2, 0): cost_G_to_E,
        (2, 1): cost_G_to_F,
        (2, 3): cost_G_to_H,
        (3, 0): cost_H_to_E,
        (3, 1): cost_H_to_F,
        (3, 2): cost_H_to_G,
    }

    arcs = [(i, j) for i in locations for j in locations if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    u = model.addVars(locations, vtype=GRB.CONTINUOUS, name="u")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each location has exactly one outgoing arc
    for i in locations:
        model.addConstr(gp.quicksum(x[i, j] for j in locations if j != i) == 1)

    # Each location has exactly one incoming arc
    for j in locations:
        model.addConstr(gp.quicksum(x[i, j] for i in locations if i != j) == 1)

    # Miller-Tucker-Zemlin subtour elimination
    for i in locations[1:]:
        model.addConstr(u[i] >= 1)
        model.addConstr(u[i] <= n - 1)

    for i in locations[1:]:
        for j in locations[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}