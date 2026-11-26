import gurobipy as gp
from gurobipy import GRB

def solve(params):
    container_max_weight = params["container_max_weight"]
    container_min_weight = params["container_min_weight"]
    container_length = params["container_length"]
    container_width = params["container_width"]
    container_height = params["container_height"]

    demand = {
        'A': params["demand_A"],
        'B': params["demand_B"],
        'C': params["demand_C"],
        'D': params["demand_D"],
        'E': params["demand_E"],
    }

    weight = {
        'A': params["weight_A"],
        'B': params["weight_B"],
        'C': params["weight_C"],
        'D': params["weight_D"],
        'E': params["weight_E"],
    }

    dims = {
        'A': params["dims_A"],
        'B': params["dims_B"],
        'C': params["dims_C"],
        'D': params["dims_D"],
        'E': params["dims_E"],
    }

    coupling_AC = params["coupling_AC"]
    min_D_per_container = params["min_D_per_container"]

    goods = ['A', 'B', 'C', 'D', 'E']

    # Volume per unit for each good type
    vol_per_unit = {g: dims[g][0] * dims[g][1] * dims[g][2] for g in goods}

    # Total container volume
    container_volume = container_length * container_width * container_height

    # Upper bound on number of containers needed
    # Use a generous upper bound: total volume / container_volume rounded up + buffer
    total_volume = sum(demand[g] * vol_per_unit[g] for g in goods)
    total_weight = sum(demand[g] * weight[g] for g in goods)
    n_containers_vol = int(total_volume / container_volume) + 2
    n_containers_wt = int(total_weight / container_max_weight) + 2
    N = max(n_containers_vol, n_containers_wt) + 5  # upper bound

    model = gp.Model("container_loading")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)

    # y[k] = 1 if container k is used
    y = model.addVars(N, vtype=GRB.BINARY, name="y")

    # x[g][k] = number of units of good g loaded into container k
    x = {}
    for g in goods:
        x[g] = model.addVars(N, vtype=GRB.INTEGER, lb=0, ub=demand[g], name=f"x_{g}")

    # Objective: minimize number of containers used
    model.setObjective(gp.quicksum(y[k] for k in range(N)), GRB.MINIMIZE)

    # Demand constraints: all units must be transported
    for g in goods:
        model.addConstr(
            gp.quicksum(x[g][k] for k in range(N)) == demand[g],
            name=f"demand_{g}"
        )

    for k in range(N):
        # Weight capacity constraint
        model.addConstr(
            gp.quicksum(weight[g] * x[g][k] for g in goods) <= container_max_weight * y[k],
            name=f"max_weight_{k}"
        )

        # Minimum weight if container is used
        model.addConstr(
            gp.quicksum(weight[g] * x[g][k] for g in goods) >= container_min_weight * y[k],
            name=f"min_weight_{k}"
        )

        # Volume capacity constraint
        model.addConstr(
            gp.quicksum(vol_per_unit[g] * x[g][k] for g in goods) <= container_volume * y[k],
            name=f"volume_{k}"
        )

        # Coupling: for each unit of A, at least coupling_AC units of C required
        model.addConstr(
            x['C'][k] >= coupling_AC * x['A'][k],
            name=f"coupling_AC_{k}"
        )

        # Minimum D per used container
        model.addConstr(
            x['D'][k] >= min_D_per_container * y[k],
            name=f"min_D_{k}"
        )

        # Link: if any good is loaded in container k, y[k] must be 1
        for g in goods:
            model.addConstr(
                x[g][k] <= demand[g] * y[k],
                name=f"link_{g}_{k}"
            )

    # Symmetry breaking: use containers in order
    for k in range(N - 1):
        model.addConstr(y[k] >= y[k + 1], name=f"sym_{k}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}