import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_towers = len(tower_cost)
    num_areas = len(population)

    coverage_by_area = [
        [3],
        [0, 1, 2, 3, 7],
        [1, 2, 6],
        [0, 4, 5, 6],
        [3, 5],
        [3, 5],
        [0, 3, 4],
        [2, 3, 4, 5],
        [2, 4, 5],
        [2, 5],
        [1, 2, 3, 4, 5],
    ]

    model = gp.Model("cell_tower_coverage")
    model.Params.OutputFlag = 0

    build = model.addVars(num_towers, vtype=GRB.BINARY, name="build")
    covered = model.addVars(num_areas, vtype=GRB.BINARY, name="covered")

    model.setObjective(
        gp.quicksum(population[j] * covered[j] for j in range(num_areas)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(tower_cost[i] * build[i] for i in range(num_towers)) <= budget,
        name="budget",
    )

    for j, tower_list in enumerate(coverage_by_area):
        if tower_list:
            model.addConstr(
                covered[j] <= gp.quicksum(build[i] for i in tower_list),
                name=f"coverage_{j}",
            )
        else:
            model.addConstr(covered[j] == 0, name=f"coverage_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}