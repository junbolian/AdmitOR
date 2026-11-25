import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_regions = 10
    num_towers = 8

    # Coverage: which towers can cover each region
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

    # Binary: build tower j
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    # Binary: region i is covered
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

    # Coverage linking: region i is covered only if at least one of its towers is built
    for i in range(num_regions):
        towers = coverage[i]
        # covered[i] <= sum of build[j] for j in towers[i]
        model.addConstr(
            covered[i] <= gp.quicksum(build[j] for j in towers),
            name=f"cover_ub_{i}"
        )
        # covered[i] >= build[j] for each j in towers[i]
        # (forces covered[i]=1 when any tower covering i is built, combined with maximization)
        for j in towers:
            model.addConstr(covered[i] >= build[j], name=f"cover_lb_{i}_{j}")

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