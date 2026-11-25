import gurobipy as gp
from gurobipy import GRB

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    # Coverage map: region -> list of towers that can cover it
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

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variables: x[j] = 1 if tower j is built, y[i] = 1 if region i is covered
    x = model.addVars(num_towers, vtype=GRB.BINARY, name="x")
    y = model.addVars(num_regions, vtype=GRB.BINARY, name="y")

    # Objective: maximize total population covered
    model.setObjective(
        gp.quicksum(population[i] * y[i] for i in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(tower_cost[j] * x[j] for j in range(num_towers)) <= budget,
        name="budget"
    )

    # Coverage constraints: region i can only be covered if at least one of its towers is built
    for i in range(num_regions):
        towers = coverage[i]
        model.addConstr(
            y[i] <= gp.quicksum(x[j] for j in towers),
            name=f"cover_{i}"
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