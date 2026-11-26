import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_AB = params["cost_AB"]
    cost_AC = params["cost_AC"]
    cost_AD = params["cost_AD"]
    cost_BA = params["cost_BA"]
    cost_BC = params["cost_BC"]
    cost_BD = params["cost_BD"]
    cost_CA = params["cost_CA"]
    cost_CB = params["cost_CB"]
    cost_CD = params["cost_CD"]
    cost_DA = params["cost_DA"]
    cost_DB = params["cost_DB"]
    cost_DC = params["cost_DC"]

    cities = [0, 1, 2, 3]  # Alpha=0, Bravo=1, Charlie=2, Delta=3
    n = len(cities)

    cost = {
        (0, 1): cost_AB,
        (0, 2): cost_AC,
        (0, 3): cost_AD,
        (1, 0): cost_BA,
        (1, 2): cost_BC,
        (1, 3): cost_BD,
        (2, 0): cost_CA,
        (2, 1): cost_CB,
        (2, 3): cost_CD,
        (3, 0): cost_DA,
        (3, 1): cost_DB,
        (3, 2): cost_DC,
    }

    arcs = list(cost.keys())

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs), GRB.MINIMIZE)

    # Each city has exactly one outgoing arc
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for (ii, j) in arcs if ii == i) == 1, name=f"out_{i}")

    # Each city has exactly one incoming arc
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for (i, jj) in arcs if jj == j) == 1, name=f"in_{j}")

    # Subtour elimination via MTZ
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    for (i, j) in arcs:
        if i != 0 and j != 0:
            model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}