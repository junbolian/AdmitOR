import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    # Coverage map: area -> list of towers that can cover it
    coverage = {
        0: [2, 4, 5, 6, 7],
        1: [0, 1, 6, 8],
        2: [1, 6, 8],
        3: [1, 2, 6, 7],
        4: [0, 2, 3, 6, 7, 8],
        5: [0, 1, 2, 6, 7],
        6: [0, 1, 2, 4],
        7: [1, 2, 4, 5, 6],
        8: [0, 1, 3, 4, 5, 8],
    }

    num_areas = 9
    num_towers = 9
    areas = range(num_areas)
    towers = range(num_towers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: build tower j
    build = model.addVars(towers, vtype=GRB.BINARY, name="build")
    # Binary: cover area i
    cover = model.addVars(areas, vtype=GRB.BINARY, name="cover")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[i] * cover[i] for i in areas),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[j] * build[j] for j in towers) <= budget,
        name="budget"
    )

    # Coverage constraints: area i can be covered only if at least one of its towers is built
    for i in areas:
        model.addConstr(
            cover[i] <= gp.quicksum(build[j] for j in coverage[i]),
            name=f"coverage_{i}"
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