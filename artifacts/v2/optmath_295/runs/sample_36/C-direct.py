import gurobipy as gp
from gurobipy import GRB
import random

def solve(params):
    total_capacity = params["total_capacity"]
    project_demand = params["project_demand"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    assignment_limit_min = params["assignment_limit_min"]
    assignment_limit_max = params["assignment_limit_max"]

    num_persons = len(total_capacity)
    num_projects = len(project_demand)

    persons = range(num_persons)
    projects = range(num_projects)

    # Generate costs and limits deterministically from min/max bounds
    # Use a seeded random to produce fixed per-(person,project) values
    rng = random.Random(42)
    cost = {
        (i, j): rng.randint(int(cost_min), int(cost_max))
        for i in persons for j in projects
    }
    limit = {
        (i, j): rng.randint(int(assignment_limit_min), int(assignment_limit_max))
        for i in persons for j in projects
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units assigned from person i to project j
    x = model.addVars(persons, projects, lb=0.0, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in persons for j in projects),
        GRB.MINIMIZE
    )

    # Person capacity constraints: each person's total assignment equals their capacity
    for i in persons:
        model.addConstr(
            gp.quicksum(x[i, j] for j in projects) == total_capacity[i],
            name=f"cap_{i}"
        )

    # Project demand constraints: each project's total assignment meets demand
    for j in projects:
        model.addConstr(
            gp.quicksum(x[i, j] for i in persons) == project_demand[j],
            name=f"dem_{j}"
        )

    # Per-person, per-project assignment limit
    for i in persons:
        for j in projects:
            model.addConstr(x[i, j] <= limit[i, j], name=f"lim_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}