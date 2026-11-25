import gurobipy as gp
from gurobipy import GRB

def solve(params):
    travel_time = params["travel_time"]
    tw_earliest = [params[f"tw_{i}_earliest"] for i in range(8)]
    tw_latest = [params[f"tw_{i}_latest"] for i in range(8)]
    service_time = params["service_time"]
    max_shelf_life_window = params["max_shelf_life_window"]

    N = 8
    stores = list(range(1, N))

    max_tt = max(travel_time[i][j] for i in range(N) for j in range(N))
    M = max(tw_latest) + service_time + max_tt + 1

    model = gp.Model("vrptw")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(N):
        for j in range(N):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    t = {}
    for i in range(N):
        t[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"t_{i}")

    t_ret = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="t_ret")

    model.update()

    model.setObjective(
        gp.quicksum(travel_time[i][j] * x[i, j]
                    for i in range(N) for j in range(N) if i != j),
        GRB.MINIMIZE
    )

    # Leave depot once, return to depot once
    model.addConstr(gp.quicksum(x[0, j] for j in stores) == 1, "leave_depot")
    model.addConstr(gp.quicksum(x[i, 0] for i in stores) == 1, "return_depot")

    # Each store entered and left exactly once
    for j in stores:
        model.addConstr(gp.quicksum(x[i, j] for i in range(N) if i != j) == 1, f"enter_{j}")
    for i in stores:
        model.addConstr(gp.quicksum(x[i, j] for j in range(N) if i != j) == 1, f"leave_{i}")

    # Time windows for depot departure and all stores
    for i in range(N):
        model.addConstr(t[i] >= tw_earliest[i], f"tw_e_{i}")
        model.addConstr(t[i] <= tw_latest[i], f"tw_l_{i}")

    # Return time constraints
    model.addConstr(t_ret >= tw_earliest[0], "ret_e")
    model.addConstr(t_ret <= tw_latest[0], "ret_l")
    model.addConstr(t_ret <= max_shelf_life_window, "shelf_life")

    # Time propagation to stores (also eliminates subtours via increasing time)
    for i in range(N):
        for j in stores:
            if i != j:
                model.addConstr(
                    t[j] >= t[i] + service_time + travel_time[i][j] - M * (1 - x[i, j]),
                    f"tp_{i}_{j}"
                )

    # Time propagation back to depot
    for i in stores:
        model.addConstr(
            t_ret >= t[i] + service_time + travel_time[i][0] - M * (1 - x[i, 0]),
            f"tpr_{i}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}