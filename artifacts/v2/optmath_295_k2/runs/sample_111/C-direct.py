import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_towers = 8
    num_areas = 11

    # Coverage: area -> list of towers that cover it
    coverage = {
        0: [3],
        1: [0, 1, 2, 3, 7],
        2: [1, 2, 6],
        3: [0, 4, 5, 6],
        4: [3, 5],
        5: [3, 5],
        6: [0, 3, 4],
        7: [2, 3, 4, 5],
        8: [2, 4, 5],
        9: [2, 5],
        10: [1, 2, 3, 4, 5],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    covered = model.addVars(num_areas, vtype=GRB.BINARY, name="covered")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[a] * covered[a] for a in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[t] * build[t] for t in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area a is covered only if at least one covering tower is built
    for a in range(num_areas):
        towers = coverage[a]
        # covered[a] <= sum of build[t] for t in towers
        model.addConstr(
            covered[a] <= gp.quicksum(build[t] for t in towers),
            name=f"cov_upper_{a}"
        )
        # covered[a] >= build[t] for each t in towers (if any tower is built, area can be covered)
        # Actually we need: if covered[a]=1 then at least one tower in towers is built.
        # The upper bound above suffices since we maximize coverage population (positive).
        # covered[a] is free to be 1 only if some tower covers it, enforced by upper bound.

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}