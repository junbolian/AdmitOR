import gurobipy as gp
from gurobipy import GRB
from itertools import combinations, permutations

def solve(params):
    vehicle_capacity = params["vehicle_capacity"]
    demands = params["demands"]
    num_vehicles = params["num_vehicles"]
    num_service_segments = params["num_service_segments"]
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    # Service segments (indexed 0..num_service_segments-1)
    # Each segment is an unordered pair of nodes; directionality unrestricted
    service_segments = [(0, 3), (0, 4), (2, 3), (3, 4)]
    seg_demand = demands  # list of demands indexed by segment

    depot = 0
    nodes = list(range(num_nodes))
    vehicles = list(range(num_vehicles))
    segs = list(range(num_service_segments))

    def dist(i, j):
        return distance_matrix[i][j]

    # We enumerate all feasible subsets of segments for a single vehicle
    # (subsets where total demand <= vehicle_capacity)
    # Then for each feasible subset, compute the minimum travel cost route
    # starting and ending at the depot, covering all segments in the subset.

    # For a given ordered sequence of segments, the vehicle traverses each segment
    # (in either direction) and travels between consecutive segments optimally.
    # We need to find the minimum cost tour for a given subset.

    def route_cost_for_subset(subset):
        """
        Given a subset (list of segment indices), find minimum cost route
        starting at depot, servicing each segment exactly once (in some order,
        some direction), returning to depot.
        Uses brute-force over permutations since subsets are small (<=4 segments).
        """
        if not subset:
            return 0.0

        min_cost = float('inf')
        # Try all orderings of segments
        for perm in permutations(subset):
            # For each ordering, try both directions for each segment
            # Direction: 0 means (u, v), 1 means (v, u)
            n = len(perm)
            for dirs in range(1 << n):
                cost = 0.0
                current_node = depot
                for k, seg_idx in enumerate(perm):
                    u, v = service_segments[seg_idx]
                    direction = (dirs >> k) & 1
                    if direction == 0:
                        entry, exit_node = u, v
                    else:
                        entry, exit_node = v, u
                    # Travel from current_node to entry, then traverse segment
                    cost += dist(current_node, entry)
                    cost += dist(entry, exit_node)
                    current_node = exit_node
                # Return to depot
                cost += dist(current_node, depot)
                if cost < min_cost:
                    min_cost = cost
        return min_cost

    # Enumerate all feasible subsets
    feasible_subsets = []
    for r in range(0, num_service_segments + 1):
        for combo in combinations(segs, r):
            total_demand = sum(seg_demand[s] for s in combo)
            if total_demand <= vehicle_capacity:
                feasible_subsets.append(list(combo))

    # Precompute costs
    subset_costs = {}
    for fs in feasible_subsets:
        key = tuple(sorted(fs))
        if key not in subset_costs:
            subset_costs[key] = route_cost_for_subset(fs)

    # We need to partition all num_service_segments segments among num_vehicles
    # such that each vehicle's subset is feasible, and total cost is minimized.
    # Enumerate all ways to partition segs into num_vehicles groups.

    # For 2 vehicles and 4 segments, enumerate all partitions.
    # A partition assigns each segment to exactly one vehicle.
    # Number of ways = num_vehicles^num_service_segments but we deduplicate.

    def enumerate_partitions(seg_list, num_v):
        """Yield all assignments: list of lists, one per vehicle."""
        if not seg_list:
            yield [[] for _ in range(num_v)]
            return
        s = seg_list[0]
        rest = seg_list[1:]
        for sub_partition in enumerate_partitions(rest, num_v):
            for v in range(num_v):
                new_partition = [list(sp) for sp in sub_partition]
                new_partition[v] = new_partition[v] + [s]
                yield new_partition

    best_cost = float('inf')
    best_partition = None

    for partition in enumerate_partitions(segs, num_vehicles):
        feasible = True
        total_cost = 0.0
        for v in range(num_vehicles):
            vsegs = partition[v]
            total_demand = sum(seg_demand[s] for s in vsegs)
            if total_demand > vehicle_capacity:
                feasible = False
                break
            key = tuple(sorted(vsegs))
            c = subset_costs.get(key)
            if c is None:
                c = route_cost_for_subset(vsegs)
                subset_costs[key] = c
            total_cost += c
        if feasible and total_cost < best_cost:
            best_cost = total_cost
            best_partition = partition

    if best_partition is None:
        return {"objective": None, "status": "infeasible"}

    # Now formulate as a MIP to get a clean optimal solution with Gurobi.
    # Variables: x[s, v] = 1 if segment s is assigned to vehicle v.
    # Then use the precomputed route costs via a set-covering formulation.

    # Since subsets are small, use a set-partitioning MIP with
    # binary variables y[fs_key, v] = 1 if vehicle v uses subset fs.

    # Build list of unique feasible subsets with their costs
    unique_subsets = list(subset_costs.keys())  # tuples of sorted seg indices
    us_index = {fs: i for i, fs in enumerate(unique_subsets)}
    us_cost = [subset_costs[fs] for fs in unique_subsets]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[i, v] = 1 if vehicle v uses subset unique_subsets[i]
    y = {}
    for i, fs in enumerate(unique_subsets):
        total_demand = sum(seg_demand[s] for s in fs)
        if total_demand <= vehicle_capacity:
            for v in vehicles:
                y[i, v] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{v}")

    # Each vehicle uses exactly one subset
    for v in vehicles:
        model.addConstr(
            gp.quicksum(y[i, v] for i in range(len(unique_subsets)) if (i, v) in y) == 1,
            name=f"one_subset_per_vehicle_{v}"
        )

    # Each segment covered exactly once across all vehicles
    for s in segs:
        model.addConstr(
            gp.quicksum(
                y[i, v]
                for i, fs in enumerate(unique_subsets)
                for v in vehicles
                if s in fs and (i, v) in y
            ) == 1,
            name=f"seg_covered_{s}"
        )

    # Objective: minimize total route cost
    model.setObjective(
        gp.quicksum(
            us_cost[i] * y[i, v]
            for i in range(len(unique_subsets))
            for v in vehicles
            if (i, v) in y
        ),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}