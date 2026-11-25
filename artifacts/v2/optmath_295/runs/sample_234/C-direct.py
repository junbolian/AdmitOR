import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_areas = 25
    num_towers = 18

    # Coverage map: which towers can cover each area
    coverage = {
        0:  [1, 4, 7, 8, 9, 13, 15, 16],
        1:  [7, 9, 11, 12, 13, 14, 15, 16],
        2:  [1, 2, 4, 5, 7, 9, 10, 11, 14, 17],
        3:  [1, 3, 4, 7, 8, 13, 14, 17],
        4:  [5, 6, 7, 9, 10, 13, 16, 17],
        5:  [0, 1, 3, 4, 9, 10, 12, 14, 17],
        6:  [0, 3, 4, 5, 6, 9, 10, 12, 14, 15, 16, 17],
        7:  [3, 4, 5, 6, 7, 8, 11, 13, 14],
        8:  [0, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15],
        9:  [1, 2, 3, 4, 7, 8, 10, 11, 12, 15, 16, 17],
        10: [2, 8, 10, 15, 16],
        11: [0, 2, 3, 5, 12, 13, 14, 15, 17],
        12: [2, 4, 5, 7, 8, 10, 12, 14, 17],
        13: [2, 5, 7, 8, 9, 15, 16],
        14: [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 15],
        15: [0, 1, 3, 4, 6, 7, 8, 9, 10, 13, 15, 16, 17],
        16: [0, 2, 3, 4, 9, 10, 12, 13, 14, 17],
        17: [0, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15],
        18: [2, 4, 5, 7, 9, 10, 11, 12, 16, 17],
        19: [0, 2, 5, 6, 8, 9, 12, 13, 15, 16, 17],
        20: [1, 2, 4, 5, 8, 10, 13, 14, 16],
        21: [0, 1, 3, 4, 7, 10, 12, 14, 17],
        22: [4, 5, 7, 9, 11, 14, 15, 16],
        23: [4, 11, 14, 16],
        24: [9, 11, 17],
    }

    model = gp.Model("cell_tower_coverage")
    model.setParam("OutputFlag", 0)

    # Binary variables: build tower t or not
    tower_vars = model.addVars(num_towers, vtype=GRB.BINARY, name="tower")

    # Binary variables: area a is covered or not
    area_vars = model.addVars(num_areas, vtype=GRB.BINARY, name="area")

    # Objective: maximize total covered population
    model.setObjective(
        gp.quicksum(population[a] * area_vars[a] for a in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * tower_vars[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area a can only be covered if at least one of its towers is built
    for a in range(num_areas):
        covering_towers = coverage[a]
        # area_vars[a] <= sum of tower_vars for covering towers
        model.addConstr(
            area_vars[a] <= gp.quicksum(tower_vars[t] for t in covering_towers),
            name=f"coverage_{a}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}