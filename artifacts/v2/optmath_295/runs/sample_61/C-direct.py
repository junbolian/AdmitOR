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

    # Binary: build tower j or not
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")

    # Binary: region i is covered or not
    covered = model.addVars(num_regions, vtype=GRB.BINARY, name="covered")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[i] * covered[i] for i in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[j] * build[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region i covered only if at least one covering tower is built
    for i in range(num_regions):
        towers_for_i = coverage[i]
        # covered[i] <= sum of build[j] for j in towers_for_i
        model.addConstr(
            covered[i] <= gp.quicksum(build[j] for j in towers_for_i),
            name=f"cover_ub_{i}"
        )
        # covered[i] can be forced to 1 only if at least one tower is built;
        # since we maximize, the solver will set covered[i]=1 when possible.
        # No lower-bound constraint needed: objective drives coverage up.

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}