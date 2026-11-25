import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_regions = 10
    num_towers = 8

    # Structural coverage relationships: region i -> list of tower indices that can cover it
    coverage = [
        [0, 3, 5, 7],       # Region 0
        [2, 6],             # Region 1
        [1, 3, 5],          # Region 2
        [0, 2, 5, 6, 7],    # Region 3
        [4, 6],             # Region 4
        [0, 1, 2, 5, 6],    # Region 5
        [1, 3, 4, 6],       # Region 6
        [0, 1, 6],          # Region 7
        [4, 5, 6, 7],       # Region 8
        [3, 4, 5, 6],       # Region 9
    ]

    model = gp.Model("telecom_coverage")
    model.Params.OutputFlag = 0

    # x[j] = 1 if tower j is built, y[i] = 1 if region i is covered
    x = model.addVars(num_towers, vtype=GRB.BINARY, name="x")
    y = model.addVars(num_regions, vtype=GRB.BINARY, name="y")

    # Objective: maximize total population covered
    model.setObjective(
        gp.quicksum(population[i] * y[i] for i in range(num_regions)),
        GRB.MAXIMIZE,
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[j] * x[j] for j in range(num_towers)) <= budget,
        name="budget",
    )

    # Coverage linking and must-cover constraints
    for i in range(num_regions):
        towers_i = coverage[i]
        model.addConstr(
            y[i] <= gp.quicksum(x[j] for j in towers_i),
            name=f"link_{i}",
        )
        model.addConstr(
            gp.quicksum(x[j] for j in towers_i) >= 1,
            name=f"cover_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}