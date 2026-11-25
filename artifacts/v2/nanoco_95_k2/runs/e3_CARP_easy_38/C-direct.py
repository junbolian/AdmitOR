import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    vehicle_capacity = params["vehicle_capacity"]
    demands = params["demands"]
    num_vehicles = params["num_vehicles"]
    num_service_segments = params["num_service_segments"]
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    # Service segments (indexed 0..num_service_segments-1)
    # Each segment has two endpoints and a demand
    # From the problem: segments are (0,3), (0,4), (2,3), (3,4)
    service_segments = [(0,3), (0,4), (2,3), (3,4)]
    S = list(range(num_service_segments))  # 0,1,2,3
    V = list(range(num_vehicles))           # 0,1
    depot = 0

    # Enumerate all feasible subsets of segments for each vehicle
    # A subset is feasible if total demand <= vehicle_capacity
    def get_feasible_subsets():
        feasible = []
        for r in range(1, num_service_segments + 1):
            for combo in itertools.combinations(S, r):
                total_demand = sum(demands[i] for i in combo)
                if total_demand <= vehicle_capacity:
                    feasible.append(frozenset(combo))
        return feasible

    feasible_subsets = get_feasible_subsets()

    # For a given subset of service segments, compute the minimum travel distance
    # for a vehicle starting and ending at depot, visiting all segments.
    # Each segment can be traversed in either direction.
    # We use TSP-like enumeration over the nodes implied by the segments.

    def route_cost(subset):
        """
        Given a subset (frozenset of segment indices), compute minimum cost tour
        from depot, servicing each segment exactly once, returning to depot.
        Each segment (u,v) must be traversed in one direction: u->v or v->u.
        We enumerate all orderings of segments and directions.
        """
        seg_list = list(subset)
        n_seg = len(seg_list)
        
        # For each segment, it contributes an arc (either direction)
        # The route visits segments in some order; between consecutive segments
        # we travel (deadhead) from the endpoint of one to the start of the next.
        # Cost = deadhead(depot -> start_seg1) + dist(seg1) + deadhead(end_seg1 -> start_seg2)
        #        + dist(seg2) + ... + deadhead(end_last -> depot)

        def seg_endpoints(seg_idx, direction):
            u, v = service_segments[seg_idx]
            if direction == 0:
                return u, v
            else:
                return v, u

        seg_dist = {}
        for seg_idx in seg_list:
            u, v = service_segments[seg_idx]
            seg_dist[(seg_idx, 0)] = distance_matrix[u][v]
            seg_dist[(seg_idx, 1)] = distance_matrix[v][u]

        best = float('inf')

        # Enumerate all permutations of segments
        for perm in itertools.permutations(seg_list):
            # Enumerate all direction assignments
            for dirs in itertools.product([0, 1], repeat=n_seg):
                cost = 0.0
                # Travel from depot to start of first segment
                start0, end0 = seg_endpoints(perm[0], dirs[0])
                cost += distance_matrix[depot][start0]
                cost += seg_dist[(perm[0], dirs[0])]
                prev_end = end0

                for k in range(1, n_seg):
                    start_k, end_k = seg_endpoints(perm[k], dirs[k])
                    cost += distance_matrix[prev_end][start_k]
                    cost += seg_dist[(perm[k], dirs[k])]
                    prev_end = end_k

                # Return to depot
                cost += distance_matrix[prev_end][depot]

                if cost < best:
                    best = cost

        return best

    # Precompute costs for all feasible subsets
    subset_cost = {}
    for fs in feasible_subsets:
        subset_cost[fs] = route_cost(fs)

    # Build assignment MIP:
    # Binary variable x[v, fs] = 1 if vehicle v uses subset fs
    # Each segment must be covered exactly once across all vehicles
    # Each vehicle uses exactly one subset (or possibly zero segments,
    # but we need all segments covered)

    # We need: for each segment s, sum over v,fs: x[v,fs] * (s in fs) == 1
    # Each vehicle assigned exactly one subset: sum over fs: x[v,fs] == 1
    # Minimize sum of x[v,fs] * cost[fs]

    # Actually vehicle can be idle (assigned empty route with cost 0),
    # but all segments must be covered. Let's allow "empty" assignment.
    # Add empty subset with cost 0.
    empty = frozenset()
    subset_cost[empty] = 0.0
    all_subsets = feasible_subsets + [empty]
    # Deduplicate
    all_subsets = list(set(all_subsets))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[v][i] = 1 if vehicle v is assigned subset all_subsets[i]
    x = {}
    for v in V:
        for i, fs in enumerate(all_subsets):
            x[v, i] = model.addVar(vtype=GRB.BINARY, name=f"x_{v}_{i}")

    # Each vehicle assigned exactly one subset
    for v in V:
        model.addConstr(
            gp.quicksum(x[v, i] for i in range(len(all_subsets))) == 1
        )

    # Each segment covered exactly once
    for s in S:
        model.addConstr(
            gp.quicksum(
                x[v, i]
                for v in V
                for i, fs in enumerate(all_subsets)
                if s in fs
            ) == 1
        )

    # Objective: minimize total travel distance
    obj = gp.quicksum(
        x[v, i] * subset_cost[fs]
        for v in V
        for i, fs in enumerate(all_subsets)
        for _ in [None]  # just to unpack fs
        if True
    )
    # Rebuild objective cleanly
    obj_expr = gp.LinExpr()
    for v in V:
        for i, fs in enumerate(all_subsets):
            obj_expr += x[v, i] * subset_cost[fs]

    model.setObjective(obj_expr, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}