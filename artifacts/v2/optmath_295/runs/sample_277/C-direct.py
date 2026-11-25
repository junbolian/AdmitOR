import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["n_cities"])
    pos_min = params["position_min"]
    pos_max = params["position_max"]

    # Build distance dict from params
    dist = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i, j] = params[f"dist_{i}_{j}"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route selection variables x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in range(n) for j in range(n) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Position variables for MTZ subtour elimination
    u = model.addVars(n, lb=pos_min, ub=pos_max, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city has exactly one outgoing route
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1,
            name=f"out_{i}"
        )

    # Each city has exactly one incoming route
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"in_{j}"
        )

    # Fix city 0 at position 0
    model.addConstr(u[0] == 0, name="fix_pos_0")

    # MTZ subtour elimination constraints
    # For non-depot cities: if x[i,j]=1 then u[j] >= u[i] + 1
    big_m = pos_max - pos_min + 1
    for i in range(n):
        for j in range(1, n):  # j != 0 (depot)
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - big_m * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}