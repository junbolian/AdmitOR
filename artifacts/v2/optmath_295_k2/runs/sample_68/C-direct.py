import gurobipy as gp
from gurobipy import GRB


def solve(params):
    costs = [
        params["cost_vehicle_1"],
        params["cost_vehicle_2"],
        params["cost_vehicle_3"],
        params["cost_vehicle_4"],
        params["cost_vehicle_5"],
        params["cost_vehicle_6"],
    ]

    # Structural coverage: route -> list of vehicle indices (1-based) that can cover it.
    coverage = {
        1: [6],
        2: [2, 4, 6],
        3: [1, 3, 4],
        4: [3],
        5: [1, 5, 6],
        6: [1, 4],
        7: [3, 5],
        8: [4],
        9: [3, 5, 6],
        10: [4, 5, 6],
        11: [3, 4],
        12: [1, 3, 5, 6],
        13: [3, 4, 6],
    }

    model = gp.Model("fleet_deployment")
    model.Params.OutputFlag = 0

    x = model.addVars(range(1, 7), vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(costs[i - 1] * x[i] for i in range(1, 7)),
        GRB.MINIMIZE,
    )

    for route, vehicles in coverage.items():
        model.addConstr(
            gp.quicksum(x[v] for v in vehicles) >= 1,
            name=f"route_{route}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "no_solution"}