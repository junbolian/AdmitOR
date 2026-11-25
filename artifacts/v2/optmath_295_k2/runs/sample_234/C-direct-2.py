import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    coverage = params["coverage"]

    num_areas = len(population)
    num_towers = len(tower_cost)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    covered = model.addVars(num_areas, vtype=GRB.BINARY, name="covered")

    # Objective: maximize covered population
    model.setObjective(
        gp.quicksum(population[i] * covered[i] for i in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[j] * build[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area i is covered only if at least one covering tower is built
    for i in range(num_areas):
        covering_towers = [j for j in range(num_towers) if coverage[i][j] == 1]
        if len(covering_towers) == 0:
            # Area cannot be covered
            model.addConstr(covered[i] == 0, name=f"no_cover_{i}")
        else:
            # covered[i] <= sum of build[j] for j in covering_towers
            model.addConstr(
                covered[i] <= gp.quicksum(build[j] for j in covering_towers),
                name=f"cover_ub_{i}"
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