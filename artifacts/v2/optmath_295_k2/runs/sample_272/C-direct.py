import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    # Coverage mapping: area -> list of towers that can cover it
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

    model = gp.Model("cell_tower_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    cover = model.addVars(num_areas, vtype=GRB.BINARY, name="cover")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[a] * cover[a] for a in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * build[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area a can only be covered if at least one of its towers is built
    for a in range(num_areas):
        towers_for_area = coverage[a]
        # cover[a] <= sum of build[t] for t in towers_for_area
        model.addConstr(
            cover[a] <= gp.quicksum(build[t] for t in towers_for_area),
            name=f"coverage_{a}"
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