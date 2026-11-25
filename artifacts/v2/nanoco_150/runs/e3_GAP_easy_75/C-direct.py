import gurobipy as gp
from gurobipy import GRB

def solve(params):
    crew_capacities = params["crew_capacities"]
    fuel_costs = params["fuel_costs"]
    operating_costs = params["operating_costs"]

    num_crews = len(crew_capacities)
    num_zones = len(operating_costs[0])

    model = gp.Model("harvest_planning")

    x = {}
    for i in range(num_crews):
        for j in range(num_zones):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(
            operating_costs[i][j] * x[i, j]
            for i in range(num_crews)
            for j in range(num_zones)
        ),
        GRB.MINIMIZE,
    )

    for j in range(num_zones):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_crews)) == 1,
            name=f"assign_{j}",
        )

    for i in range(num_crews):
        model.addConstr(
            gp.quicksum(fuel_costs[i][j] * x[i, j] for j in range(num_zones))
            <= crew_capacities[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}