import gurobipy as gp
from gurobipy import GRB


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    coverage = {
        0: [0, 3, 5, 6],
        1: [2, 3, 4, 6],
        2: [0, 1, 4, 5, 6],
        3: [0, 3, 4],
        4: [0, 3, 4],
        5: [1, 2, 3],
        6: [1, 2, 3, 4],
        7: [1, 2, 3, 4, 5, 6],
        8: [0, 1, 2, 4, 5],
        9: [1, 4, 6],
    }

    num_regions = len(population)
    num_towers = len(tower_cost)

    model = gp.Model("cell_tower_coverage")
    model.Params.OutputFlag = 0

    x = model.addVars(num_towers, vtype=GRB.BINARY, name="x")
    y = model.addVars(num_regions, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(population[r] * y[r] for r in range(num_regions)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(tower_cost[t] * x[t] for t in range(num_towers)) <= budget,
        name="budget",
    )

    for r in range(num_regions):
        model.addConstr(
            y[r] <= gp.quicksum(x[t] for t in coverage[r]),
            name=f"cover_{r}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible_or_failed"}