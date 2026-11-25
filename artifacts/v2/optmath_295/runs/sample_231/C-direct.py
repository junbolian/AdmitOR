import gurobipy as gp

def solve(params):
    costs = [
        params["cost_vehicle_1"],
        params["cost_vehicle_2"],
        params["cost_vehicle_3"],
        params["cost_vehicle_4"],
        params["cost_vehicle_5"],
    ]

    coverage = [
        (1, [4, 5]), (2, [4, 5]), (3, [3]), (4, [1, 2]), (5, [1, 2, 4]),
        (6, [1, 3, 4]), (7, [3, 4, 5]), (8, [3, 4]), (9, [1, 2, 3]), (10, [3, 4, 5]),
        (11, [3, 5]), (12, [1]), (13, [1, 4, 5]), (14, [3, 4]), (15, [1, 2, 5]),
        (16, [1, 2]), (17, [2]), (18, [5]), (19, [1, 4]), (20, [2]),
        (21, [3, 4, 5]), (22, [5]), (23, [1, 4]), (24, [2, 5]), (25, [1, 3, 5]),
        (26, [1, 2, 3]), (27, [5]), (28, [2, 4]), (29, [1, 3]), (30, [5]),
        (31, [1, 3]),
    ]

    model = gp.Model("vehicle_deployment")
    model.setParam("OutputFlag", 0)

    deploy = model.addVars(5, vtype=gp.GRB.BINARY, name="deploy")

    model.setObjective(
        gp.quicksum(costs[i] * deploy[i] for i in range(5)),
        gp.GRB.MINIMIZE,
    )

    for region_idx, vehicle_list in coverage:
        model.addConstr(
            gp.quicksum(deploy[v - 1] for v in vehicle_list) >= 1,
            name=f"cover_e{region_idx}",
        )

    model.optimize()

    if model.status == gp.GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == gp.GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "not_optimal"}