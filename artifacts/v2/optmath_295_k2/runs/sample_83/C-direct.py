import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_areas = 24
    num_towers = 18

    # Coverage mapping: which towers can cover each area
    coverage = {
        0:  [1, 2, 8, 14, 15, 17],
        1:  [0, 3, 6, 7, 8, 9, 12],
        2:  [0, 1, 4, 5, 7, 10, 11, 12, 16],
        3:  [1, 2, 3, 5, 9, 12, 13, 15, 17],
        4:  [1, 2, 3, 7, 8, 10, 11, 16],
        5:  [1, 4, 5, 6, 8, 11, 12, 14, 16],
        6:  [0, 2, 3, 4, 5, 7, 10, 11, 13, 14, 16],
        7:  [1, 2, 4, 5, 7, 10, 11, 13, 14, 16, 17],
        8:  [2, 3, 10, 13, 14, 16],
        9:  [2, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 17],
        10: [0, 1, 5, 12, 16, 17],
        11: [2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 16, 17],
        12: [0, 1, 2, 7, 9, 10, 12, 14, 15, 17],
        13: [0, 1, 2, 3, 6, 10, 11, 14, 15, 16],
        14: [0, 2, 4, 7, 8, 10, 11, 14, 15, 16],
        15: [0, 1, 4, 5, 7, 10, 13, 15, 16, 17],
        16: [0, 3, 4, 8, 10, 12, 13, 14, 15],
        17: [3, 4, 5, 6, 8, 10, 12, 14],
        18: [7, 8, 9, 15],
        19: [0, 3, 6, 7, 8, 9, 13, 15, 17],
        20: [2, 4, 7, 8, 11, 12, 13, 14, 15, 16],
        21: [1, 5, 8, 10, 11, 12],
        22: [1, 2, 4, 6, 8, 12, 14, 16],
        23: [0, 1, 2, 5, 6, 10, 12, 13, 15, 16, 17],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    tower_built = model.addVars(num_towers, vtype=GRB.BINARY, name="tower")
    area_covered = model.addVars(num_areas, vtype=GRB.BINARY, name="area")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[a] * area_covered[a] for a in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * tower_built[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area can only be covered if at least one of its towers is built
    for a in range(num_areas):
        covering_towers = coverage[a]
        model.addConstr(
            area_covered[a] <= gp.quicksum(tower_built[t] for t in covering_towers),
            name=f"cover_{a}"
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