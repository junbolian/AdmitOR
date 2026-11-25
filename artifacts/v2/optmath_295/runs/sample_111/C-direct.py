import gurobipy as gp
from gurobipy import GRB

def solve(params):
    budget = params["budget"]
    population = params["population"]
    tower_cost = params["tower_cost"]

    # Coverage relationships: area -> list of towers that can cover it
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

    num_towers = 8
    num_areas = 11

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
            name=f"cover_ub_{a}"
        )
        # covered[a] >= build[t] for each t in towers (if any tower built, area can be covered)
        # Actually we want to allow covered[a]=1 only if some tower is built, and
        # since we maximize, the solver will set covered[a]=1 whenever possible.
        # The upper bound constraint is sufficient given maximization objective.

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