import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_regions = 11
    num_towers = 7

    # Coverage map: which towers can cover each region
    coverage = {
        0: [1, 2, 4, 5, 6],
        1: [0, 1, 3, 6],
        2: [0, 1, 2, 4],
        3: [0, 1, 2, 3, 5],
        4: [0, 1, 2, 3, 5],
        5: [0, 1, 2, 6],
        6: [3],
        7: [3, 4, 6],
        8: [0, 2],
        9: [1, 3, 4, 5],
        10: [1, 3, 5, 6],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: build tower t or not
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")

    # Binary variables: region r is covered or not
    covered = model.addVars(num_regions, vtype=GRB.BINARY, name="covered")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[r] * covered[r] for r in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * build[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region r can only be covered if at least one covering tower is built
    for r in range(num_regions):
        towers = coverage[r]
        # covered[r] <= sum of build[t] for t in towers
        model.addConstr(
            covered[r] <= gp.quicksum(build[t] for t in towers),
            name=f"coverage_{r}"
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