import gurobipy as gp
from gurobipy import GRB

def solve(params):
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    population = params["population"]

    num_towers = 9
    num_regions = 11

    # coverage[r] = list of towers that can cover region r
    coverage = {
        0:  [4, 5, 6, 8],
        1:  [1, 2, 3, 4, 5, 7],
        2:  [3, 5, 7],
        3:  [1, 3, 4, 5, 6],
        4:  [0, 3, 4, 7],
        5:  [5, 7, 8],
        6:  [1, 3, 6, 8],
        7:  [6, 7],
        8:  [3],
        9:  [0, 2, 3, 4, 5, 8],
        10: [1, 2, 4, 6, 7, 8],
    }

    # Normalize population: support both list and dict forms
    if isinstance(population, list):
        pop = {r: population[r] for r in range(num_regions)}
    else:
        pop = {r: population[f"region_{r}"] for r in range(num_regions)}

    # Normalize tower_cost: support both list and dict forms
    if isinstance(tower_cost, list):
        cost = {t: tower_cost[t] for t in range(num_towers)}
    else:
        cost = {t: tower_cost[f"tower_{t}"] for t in range(num_towers)}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    cover = model.addVars(num_regions, vtype=GRB.BINARY, name="cover")

    model.setObjective(
        gp.quicksum(pop[r] * cover[r] for r in range(num_regions)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(cost[t] * build[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    for r in range(num_regions):
        model.addConstr(
            cover[r] <= gp.quicksum(build[t] for t in coverage[r]),
            name=f"cover_region_{r}"
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