import gurobipy as gp
from gurobipy import GRB
from itertools import combinations, permutations

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

    # Normalize distance_matrix: accept flat list or nested list
    if isinstance(distance_matrix[0], (list, tuple)):
        dist_mat = distance_matrix
    else:
        dist_mat = [distance_matrix[i * num_nodes:(i + 1) * num_nodes] for i in range(num_nodes)]

    def dist(i, j):
        return dist_mat[i][j]

    segments = [
        (0, 2, demand_0_2),
        (0, 6, demand_0_6),
        (2, 3, demand_2_3),
        (2, 4, demand_2_4),
    ]
    num_seg = num_service_segments
    num_k = num_trucks
    depot = 0

    def min_route_cost(seg_indices):
        if not seg_indices:
            return 0.0
        segs = [segments[i] for i in seg_indices]
        n = len(segs)
        best = float('inf')
        for perm in permutations(range(n)):
            for dirs in range(1 << n):
                cost = 0.0
                current = depot
                for step in range(n):
                    idx = perm[step]
                    u, v, _ = segs[idx]
                    if (dirs >> step) & 1:
                        start_node, end_node = v, u
                    else:
                        start_node, end_node = u, v
                    cost += dist(current, start_node)
                    cost += dist(start_node, end_node)
                    current = end_node
                cost += dist(current, depot)
                if cost < best:
                    best = cost
        return best

    seg_indices = list(range(num_seg))

    all_subsets = []
    for r in range(num_seg + 1):
        for combo in combinations(seg_indices, r):
            subset0 = list(combo)
            subset1 = [s for s in seg_indices if s not in subset0]
            demand0 = sum(segments[i][2] for i in subset0)
            demand1 = sum(segments[i][2] for i in subset1)
            if demand0 <= truck_capacity and demand1 <= truck_capacity:
                all_subsets.append((subset0, subset1))

    if not all_subsets:
        return {"objective": None, "status": "infeasible"}

    unique_subsets = {}
    for s0, s1 in all_subsets:
        k0 = tuple(sorted(s0))
        k1 = tuple(sorted(s1))
        if k0 not in unique_subsets:
            unique_subsets[k0] = min_route_cost(list(k0))
        if k1 not in unique_subsets:
            unique_subsets[k1] = min_route_cost(list(k1))

    model = gp.Model("CARP")
    model.setParam("OutputFlag", 0)

    num_partitions = len(all_subsets)
    x = model.addVars(num_partitions, vtype=GRB.BINARY, name="x")

    model.addConstr(gp.quicksum(x[p] for p in range(num_partitions)) == 1, "one_partition")

    obj_coeffs = {}
    for p, (s0, s1) in enumerate(all_subsets):
        k0 = tuple(sorted(s0))
        k1 = tuple(sorted(s1))
        obj_coeffs[p] = unique_subsets[k0] + unique_subsets[k1]

    model.setObjective(
        gp.quicksum(obj_coeffs[p] * x[p] for p in range(num_partitions)),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}