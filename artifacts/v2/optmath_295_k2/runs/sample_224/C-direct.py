import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    pos_lb = params["pos_lower_bound"]
    pos_ub = params["pos_upper_bound"]
    pos_0_fixed = params["pos_0_fixed"]
    sep_min = params["subtour_separation_min"]

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    pos = {}
    for i in cities:
        pos[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=pos_lb, ub=pos_ub, name=f"pos_{i}")

    model.addConstr(pos[0] == pos_0_fixed, name="fix_pos_0")

    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"out_{i}")
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"in_{j}")

    M = pos_ub - pos_lb + sep_min
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    pos[i] - pos[j] <= -sep_min + M * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}",
                )

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "no_solution"}