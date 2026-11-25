import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    coverage = params["coverage"]

    num_areas = 25
    num_towers = 18

    model = gp.Model("cell_tower_coverage")
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

    # Coverage constraints: area i can only be covered if at least one of its towers is built
    for i in range(num_areas):
        covering_towers = [j for j in range(num_towers) if coverage[i][j] == 1]
        if covering_towers:
            # covered[i] <= sum of build[j] for j in covering_towers
            model.addConstr(
                covered[i] <= gp.quicksum(build[j] for j in covering_towers),
                name=f"coverage_{i}"
            )
        else:
            # No tower can cover this area
            model.addConstr(covered[i] == 0, name=f"coverage_{i}_none")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}