import gurobipy as gp
from gurobipy import GRB


def solve(params):
    model = gp.Model("airline_optimization")
    model.Params.OutputFlag = 0

    # --- Read all numeric parameters from the dict ---
    cost_P0_L0_to_L1 = params["cost_P0_L0_to_L1"]
    cost_P0_L1_to_L0 = params["cost_P0_L1_to_L0"]
    cost_P1_L0_to_L1 = params["cost_P1_L0_to_L1"]
    cost_P1_L1_to_L0 = params["cost_P1_L1_to_L0"]
    cost_idle = params["cost_idle"]
    max_planes_P0 = params["max_planes_P0"]
    max_planes_P1 = params["max_planes_P1"]
    demand_L0_to_L1_period1 = params["demand_L0_to_L1_period1"]
    capacity_P0 = params["capacity_P0"]
    capacity_P1 = params["capacity_P1"]
    max_route_P0_L0_to_L1 = params["max_route_P0_L0_to_L1"]
    max_route_P1_L0_to_L1 = params["max_route_P1_L0_to_L1"]
    max_route_P0_L1_to_L0 = params["max_route_P0_L1_to_L0"]
    max_route_P1_L1_to_L0 = params["max_route_P1_L1_to_L0"]

    planes = [0, 1]
    locations = [0, 1]
    periods = [1]  # single period – demand and route data are for period 1 only

    # --- Decision variables ---
    # Route variables: number of planes of type p flying from loc i to loc j in period t
    x = {}
    for p in planes:
        for i in locations:
            for j in locations:
                for t in periods:
                    if i == j:
                        continue
                    x[p, i, j, t] = model.addVar(
                        vtype=GRB.INTEGER, lb=0,
                        name=f"x_P{p}_L{i}_to_L{j}_t{t}"
                    )

    # Idle variables: number of idle planes of type p at location i in period t
    idle = {}
    for p in planes:
        for i in locations:
            for t in periods:
                idle[p, i, t] = model.addVar(
                    vtype=GRB.INTEGER, lb=0,
                    name=f"idle_P{p}_L{i}_t{t}"
                )

    model.update()

    # --- Objective: minimise total operational cost ---
    obj = gp.LinExpr()
    cost_map = {
        (0, 0, 1): cost_P0_L0_to_L1,
        (0, 1, 0): cost_P0_L1_to_L0,
        (1, 0, 1): cost_P1_L0_to_L1,
        (1, 1, 0): cost_P1_L1_to_L0,
    }
    for p in planes:
        for i in locations:
            for j in locations:
                if i == j:
                    continue
                for t in periods:
                    obj += cost_map[(p, i, j)] * x[p, i, j, t]

    for p in planes:
        for i in locations:
            for t in periods:
                obj += cost_idle * idle[p, i, t]

    model.setObjective(obj, GRB.MINIMIZE)

    # --- Demand constraint (period 1, L0 -> L1) ---
    model.addConstr(
        capacity_P0 * x[0, 0, 1, 1] + capacity_P1 * x[1, 0, 1, 1]
        >= demand_L0_to_L1_period1,
        name="demand_L0_to_L1_t1"
    )

    # --- Fleet availability: total planes of each type across both locations ---
    for p in planes:
        max_p = max_planes_P0 if p == 0 else max_planes_P1
        model.addConstr(
            gp.quicksum(
                idle[p, i, t] + x[p, i, j, t]
                for i in locations
                for j in locations if i != j
                for t in periods
            ) <= max_p,
            name=f"fleet_P{p}"
        )

    # --- Route restrictions ---
    route_max = {
        (0, 0, 1): max_route_P0_L0_to_L1,
        (1, 0, 1): max_route_P1_L0_to_L1,
        (0, 1, 0): max_route_P0_L1_to_L0,
        (1, 1, 0): max_route_P1_L1_to_L0,
    }
    for p in planes:
        for i in locations:
            for j in locations:
                if i == j:
                    continue
                for t in periods:
                    model.addConstr(
                        x[p, i, j, t] <= route_max[(p, i, j)],
                        name=f"max_route_P{p}_L{i}_to_L{j}_t{t}"
                    )

    # --- Solve ---
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}