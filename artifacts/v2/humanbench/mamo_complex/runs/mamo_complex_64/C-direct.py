import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    cities = [0, 1, 2, 3, 4]  # E=0, F=1, G=2, H=3, I=4
    n = len(cities)

    # Build symmetric cost matrix from params
    cost = {}
    cost[(0,1)] = cost[(1,0)] = params["cost_E_to_F"]
    cost[(0,2)] = cost[(2,0)] = params["cost_E_to_G"]
    cost[(0,3)] = cost[(3,0)] = params["cost_E_to_H"]
    cost[(0,4)] = cost[(4,0)] = params["cost_E_to_I"]
    cost[(1,2)] = cost[(2,1)] = params["cost_F_to_G"]
    cost[(1,3)] = cost[(3,1)] = params["cost_F_to_H"]
    cost[(1,4)] = cost[(4,1)] = params["cost_F_to_I"]
    cost[(2,3)] = cost[(3,2)] = params["cost_G_to_H"]
    cost[(2,4)] = cost[(4,2)] = params["cost_G_to_I"]
    cost[(3,4)] = cost[(4,3)] = params["cost_H_to_I"]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # Subtour elimination via MTZ
    u = model.addVars(cities, lb=0, ub=n - 1, vtype=GRB.INTEGER, name="u")

    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}