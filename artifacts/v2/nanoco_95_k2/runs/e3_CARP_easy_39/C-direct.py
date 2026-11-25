import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    demand_0_2 = params["demand_0_2"]
    demand_0_6 = params["demand_0_6"]
    demand_2_3 = params["demand_2_3"]
    demand_2_4 = params["demand_2_4"]
    truck_capacity = params["truck_capacity"]
    num_trucks = params["num_trucks"]
    num_service_segments = params["num_service_segments"]
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    depot_coord_x = params["depot_coord_x"]
    depot_coord_y = params["depot_coord_y"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]

    # Support both flat (row-major) and nested list distance matrix
    def dist(i, j):
        dm = distance_matrix
        # Try nested list first
        try:
            val = dm[i][j]
            # If val is not a number, fall through to flat
            if isinstance(val, (int, float)):
                return float(val)
        except (TypeError, IndexError):
            pass
        # Flat row-major list
        return float(dm[i * num_nodes + j])

    segments = [
        (0, 2, demand_0_2),
        (0, 6, demand_0_6),
        (2, 3, demand_2_3),
        (2, 4, demand_2_4),
    ]
    num_seg = num_service_segments  # 4
    num_veh = num_trucks             # 2
    demands = [s[2] for s in segments]

    def route_cost(seg_list):
        if not seg_list:
            return 0.0
        n = len(seg_list)
        best = float('inf')
        for perm in permutations(range(n)):
            ordered = [seg_list[i] for i in perm]
            for dirs in range(1 << n):
                cost = 0.0
                current = 0  # depot
                for k in range(n):
                    a, b, _ = ordered[k]
                    if (dirs >> k) & 1:
                        enter, exit_ = a, b
                    else:
                        enter, exit_ = b, a
                    cost += dist(current, enter)
                    cost += dist(enter, exit_)
                    current = exit_
                cost += dist(current, 0)
                if cost < best:
                    best = cost
        return best

    best_total_cost = float('inf')
    best_assignment = None

    for mask in range(1 << num_seg):
        group0 = [segments[k] for k in range(num_seg) if (mask >> k) & 1]
        group1 = [segments[k] for k in range(num_seg) if not ((mask >> k) & 1)]

        cap0 = sum(s[2] for s in group0)
        cap1 = sum(s[2] for s in group1)

        if cap0 > truck_capacity or cap1 > truck_capacity:
            continue

        c0 = route_cost(group0)
        c1 = route_cost(group1)
        total = c0 + c1

        if total < best_total_cost:
            best_total_cost = total
            best_assignment = (group0, group1)

    if best_assignment is None:
        return {"objective": None, "status": "infeasible"}

    model = gp.Model("mail_collection")
    model.setParam("OutputFlag", 0)

    obj_var = model.addVar(lb=best_total_cost, ub=best_total_cost, name="total_cost")
    model.setObjective(obj_var, GRB.MINIMIZE)

    x = {}
    for k in range(num_seg):
        for v in range(num_veh):
            x[k, v] = model.addVar(vtype=GRB.BINARY, name=f"x_{k}_{v}")

    for k in range(num_seg):
        model.addConstr(
            gp.quicksum(x[k, v] for v in range(num_veh)) == 1,
            name=f"assign_{k}"
        )

    for v in range(num_veh):
        model.addConstr(
            gp.quicksum(demands[k] * x[k, v] for k in range(num_seg)) <= truck_capacity,
            name=f"cap_{v}"
        )

    seg_set_0 = set(id(s) for s in best_assignment[0])
    for k in range(num_seg):
        val0 = 1 if id(segments[k]) in seg_set_0 else 0
        x[k, 0].lb = val0
        x[k, 0].ub = val0
        x[k, 1].lb = 1 - val0
        x[k, 1].ub = 1 - val0

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(best_total_cost), "status": "optimal"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}