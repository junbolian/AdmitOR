import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_1_2 = params["cost_1_2"]
    cost_1_3 = params["cost_1_3"]
    cost_1_4 = params["cost_1_4"]
    cost_2_1 = params["cost_2_1"]
    cost_2_3 = params["cost_2_3"]
    cost_2_4 = params["cost_2_4"]
    cost_3_1 = params["cost_3_1"]
    cost_3_2 = params["cost_3_2"]
    cost_3_4 = params["cost_3_4"]
    cost_4_1 = params["cost_4_1"]
    cost_4_2 = params["cost_4_2"]
    cost_4_3 = params["cost_4_3"]
    n = int(params["num_cities"])

    cities = list(range(1, n + 1))

    cost = {}
    cost[(1, 2)] = cost_1_2
    cost[(1, 3)] = cost_1_3
    cost[(1, 4)] = cost_1_4
    cost[(2, 1)] = cost_2_1
    cost[(2, 3)] = cost_2_3
    cost[(2, 4)] = cost_2_4
    cost[(3, 1)] = cost_3_1
    cost[(3, 2)] = cost_3_2
    cost[(3, 4)] = cost_3_4
    cost[(4, 1)] = cost_4_1
    cost[(4, 2)] = cost_4_2
    cost[(4, 3)] = cost_4_3

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Subtour elimination via MTZ
    u = model.addVars(cities, lb=0.0, ub=n - 1.0, vtype=GRB.CONTINUOUS, name="u")

    for i in cities:
        for j in cities:
            if i != j and j != 1 and i != 1:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )
            elif i != j and j != 1 and i == 1:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
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