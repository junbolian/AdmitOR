import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_areas = 22
    num_towers = 20

    # Coverage map: which towers can cover each area
    coverage = {
        0:  [0, 1, 4, 5, 6, 7, 11, 12, 14, 16, 18],
        1:  [0, 1, 4, 6, 7, 13, 14, 17],
        2:  [6, 7, 8, 11, 12, 14, 15, 16, 18],
        3:  [1, 2, 4, 5, 8, 9, 12, 13, 14, 17, 18, 19],
        4:  [0, 3, 9, 10, 11, 13, 14, 17, 18, 19],
        5:  [0, 1, 5, 8, 9, 11, 12, 13, 16, 17, 19],
        6:  [0, 2, 3, 4, 6, 7, 9, 14, 17, 19],
        7:  [0, 4, 5, 6, 10, 11, 14, 15, 18],
        8:  [0, 1, 7, 8, 9, 10, 11, 12, 16, 17, 18, 19],
        9:  [5, 10, 15],
        10: [0, 5, 7, 8, 9, 11, 13, 15, 16, 17, 19],
        11: [0, 1, 3, 6, 7, 8, 10, 12, 16, 17, 19],
        12: [1, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        13: [0, 2, 4, 5, 6, 7, 9, 13, 14, 15, 16, 19],
        14: [4, 5, 6, 8, 11, 14, 15],
        15: [0, 1, 2, 8, 10, 11, 17, 19],
        16: [0, 2, 3, 4, 8, 10, 11, 13, 14, 15, 16, 18],
        17: [0, 2, 3, 4, 5, 6, 7, 8, 11, 14, 17, 18, 19],
        18: [2, 5, 8, 11, 13, 15, 16, 18],
        19: [3, 5, 6, 7, 8, 10, 11, 12, 15, 16, 18, 19],
        20: [0, 4, 8, 9, 11, 14, 16, 18, 19],
        21: [0, 4, 5, 6, 7, 9, 10, 15, 17, 18, 19],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: build tower t or not
    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    # Binary variables: area a is covered or not
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

    # Coverage constraints: area a can only be covered if at least one of its towers is built
    for a in range(num_areas):
        towers_for_area = coverage[a]
        # covered[a] <= sum of build[t] for t in towers_for_area
        model.addConstr(
            covered[a] <= gp.quicksum(build[t] for t in towers_for_area),
            name=f"cover_ub_{a}"
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
        return {"objective": None, "status": f"solver_status_{status}"}