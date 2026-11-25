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

    # Binary variables: build tower j or not
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")

    # Binary variables: region i is covered or not
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
        towers = coverage[i]
        # covered[i] <= sum of build[j] for j in towers
        model.addConstr(
            covered[i] <= gp.quicksum(build[j] for j in towers),
            name=f"cover_ub_{i}"
        )
        # covered[i] >= build[j] for each j in towers (if any tower is built, region can be covered)
        # We don't force coverage — the maximization objective will drive covered[i] up naturally.
        # But we need to ensure covered[i] can only be 1 if a tower covers it.
        # The upper bound constraint above is sufficient given the maximization direction.

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