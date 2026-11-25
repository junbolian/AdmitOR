import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }
    pos1_lower = params["pos1_lower"]
    pos1_upper = params["pos1_upper"]
    pos2_lower = params["pos2_lower"]
    pos2_upper = params["pos2_upper"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables x[i,j] = 1 if route from i to j is taken
    x = {}
    for (i, j) in cost:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables for subtour elimination
    # City 0 is unrestricted (use large bounds)
    p0 = model.addVar(lb=-GRB.INFINITY, ub=GRB.INFINITY, name="p0")
    p1 = model.addVar(lb=pos1_lower, ub=pos1_upper, name="p1")
    p2 = model.addVar(lb=pos2_lower, ub=pos2_upper, name="p2")

    model.update()

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in cost),
        GRB.MINIMIZE
    )

    # Each city visited exactly once (in-flow = 1)
    model.addConstr(x[1, 0] + x[2, 0] == 1, name="visit_0")
    model.addConstr(x[0, 1] + x[2, 1] == 1, name="visit_1")
    model.addConstr(x[0, 2] + x[1, 2] == 1, name="visit_2")

    # Each city departed exactly once (out-flow = 1)
    model.addConstr(x[0, 1] + x[0, 2] == 1, name="depart_0")
    model.addConstr(x[1, 0] + x[1, 2] == 1, name="depart_1")
    model.addConstr(x[2, 0] + x[2, 1] == 1, name="depart_2")

    # Subtour elimination via position variables
    # Big-M for subtour constraints; positions are bounded in [0, 2]
    M = 3

    # If x[1,2] = 1 then p1 < p2, i.e. p1 - p2 <= -1 + M*(1 - x[1,2])
    model.addConstr(p1 - p2 <= -1 + M * (1 - x[1, 2]), name="subtour_12")

    # If x[2,1] = 1 then p2 < p1, i.e. p2 - p1 <= -1 + M*(1 - x[2,1])
    model.addConstr(p2 - p1 <= -1 + M * (1 - x[2, 1]), name="subtour_21")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}