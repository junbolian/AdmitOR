import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_regions = 12
    num_towers = 9

    # Coverage map: which towers can cover each region
    coverage = {
        0:  [4, 6, 8],
        1:  [2, 5, 7],
        2:  [0, 3, 4, 5, 6, 7, 8],
        3:  [0, 2, 3, 7],
        4:  [0, 1, 4, 5, 7],
        5:  [1, 2],
        6:  [0, 1, 3, 4, 5, 6, 8],
        7:  [3, 4, 6, 8],
        8:  [1, 2, 3, 6, 8],
        9:  [1, 5, 8],
        10: [3, 5, 6],
        11: [0, 2, 3, 4, 5, 8],
    }

    model = gp.Model("cell_tower")
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    cover = model.addVars(num_regions, vtype=GRB.BINARY, name="cover")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[r] * cover[r] for r in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * build[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region r can be covered only if at least one covering tower is built
    for r in range(num_regions):
        towers = coverage[r]
        model.addConstr(
            cover[r] <= gp.quicksum(build[t] for t in towers),
            name=f"coverage_{r}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}