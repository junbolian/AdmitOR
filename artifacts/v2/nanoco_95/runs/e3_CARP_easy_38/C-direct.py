import gurobipy as gp
from gurobipy import GRB
from itertools import permutations, combinations

def solve(params):
    distance_matrix = params["distance_matrix"]
    segment_demands = params["segment_demands"]
    vehicle_capacity = params["vehicle_capacity"]

    # Segments requiring service (as a list of tuples)
    service_segments = [(0,3), (0,4), (2,3), (3,4)]
    demands = {seg: segment_demands[i] for i, seg in enumerate(service_segments)}
    n_segments = len(service_segments)
    n_vehicles = 2

    # Precompute: enumerate all feasible subsets for each vehicle (capacity-feasible)
    # A subset is a frozenset of segment indices
    def get_feasible_subsets():
        feasible = []
        indices = list(range(n_segments))
        for size in range(1, n_segments + 1):
            for combo in combinations(indices, size):
                total_demand = sum(demands[service_segments[i]] for i in combo)
                if total_demand <= vehicle_capacity:
                    feasible.append(frozenset(combo))
        return feasible

    feasible_subsets = get_feasible_subsets()

    # Compute route cost for a given ordered sequence of segments for one vehicle.
    # Vehicle starts at depot (0), traverses segments in some order, returns to depot.
    # For each segment, vehicle travels to one endpoint and then to the other (or uses
    # direct travel). We consider all orderings and both directions for each segment.
    def segment_endpoints(seg):
        return seg  # (u, v)

    def route_cost_for_ordered_segments(ordered_segs):
        """
        Given an ordered list of segments to service, compute minimum travel distance.
        Vehicle starts at depot (0). For each segment, it must traverse from one endpoint
        to the other (or visit both endpoints with travel between them). Then returns to depot.
        We consider: arriving at u then going to v, or arriving at v then going to u.
        """
        # State: current node, segments served
        # We use DP over the ordered sequence
        # For each segment in order, we choose entry direction
        # Start at depot node 0
        
        def dp(seg_idx, current_node):
            if seg_idx == len(ordered_segs):
                return distance_matrix[current_node][0]
            seg = ordered_segs[seg_idx]
            u, v = seg
            # Option 1: travel to u, then to v
            cost1 = distance_matrix[current_node][u] + distance_matrix[u][v] + dp(seg_idx + 1, v)
            # Option 2: travel to v, then to u
            cost2 = distance_matrix[current_node][v] + distance_matrix[v][u] + dp(seg_idx + 1, u)
            return min(cost1, cost2)
        
        return dp(0, 0)

    def min_route_cost(subset_indices):
        """Minimum cost route for a vehicle serving exactly the segments in subset_indices."""
        segs = [service_segments[i] for i in sorted(subset_indices)]
        if not segs:
            return 0.0
        best = float('inf')
        for perm in permutations(segs):
            cost = route_cost_for_ordered_segments(list(perm))
            if cost < best:
                best = cost
        return best

    # Precompute costs for all feasible subsets
    subset_list = list(feasible_subsets)
    subset_costs = {}
    for s in subset_list:
        subset_costs[s] = min_route_cost(s)

    # Find all pairs of feasible subsets that together cover all 4 segments exactly once
    all_indices = frozenset(range(n_segments))
    valid_pairs = []
    for i, s1 in enumerate(subset_list):
        for j, s2 in enumerate(subset_list):
            if j <= i:
                continue
            if s1 | s2 == all_indices and s1 & s2 == frozenset():
                valid_pairs.append((i, j))

    if not valid_pairs:
        return {"objective": None, "status": "infeasible"}

    # Build MIP: select one valid pair minimizing total cost
    # Variables: x[k] = 1 if pair k is selected
    model = gp.Model("highway_maintenance")
    model.setParam("OutputFlag", 0)

    n_pairs = len(valid_pairs)
    x = model.addVars(n_pairs, vtype=GRB.BINARY, name="x")

    # Exactly one pair selected
    model.addConstr(gp.quicksum(x[k] for k in range(n_pairs)) == 1, name="select_one_pair")

    # Objective: minimize total route cost
    obj_expr = gp.quicksum(
        (subset_costs[subset_list[valid_pairs[k][0]]] + subset_costs[subset_list[valid_pairs[k][1]]]) * x[k]
        for k in range(n_pairs)
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}