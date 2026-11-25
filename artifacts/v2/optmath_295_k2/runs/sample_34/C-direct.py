import gurobipy as gp
from gurobipy import GRB

def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    coverage_links = params["coverage_links"]
    num_areas = params["num_areas"]
    num_towers = params["num_towers"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    covered = model.addVars(num_areas, vtype=GRB.BINARY, name="covered")

    # Objective: maximize population covered
    model.setObjective(
        gp.quicksum(populations[i] * covered[i] for i in range(num_areas)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_costs[j] * build[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: area i can only be covered if at least one covering tower is built
    for i in range(num_areas):
        covering_towers = [j for j in range(num_towers) if coverage_links[i][j] == 1]
        if not covering_towers:
            # Area has no covering towers; force it uncovered
            model.addConstr(covered[i] == 0, name=f"no_cover_{i}")
        else:
            # covered[i] <= sum of build[j] for j in covering_towers
            model.addConstr(
                covered[i] <= gp.quicksum(build[j] for j in covering_towers),
                name=f"cover_ub_{i}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}