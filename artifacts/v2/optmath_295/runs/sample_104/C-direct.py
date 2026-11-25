import gurobipy as gp
from gurobipy import GRB

def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    num_regions = params["num_regions"]
    num_towers = params["num_towers"]

    # Coverage relationships: which towers can cover each region
    coverage = {
        0: [0, 3, 5, 7],
        1: [2, 6],
        2: [1, 3, 5],
        3: [0, 2, 5, 6, 7],
        4: [4, 6],
        5: [0, 1, 2, 5, 6],
        6: [1, 3, 4, 6],
        7: [0, 1, 6],
        8: [4, 5, 6, 7],
        9: [3, 4, 5, 6],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: build tower j or not
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")

    # Binary variable: region i is covered or not
    covered = model.addVars(num_regions, vtype=GRB.BINARY, name="covered")

    # Objective: maximize total population covered
    model.setObjective(
        gp.quicksum(populations[i] * covered[i] for i in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_costs[j] * build[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region i is covered only if at least one of its towers is built
    for i in range(num_regions):
        towers_for_region = coverage[i]
        # covered[i] can be 1 only if at least one covering tower is built
        model.addConstr(
            covered[i] <= gp.quicksum(build[j] for j in towers_for_region),
            name=f"coverage_ub_{i}"
        )
        # If all covering towers for region i are built, covered[i] should be allowed to be 1
        # (the objective maximization will drive covered[i] to 1 when possible)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}